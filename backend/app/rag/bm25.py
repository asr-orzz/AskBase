from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class BM25Result:
    chunk_id: str
    content: str
    score: float
    metadata: dict


class BM25Index:
    """In-memory BM25 index for keyword-based retrieval.

    Built from chunk data loaded from Postgres. Rebuilt per-query or cached per KB.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: list[dict] = []
        self._doc_freqs: Counter[str] = Counter()
        self._doc_lengths: list[int] = []
        self._avg_dl: float = 0.0
        self._tokenized: list[list[str]] = []

    @staticmethod
    def tokenize(text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]

    def build(self, documents: list[dict]) -> None:
        """Build index from list of dicts with 'chunk_id', 'content', 'metadata'."""
        self._documents = documents
        self._tokenized = []
        self._doc_freqs = Counter()
        self._doc_lengths = []

        for doc in documents:
            tokens = self.tokenize(doc["content"])
            self._tokenized.append(tokens)
            self._doc_lengths.append(len(tokens))

            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freqs[token] += 1

        total_length = sum(self._doc_lengths)
        self._avg_dl = total_length / len(documents) if documents else 1.0

    def search(self, query: str, top_k: int = 10) -> list[BM25Result]:
        if not self._documents:
            return []

        query_tokens = self.tokenize(query)
        scores: list[float] = []
        n = len(self._documents)

        for i, doc_tokens in enumerate(self._tokenized):
            score = 0.0
            dl = self._doc_lengths[i]
            tf_map = Counter(doc_tokens)

            for qt in query_tokens:
                if qt not in tf_map:
                    continue

                tf = tf_map[qt]
                df = self._doc_freqs.get(qt, 0)

                idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl)
                score += idf * numerator / denominator

            scores.append(score)

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results: list[BM25Result] = []

        for idx, score in ranked[:top_k]:
            if score <= 0:
                break
            doc = self._documents[idx]
            results.append(
                BM25Result(
                    chunk_id=doc["chunk_id"],
                    content=doc["content"],
                    score=score,
                    metadata=doc.get("metadata", {}),
                )
            )

        return results
