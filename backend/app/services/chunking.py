from abc import ABC, abstractmethod
from dataclasses import dataclass

import tiktoken
import xxhash


@dataclass
class ChunkResult:
    content: str
    index: int
    content_hash: str
    token_count: int
    metadata: dict


class ChunkingStrategy(ABC):
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self._encoder.encode(text))

    @staticmethod
    def compute_hash(text: str) -> str:
        return xxhash.xxh64(text.encode()).hexdigest()

    @abstractmethod
    def chunk(self, text: str, metadata: dict | None = None) -> list[ChunkResult]: ...

    def _build_results(self, chunks: list[str], metadata: dict | None = None) -> list[ChunkResult]:
        results = []
        for i, content in enumerate(chunks):
            content = content.strip()
            if not content:
                continue
            results.append(
                ChunkResult(
                    content=content,
                    index=i,
                    content_hash=self.compute_hash(content),
                    token_count=self.count_tokens(content),
                    metadata=metadata or {},
                )
            )
        return results


class FixedSizeChunker(ChunkingStrategy):
    """Split text into fixed character-length chunks with overlap."""

    def chunk(self, text: str, metadata: dict | None = None) -> list[ChunkResult]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        return self._build_results(chunks, metadata)


class RecursiveChunker(ChunkingStrategy):
    """Recursively split on separators, preferring natural boundaries."""

    SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def chunk(self, text: str, metadata: dict | None = None) -> list[ChunkResult]:
        chunks = self._recursive_split(text, self.SEPARATORS)
        enriched = self._add_overlap_context(chunks)
        return self._build_results(enriched, metadata)

    def _add_overlap_context(self, chunks: list[str]) -> list[str]:
        """Add overlap from neighboring chunks for better retrieval context."""
        if not chunks or self.chunk_overlap <= 0:
            return chunks

        result = []
        for i, chunk in enumerate(chunks):
            prefix = ""
            suffix = ""
            if i > 0:
                prefix = chunks[i - 1][-self.chunk_overlap:]
            if i < len(chunks) - 1:
                suffix = chunks[i + 1][:self.chunk_overlap]

            enriched = f"{prefix} {chunk} {suffix}".strip() if (prefix or suffix) else chunk
            result.append(enriched)
        return result

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else [""]

        if sep == "":
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

        parts = text.split(sep)
        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(part) > self.chunk_size:
                    chunks.extend(self._recursive_split(part, remaining_seps))
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        return chunks


class SentenceChunker(ChunkingStrategy):
    """Split on sentence boundaries, grouping into chunks up to chunk_size."""

    def chunk(self, text: str, metadata: dict | None = None) -> list[ChunkResult]:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence

        if current:
            chunks.append(current)

        return self._build_results(chunks, metadata)


STRATEGY_MAP = {
    "fixed": FixedSizeChunker,
    "recursive": RecursiveChunker,
    "sentence": SentenceChunker,
}


def get_chunker(
    strategy: str = "recursive",
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> ChunkingStrategy:
    cls = STRATEGY_MAP.get(strategy)
    if not cls:
        raise ValueError(f"Unknown chunking strategy: {strategy}. Options: {list(STRATEGY_MAP)}")
    return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
