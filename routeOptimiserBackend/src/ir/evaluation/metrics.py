# src/ir/evaluation/metrics.py
"""
IR evaluation metrics.

Implements:
  - Precision@K
  - Recall@K
  - F1@K
  - MRR (Mean Reciprocal Rank)
  - Retrieval latency

All metrics are computed from ACTUAL retrieval runs — no fabrication.
"""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING

from src.ir.evaluation.dataset import get_queries
from src.ir.query.parser import parse_query
from src.ir.query.expansion import expand_query

if TYPE_CHECKING:
    from src.ir.retrieval.hybrid import HybridRetriever

logger = logging.getLogger("ir.eval")


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    return len(set(top_k) & relevant) / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top_k = retrieved[:k]
    return len(set(top_k) & relevant) / len(relevant)


def f1_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    p = precision_at_k(retrieved, relevant, k)
    r = recall_at_k(retrieved, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def evaluate_retriever(
    retriever: "HybridRetriever",
    method: str = "hybrid",
    top_k: int = 5,
) -> dict:
    """
    Run the judged evaluation dataset against a retriever and compute metrics.

    Parameters
    ----------
    retriever : HybridRetriever
    method    : "bm25" | "tfidf" | "dense" | "hybrid"
    top_k     : K for P@K and Recall@K

    Returns
    -------
    dict with mean P@K, Recall@K, F1@K, MRR, mean latency_ms, per-query details.
    """
    queries = get_queries()
    results = []

    for q in queries:
        t0 = time.perf_counter()

        pq = parse_query(q["query"])
        pq.expanded_terms = expand_query(q["query"], pq.hazard, pq.cargo)

        retrieved_ids = [d for d, _ in retriever.retrieve_by_method(pq, method, top_k=top_k * 2)]
        latency_ms = (time.perf_counter() - t0) * 1000

        relevant = set(q["relevant_documents"])
        p = precision_at_k(retrieved_ids, relevant, top_k)
        r = recall_at_k(retrieved_ids, relevant, top_k)
        f = f1_at_k(retrieved_ids, relevant, top_k)
        rr = reciprocal_rank(retrieved_ids, relevant)

        results.append({
            "query_id":   q["id"],
            "query":      q["query"],
            "p_at_k":     round(p, 4),
            "recall_at_k": round(r, 4),
            "f1_at_k":    round(f, 4),
            "rr":         round(rr, 4),
            "latency_ms": round(latency_ms, 1),
            "retrieved":  retrieved_ids[:top_k],
            "relevant":   list(relevant),
        })

    n = len(results)
    summary = {
        "method":          method,
        "k":               top_k,
        "num_queries":     n,
        "mean_p_at_k":     round(sum(r["p_at_k"]      for r in results) / n, 4),
        "mean_recall_at_k": round(sum(r["recall_at_k"] for r in results) / n, 4),
        "mean_f1_at_k":    round(sum(r["f1_at_k"]     for r in results) / n, 4),
        "mrr":             round(sum(r["rr"]           for r in results) / n, 4),
        "mean_latency_ms": round(sum(r["latency_ms"]  for r in results) / n, 1),
        "per_query":       results,
    }
    return summary
