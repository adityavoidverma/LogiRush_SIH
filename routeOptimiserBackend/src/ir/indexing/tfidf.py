# src/ir/indexing/tfidf.py
"""
TF-IDF retrieval over the inverted index.

All steps are explicit:
  1. Tokenize query
  2. Compute TF-IDF weight for each query term in each candidate document
  3. Compute cosine similarity between query vector and document vectors
  4. Return top-K document IDs with scores

Nothing is hidden behind sklearn or a third-party IR library so the
implementation is fully inspectable.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ir.indexing.inverted_index import InvertedIndex


def idf(N: int, df: int) -> float:
    """Smoothed inverse document frequency: log((N+1)/(df+1)) + 1."""
    if df == 0:
        return 0.0
    return math.log((N + 1) / (df + 1)) + 1.0


def tfidf_weight(tf: int, N: int, df: int) -> float:
    """TF-IDF weight for a term in a document: (1+log(tf)) * idf."""
    if tf == 0:
        return 0.0
    return (1.0 + math.log(tf)) * idf(N, df)


def _cosine(vec_q: dict[str, float], vec_d: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    dot = sum(vec_q.get(t, 0.0) * vec_d.get(t, 0.0) for t in vec_q)
    norm_q = math.sqrt(sum(v * v for v in vec_q.values()))
    norm_d = math.sqrt(sum(v * v for v in vec_d.values()))
    if norm_q == 0 or norm_d == 0:
        return 0.0
    return dot / (norm_q * norm_d)


class TFIDFRetriever:
    """
    TF-IDF cosine-similarity retrieval.

    Requires an already-built InvertedIndex.
    """

    def __init__(self, index: "InvertedIndex") -> None:
        self._index = index

    def query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Retrieve top-K documents by TF-IDF cosine similarity.

        Returns
        -------
        list of (doc_id, score) sorted by score descending.
        """
        tokens = self._index.tokenize(query_text)
        if not tokens:
            return []

        N = self._index.N

        # Build query TF-IDF vector
        query_tf: dict[str, int] = {}
        for t in tokens:
            query_tf[t] = query_tf.get(t, 0) + 1

        vec_q: dict[str, float] = {}
        for t, tf_val in query_tf.items():
            df_val = self._index.df(t)
            vec_q[t] = tfidf_weight(tf_val, N, df_val)

        # Candidate documents: union of postings for all query terms
        candidate_ids: set[str] = set()
        for t in tokens:
            candidate_ids |= self._index.boolean_or(t)

        scores: list[tuple[str, float]] = []
        for doc_id in candidate_ids:
            vec_d: dict[str, float] = {}
            for t in tokens:
                tf_val = self._index.tf(t, doc_id)
                df_val = self._index.df(t)
                vec_d[t] = tfidf_weight(tf_val, N, df_val)
            score = _cosine(vec_q, vec_d)
            if score > 0:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
