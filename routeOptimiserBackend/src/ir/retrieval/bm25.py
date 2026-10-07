# src/ir/retrieval/bm25.py
"""
BM25 retrieval — Okapi BM25 over the inverted index.

Parameters k1 and b are read from config so they can be tuned without
touching this file.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from src.ir.config import BM25_K1, BM25_B

if TYPE_CHECKING:
    from src.ir.indexing.inverted_index import InvertedIndex


class BM25Retriever:
    """
    Okapi BM25 retrieval.

    Score for query Q and document D:

        score(Q, D) = Σ_t  idf(t) * [ tf(t,D) * (k1+1) ]
                                      / [ tf(t,D) + k1*(1-b+b*|D|/avgdl) ]

    where:
        idf(t)  = log( (N - df(t) + 0.5) / (df(t) + 0.5) + 1 )
        |D|     = document length in tokens
        avgdl   = average document length across corpus
    """

    def __init__(self, index: "InvertedIndex",
                 k1: float = BM25_K1, b: float = BM25_B) -> None:
        self._index = index
        self.k1 = k1
        self.b = b

    def _idf(self, token: str) -> float:
        N = self._index.N
        df = self._index.df(token)
        return math.log((N - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query_tokens: list[str], doc_id: str) -> float:
        """BM25 score for a pre-tokenized query against a single document."""
        avgdl = self._index.avg_doc_len()
        dl = self._index.doc_len(doc_id)
        total = 0.0
        for t in query_tokens:
            tf = self._index.tf(t, doc_id)
            if tf == 0:
                continue
            idf = self._idf(t)
            denom = tf + self.k1 * (1 - self.b + self.b * (dl / max(avgdl, 1)))
            total += idf * (tf * (self.k1 + 1)) / denom
        return total

    def query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Retrieve top-K documents by BM25 score.

        Returns
        -------
        list of (doc_id, score) sorted by score descending.
        Score is NOT normalised to [0,1] — raw BM25.
        """
        tokens = self._index.tokenize(query_text)
        if not tokens:
            return []

        # Candidate docs: union of postings for all query terms
        candidate_ids: set[str] = set()
        for t in tokens:
            candidate_ids |= self._index.boolean_or(t)

        scores = [(doc_id, self.score(tokens, doc_id)) for doc_id in candidate_ids]
        scores = [(d, s) for d, s in scores if s > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def normalised_query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Same as query() but scores normalised to [0, 1] by dividing by the max.

        Used by the hybrid scorer so BM25 and semantic scores are on the same scale.
        """
        raw = self.query(query_text, top_k=top_k * 2)
        if not raw:
            return []
        max_score = max(s for _, s in raw)
        if max_score == 0:
            return [(d, 0.0) for d, _ in raw[:top_k]]
        normalised = [(d, s / max_score) for d, s in raw]
        return normalised[:top_k]
