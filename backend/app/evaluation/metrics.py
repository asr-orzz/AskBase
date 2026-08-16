from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalMetrics:
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    citation_accuracy: float = 0.0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Fraction of relevant documents found in top-k retrieved."""
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    relevant = set(relevant_ids)
    return len(top_k & relevant) / len(relevant)


def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Fraction of top-k retrieved documents that are relevant."""
    if not retrieved_ids or k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant = set(relevant_ids)
    return sum(1 for doc in top_k if doc in relevant) / k


def mean_reciprocal_rank(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    """Reciprocal of the rank of the first relevant document."""
    relevant = set(relevant_ids)
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int = 5) -> float:
    """Normalized Discounted Cumulative Gain at k."""
    import math

    relevant = set(relevant_ids)
    top_k = retrieved_ids[:k]

    dcg = 0.0
    for i, doc_id in enumerate(top_k):
        rel = 1.0 if doc_id in relevant else 0.0
        dcg += rel / math.log2(i + 2)

    ideal = sorted([1.0 if doc_id in relevant else 0.0 for doc_id in top_k], reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))

    if idcg == 0:
        ideal_count = min(k, len(relevant_ids))
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_count))

    return dcg / idcg if idcg > 0 else 0.0


async def faithfulness_score(
    answer: str,
    contexts: list[str],
    llm_provider: str = "openai",
    llm_model: str | None = None,
) -> float:
    """LLM-as-judge: does the answer faithfully represent the context?"""
    from app.services.llm import LLMMessage, get_llm_provider

    if not answer or not contexts:
        return 0.0

    context_text = "\n\n---\n\n".join(contexts[:5])
    prompt = f"""Rate how faithfully the following answer represents the given context.
Score from 0.0 to 1.0 where 1.0 means completely faithful (no hallucination).

Context:
{context_text}

Answer:
{answer}

Respond with ONLY a number between 0.0 and 1.0."""

    llm = get_llm_provider(llm_provider, llm_model)
    response = await llm.generate(
        [LLMMessage(role="user", content=prompt)],
        temperature=0.0,
        max_tokens=10,
    )

    try:
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))
    except ValueError:
        return 0.0


async def answer_relevance_score(
    question: str,
    answer: str,
    llm_provider: str = "openai",
    llm_model: str | None = None,
) -> float:
    """LLM-as-judge: does the answer actually address the question?"""
    from app.services.llm import LLMMessage, get_llm_provider

    if not question or not answer:
        return 0.0

    prompt = f"""Rate how relevant the following answer is to the question.
Score from 0.0 to 1.0 where 1.0 means perfectly relevant and complete.

Question:
{question}

Answer:
{answer}

Respond with ONLY a number between 0.0 and 1.0."""

    llm = get_llm_provider(llm_provider, llm_model)
    response = await llm.generate(
        [LLMMessage(role="user", content=prompt)],
        temperature=0.0,
        max_tokens=10,
    )

    try:
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))
    except ValueError:
        return 0.0
