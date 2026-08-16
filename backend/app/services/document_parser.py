from __future__ import annotations

import mimetypes
from pathlib import Path

import structlog

logger = structlog.get_logger()


class DocumentParser:
    """Extract text content from various document formats."""

    SUPPORTED_TYPES = {
        "application/pdf": "_parse_pdf",
        "text/plain": "_parse_text",
        "text/markdown": "_parse_text",
        "text/html": "_parse_html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "_parse_docx",
    }

    async def parse(self, content: bytes, filename: str, mime_type: str | None = None) -> str:
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)

        if not mime_type:
            ext = Path(filename).suffix.lower()
            mime_map = {
                ".pdf": "application/pdf",
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".html": "text/html",
                ".htm": "text/html",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
            mime_type = mime_map.get(ext, "text/plain")

        parser_method = self.SUPPORTED_TYPES.get(mime_type, "_parse_text")
        parser = getattr(self, parser_method)

        text = await parser(content, filename)
        text = self._clean_text(text)

        await logger.ainfo(
            "Parsed document",
            filename=filename,
            mime_type=mime_type,
            chars=len(text),
        )
        return text

    async def _parse_pdf(self, content: bytes, filename: str) -> str:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    async def _parse_text(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8", errors="replace")

    async def _parse_html(self, content: bytes, filename: str) -> str:
        from bs4 import BeautifulSoup
        from markdownify import markdownify

        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        html = str(soup)
        return markdownify(html, strip=["img", "a"])

    async def _parse_docx(self, content: bytes, filename: str) -> str:
        import io
        from docx import Document

        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _clean_text(self, text: str) -> str:
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()
