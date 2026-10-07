# src/ir/engine.py
"""
IREngine — the single entry point for all IR operations.

Assembles the index, retrievers, and rankers and exposes:
  - search(query, top_k, method, cargo_type) → EvidenceBundle
  - get_document(doc_id) → IRDocument
  - boolean_query(query) → list[IRDocument]
  - evaluate(method, top_k) → dict

The engine is a singleton: import and use `ir_engine`.
"""

from __future__ import annotations

import logging
import os

from src.ir.corpus import build_corpus
from src.ir.indexing.inverted_index import InvertedIndex
from src.ir.indexing.tfidf import TFIDFRetriever
from src.ir.retrieval.bm25 import BM25Retriever
from src.ir.retrieval.dense import DenseRetriever
from src.ir.retrieval.hybrid import HybridRetriever
from src.ir.query.parser import parse_query
from src.ir.query.expansion import expand_query
from src.ir.schemas import EvidenceBundle, IRDocument, ParsedQuery

logger = logging.getLogger("ir.engine")


class IREngine:
    """Thin orchestration layer over the IR components."""

    def __init__(self) -> None:
        self._built = False
        self._index:   InvertedIndex  | None = None
        self._tfidf:   TFIDFRetriever | None = None
        self._bm25:    BM25Retriever  | None = None
        self._dense:   DenseRetriever | None = None
        self._hybrid:  HybridRetriever | None = None

    # ──────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────

    def build(self, live_incidents: list[dict] | None = None) -> "IREngine":
        """
        Build the complete IR index.

        Parameters
        ----------
        live_incidents : Optional list of incident dicts from the database,
                         injected as LIVE documents into the corpus.
        """
        logger.info("Building IR engine …")
        documents = build_corpus(live_incidents)

        self._index = InvertedIndex().build(documents)
        self._tfidf = TFIDFRetriever(self._index)
        self._bm25  = BM25Retriever(self._index)
        self._dense = DenseRetriever()
        self._dense.build(documents)
        self._hybrid = HybridRetriever(
            index=self._index,
            bm25=self._bm25,
            tfidf=self._tfidf,
            dense=self._dense,
        )

        self._built = True
        logger.info("IR engine ready: %d documents indexed", self._index.N)
        return self

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    # ──────────────────────────────────────────
    # Search
    # ──────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 10,
        method: str = "hybrid",
        cargo_type: str | None = None,
    ) -> EvidenceBundle:
        """
        Main search entry point.

        Parameters
        ----------
        query     : raw natural-language query
        top_k     : number of results to return
        method    : "hybrid" | "bm25" | "tfidf" | "dense"
        cargo_type: optional cargo type for boosting signals
        """
        self._ensure_built()

        pq = parse_query(query)
        pq.expanded_terms = expand_query(query, pq.hazard, pq.cargo or cargo_type)

        logger.info("Search: %r  method=%s  origin=%s  dest=%s  cargo=%s",
                    query[:80], method, pq.origin, pq.destination, pq.cargo or cargo_type)
        logger.debug("Expanded terms: %s", pq.expanded_terms[:10])

        if method == "hybrid":
            return self._hybrid.retrieve(pq, top_k=top_k, cargo_type=cargo_type or pq.cargo)

        # Single-method: populate ONLY the score field that corresponds to the method.
        # All other scores stay 0.0 so the "Why ranked?" panel is honest about what
        # was actually used — no phantom BM25/TF-IDF scores when Dense-only was selected.
        raw_results = self._hybrid.retrieve_by_method(pq, method, top_k=top_k)
        from src.ir.schemas import RetrievedResult
        from src.ir.ranking.freshness import freshness_score
        from src.ir.ranking.authority import authority_score
        from src.ir.ranking.geographic import geographic_score

        results = []
        for rank, (doc_id, score) in enumerate(raw_results, start=1):
            doc = self._index.get_document(doc_id)
            if not doc:
                continue
            kwargs = dict(document=doc, rank=rank, final_score=round(score, 4))
            if method == "bm25":
                kwargs["bm25"] = round(score, 4)
            elif method == "tfidf":
                kwargs["tfidf"] = round(score, 4)
            elif method == "dense":
                kwargs["semantic"] = round(score, 4)
            # Always compute the signal scores so the panel is informative
            kwargs["freshness"]  = round(freshness_score(doc.date), 4)
            kwargs["authority"]  = round(authority_score(doc.source_type), 4)
            kwargs["geographic"] = round(geographic_score(doc, pq), 4)
            results.append(RetrievedResult(**kwargs))
        return EvidenceBundle(
            query=query,
            parsed=pq.to_dict(),
            results=results,
            retrieval_method=method,
        )

    def get_document(self, doc_id: str) -> IRDocument | None:
        self._ensure_built()
        return self._index.get_document(doc_id)

    def boolean_query(self, query: str) -> list[IRDocument]:
        """Run a Boolean retrieval query (AND / OR / NOT)."""
        self._ensure_built()
        doc_ids = self._index.boolean_query(query)
        return [self._index.get_document(d) for d in doc_ids if self._index.get_document(d)]

    def evaluate(self, method: str = "hybrid", top_k: int = 5) -> dict:
        """Run the judged evaluation dataset and return metrics."""
        self._ensure_built()
        from src.ir.evaluation.metrics import evaluate_retriever
        return evaluate_retriever(self._hybrid, method=method, top_k=top_k)

    @property
    def document_count(self) -> int:
        if self._index is None:
            return 0
        return self._index.N

    def rebuild(self, live_incidents: list[dict] | None = None) -> "IREngine":
        """Rebuild the index (e.g. after new incidents are added)."""
        self._built = False
        return self.build(live_incidents)


# ── Singleton ──────────────────────────────────────────────────────────
ir_engine = IREngine()
