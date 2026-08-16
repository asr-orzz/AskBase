from __future__ import annotations

import base64
from datetime import datetime
from typing import Any

import structlog
import xxhash

from app.connectors.base import (
    BaseConnector,
    ChangeOperation,
    DiscoveredItem,
    DocumentEvent,
)

logger = structlog.get_logger()

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".toml", ".cfg",
    ".html", ".css", ".sql", ".sh", ".bash", ".dockerfile",
}


class GitHubConnector(BaseConnector):
    """Connector for GitHub repositories.

    Config:
        repo: str — "owner/repo"
        branch: str — branch name (default: main)
        path: str — subdirectory to scan (default: "")
        extensions: list[str] | None — file extensions to include

    Credentials:
        token: str — GitHub personal access token
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any] | None = None):
        super().__init__(config, credentials)
        self._github: Any = None
        self._repo: Any = None

    def _get_repo(self) -> Any:
        if self._repo is None:
            from github import Github

            token = self.credentials.get("token", "")
            self._github = Github(token) if token else Github()
            self._repo = self._github.get_repo(self.config["repo"])
        return self._repo

    @property
    def source_type(self) -> str:
        return "github"

    async def validate(self) -> bool:
        try:
            repo = self._get_repo()
            repo.get_branch(self.config.get("branch", repo.default_branch))
            return True
        except Exception:
            return False

    async def discover(self) -> list[DiscoveredItem]:
        repo = self._get_repo()
        branch = self.config.get("branch", repo.default_branch)
        prefix = self.config.get("path", "")
        extensions = set(self.config.get("extensions", CODE_EXTENSIONS))

        tree = repo.get_git_tree(branch, recursive=True)
        items: list[DiscoveredItem] = []

        for element in tree.tree:
            if element.type != "blob":
                continue

            path = element.path
            if prefix and not path.startswith(prefix):
                continue

            ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext not in extensions:
                continue

            filename = path.rsplit("/", 1)[-1] if "/" in path else path
            items.append(
                DiscoveredItem(
                    identifier=path,
                    title=filename,
                    location=f"https://github.com/{self.config['repo']}/blob/{branch}/{path}",
                    file_size=element.size,
                    metadata={
                        "sha": element.sha,
                        "path": path,
                        "branch": branch,
                        "repo": self.config["repo"],
                    },
                )
            )

        await logger.ainfo(
            "GitHub discovery complete",
            repo=self.config["repo"],
            branch=branch,
            items=len(items),
        )
        return items

    async def fetch(self, item: DiscoveredItem) -> bytes:
        repo = self._get_repo()
        sha = item.metadata.get("sha", "")
        blob = repo.get_git_blob(sha)

        if blob.encoding == "base64":
            return base64.b64decode(blob.content)
        return blob.content.encode("utf-8")

    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        repo = self._get_repo()
        branch = self.config.get("branch", repo.default_branch)

        if since:
            commits = repo.get_commits(sha=branch, since=since)
            changed_paths: set[str] = set()
            for commit in commits:
                for file in commit.files:
                    changed_paths.add(file.filename)

            all_items = await self.discover()
            items = [i for i in all_items if i.identifier in changed_paths]
        else:
            items = await self.discover()

        events: list[DocumentEvent] = []
        for item in items:
            content = await self.fetch(item)
            events.append(
                DocumentEvent(
                    document_id=item.identifier,
                    source_id=self.config.get("source_id", ""),
                    tenant_id=self.config.get("tenant_id", ""),
                    operation=ChangeOperation.UPDATED if since else ChangeOperation.CREATED,
                    title=item.title,
                    content_location=item.location,
                    content_hash=xxhash.xxh64(content).hexdigest(),
                    file_size=len(content),
                    metadata=item.metadata,
                )
            )

        return events
