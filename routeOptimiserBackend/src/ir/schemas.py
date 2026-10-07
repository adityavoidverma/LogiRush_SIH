# src/ir/schemas.py
"""
Pydantic-free document and result schemas for the LogiRush IR engine.

Using plain dataclasses so there are no extra dependencies beyond the stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IRDocument:
    """A searchable logistics / hazard document."""

    id: str
    title: str
    text: str
    source: str
    source_type: str          # one of SOURCE_AUTHORITY keys
    date: str                 # ISO-8601  e.g. "2026-09-06"
    location: str
    hazard: str
    severity: str             # "low" | "medium" | "high" | "critical"
    tags: list[str] = field(default_factory=list)
    provenance: str = "SYNTHETIC"   # "LIVE" | "SAMPLED" | "SYNTHETIC"

    # optional enrichments
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    route:     Optional[str]   = None
    state:     Optional[str]   = None
    district:  Optional[str]   = None
    highway:   Optional[str]   = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class RetrievedResult:
    """A single retrieved document with all contributing scores."""

    document: IRDocument
    rank: int
    bm25:       float = 0.0
    tfidf:      float = 0.0
    semantic:   float = 0.0
    freshness:  float = 0.0
    geographic: float = 0.0
    authority:  float = 0.0
    final_score: float = 0.0

    def score_breakdown(self) -> dict[str, float]:
        return {
            "bm25":       round(self.bm25,       4),
            "tfidf":      round(self.tfidf,       4),
            "semantic":   round(self.semantic,    4),
            "freshness":  round(self.freshness,   4),
            "geographic": round(self.geographic,  4),
            "authority":  round(self.authority,   4),
            "final_score": round(self.final_score, 4),
        }

    def to_dict(self) -> dict:
        d = self.document.to_dict()
        d["rank"]          = self.rank
        d["scores"]        = self.score_breakdown()
        d["final_score"]   = round(self.final_score, 4)
        d["explanation"]   = self._why()
        return d

    def _why(self) -> str:
        parts = []
        if self.bm25 > 0.5:
            parts.append("strong keyword match")
        if self.semantic > 0.6:
            parts.append("high semantic similarity")
        if self.freshness > 0.8:
            parts.append("very recent report")
        if self.geographic > 0.7:
            parts.append("directly on the queried corridor")
        if self.authority >= 0.9:
            parts.append("authoritative government source")
        return "; ".join(parts) if parts else "relevant to query"


@dataclass
class ParsedQuery:
    """Structured representation produced by the query parser."""
    raw: str
    origin:      Optional[str] = None
    destination: Optional[str] = None
    cargo:       Optional[str] = None
    hazard:      Optional[str] = None
    date:        Optional[str] = None
    urgency:     str = "normal"
    intent:      str = "route_risk"   # "route_risk" | "hazard_info" | "general"
    expanded_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != []}


@dataclass
class EvidenceBundle:
    """Top-K ranked results plus metadata passed to the RAG layer."""
    query: str
    parsed: dict
    results: list[RetrievedResult] = field(default_factory=list)
    retrieval_method: str = "hybrid"
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "query":            self.query,
            "parsed_query":     self.parsed,
            "retrieval_method": self.retrieval_method,
            "latency_ms":       round(self.latency_ms, 1),
            "results":          [r.to_dict() for r in self.results],
        }
