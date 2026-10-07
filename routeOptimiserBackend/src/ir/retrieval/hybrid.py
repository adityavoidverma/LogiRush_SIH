# src/ir/retrieval/hybrid.py
"""
Hybrid retrieval: BM25 + Dense + Freshness + Authority re-ranking.

Score = 0.45*bm25 + 0.35*semantic + 0.10*freshness + 0.10*authority
Weights are read from config.HYBRID_WEIGHTS so they can be tuned without
touching this file.

Geographic relevance is applied as a separate multiplier after fusion so
it can be boosted per cargo type without affecting the baseline weights.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from src.ir.config import HYBRID_WEIGHTS, TOP_K_DEFAULT, CARGO_RETRIEVAL_BOOSTS
from src.ir.ranking.freshness import freshness_score
from src.ir.ranking.authority import authority_score
from src.ir.ranking.geographic import geographic_score
from src.ir.schemas import RetrievedResult, EvidenceBundle

if TYPE_CHECKING:
    from src.ir.indexing.inverted_index import InvertedIndex
    from src.ir.indexing.tfidf import TFIDFRetriever
    from src.ir.retrieval.bm25 import BM25Retriever
    from src.ir.retrieval.dense import DenseRetriever
    from src.ir.schemas import IRDocument, ParsedQuery

logger = logging.getLogger("ir.hybrid")


class HybridRetriever:
    """
    Fuses BM25, TF-IDF, dense semantic, freshness, geographic, and authority
    signals into a single ranked evidence bundle.
    """

    def __init__(
        self,
        index: "InvertedIndex",
        bm25: "BM25Retriever",
        tfidf: "TFIDFRetriever",
        dense: "DenseRetriever",
        weights: dict[str, float] | None = None,
    ) -> None:
        self._index  = index
        self._bm25   = bm25
        self._tfidf  = tfidf
        self._dense  = dense
        self._weights = weights or dict(HYBRID_WEIGHTS)

    def retrieve(
        self,
        parsed_query: "ParsedQuery",
        top_k: int = TOP_K_DEFAULT,
        cargo_type: str | None = None,
    ) -> EvidenceBundle:
        """
        Run hybrid retrieval and return an EvidenceBundle.

        Steps
        -----
        1. Expand the query with synonyms from ParsedQuery.expanded_terms.
        2. Retrieve candidates from BM25, TF-IDF, and dense (each top 2×K).
        3. Union the candidate sets.
        4. Score each candidate on all signals.
        5. Fuse into a hybrid score.
        6. Apply geographic boost.
        7. Sort and return top-K as RetrievedResult objects.
        """
        t0 = time.perf_counter()

        expanded_text = parsed_query.raw + " " + " ".join(parsed_query.expanded_terms)

        # ── Retrieval ──────────────────────────────────────────────────
        fetch_k = top_k * 3
        bm25_scores:   dict[str, float] = dict(self._bm25.normalised_query(expanded_text, top_k=fetch_k))
        tfidf_scores:  dict[str, float] = dict(self._tfidf.query(expanded_text, top_k=fetch_k))
        dense_scores:  dict[str, float] = dict(self._dense.query(expanded_text,  top_k=fetch_k))

        # Normalise TF-IDF to [0,1]
        if tfidf_scores:
            max_t = max(tfidf_scores.values())
            if max_t > 0:
                tfidf_scores = {k: v / max_t for k, v in tfidf_scores.items()}

        candidate_ids = set(bm25_scores) | set(dense_scores) | set(tfidf_scores)
        logger.debug("Candidates: %d  (bm25=%d dense=%d tfidf=%d)",
                     len(candidate_ids), len(bm25_scores), len(dense_scores), len(tfidf_scores))

        if not candidate_ids:
            return EvidenceBundle(
                query=parsed_query.raw,
                parsed=parsed_query.to_dict(),
                results=[],
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # ── Cargo-aware signal boosts ──────────────────────────────────
        boosts = CARGO_RETRIEVAL_BOOSTS.get(cargo_type or "general", CARGO_RETRIEVAL_BOOSTS["general"])

        # ── Score fusion ───────────────────────────────────────────────
        w = self._weights
        results: list[RetrievedResult] = []

        for doc_id in candidate_ids:
            doc = self._index.get_document(doc_id)
            if doc is None:
                continue

            bm25_s  = bm25_scores.get(doc_id, 0.0)
            tfidf_s = tfidf_scores.get(doc_id, 0.0)
            sem_s   = dense_scores.get(doc_id, 0.0)

            fresh   = freshness_score(doc.date) * boosts.get("freshness", 1.0)
            fresh   = min(fresh, 1.0)
            auth    = authority_score(doc.source_type)
            geo     = geographic_score(doc, parsed_query) * boosts.get("geographic", 1.0)
            geo     = min(geo, 1.0)

            # Lexical = max of BM25 and TF-IDF
            lexical = max(bm25_s, tfidf_s)

            hybrid = (
                w.get("bm25", 0.45)      * lexical
                + w.get("semantic", 0.35) * sem_s
                + w.get("freshness", 0.10)* fresh
                + w.get("authority", 0.10)* auth
            )

            # Geographic boost: multiply rather than add — keeps the
            # score in [0,1] and lets irrelevant geography push rank down.
            hybrid_geo = hybrid * (0.5 + 0.5 * geo)

            results.append(RetrievedResult(
                document=doc,
                rank=0,            # set after sorting
                bm25=round(bm25_s, 4),
                tfidf=round(tfidf_s, 4),
                semantic=round(sem_s, 4),
                freshness=round(fresh, 4),
                geographic=round(geo, 4),
                authority=round(auth, 4),
                final_score=round(hybrid_geo, 4),
            ))

        # ── Sort and assign ranks ──────────────────────────────────────
        results.sort(key=lambda r: r.final_score, reverse=True)
        for i, r in enumerate(results[:top_k], start=1):
            r.rank = i

        latency = (time.perf_counter() - t0) * 1000
        logger.info("Hybrid retrieval: %d results in %.1f ms", len(results[:top_k]), latency)

        return EvidenceBundle(
            query=parsed_query.raw,
            parsed=parsed_query.to_dict(),
            results=results[:top_k],
            retrieval_method="hybrid",
            latency_ms=latency,
        )

    def retrieve_by_method(
        self,
        parsed_query: "ParsedQuery",
        method: str,
        top_k: int = TOP_K_DEFAULT,
    ) -> list[tuple[str, float]]:
        """
        Retrieve using a single named method.

        Returns list of (doc_id, score).
        Useful for the evaluation module.
        """
        text = parsed_query.raw + " " + " ".join(parsed_query.expanded_terms)
        if method == "bm25":
            return self._bm25.normalised_query(text, top_k=top_k)
        if method == "tfidf":
            raw = self._tfidf.query(text, top_k=top_k)
            if raw:
                m = max(s for _, s in raw)
                return [(d, s / m if m > 0 else 0.0) for d, s in raw]
            return []
        if method == "dense":
            return self._dense.query(text, top_k=top_k)
        # Default: full hybrid
        bundle = self.retrieve(parsed_query, top_k=top_k)
        return [(r.document.id, r.final_score) for r in bundle.results]
