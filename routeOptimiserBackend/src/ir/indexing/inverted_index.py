# src/ir/indexing/inverted_index.py
"""
Inverted index over the logistics corpus.

Supports:
  - Boolean retrieval (AND / OR / NOT)
  - Token-level posting lists used by BM25 and TF-IDF
  - Simple inspectable data structure (dict[token → set[doc_id]])
"""

from __future__ import annotations

import re
import math
from collections import defaultdict
from typing import Iterable

from src.ir.config import STOP_WORDS
from src.ir.schemas import IRDocument


def _tokenize(text: str) -> list[str]:
    """Lower-case, strip punctuation, remove stop-words, return tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


class InvertedIndex:
    """
    Classic posting-list inverted index.

    Each entry maps token → frozenset of document IDs.
    Term-frequency (tf) per document is also stored for TF-IDF.
    """

    def __init__(self) -> None:
        # token → set of doc ids
        self._postings: dict[str, set[str]] = defaultdict(set)
        # (token, doc_id) → raw term frequency
        self._tf: dict[tuple[str, str], int] = defaultdict(int)
        # doc_id → document
        self._docs: dict[str, IRDocument] = {}
        # doc_id → token list (for BM25 document-length tracking)
        self._doc_tokens: dict[str, list[str]] = {}
        # Total documents indexed
        self._N = 0

    # ──────────────────────────────────────────
    # Building
    # ──────────────────────────────────────────

    def add_document(self, doc: IRDocument) -> None:
        """Index a single document."""
        self._docs[doc.id] = doc
        combined = f"{doc.title} {doc.text} {' '.join(doc.tags)}"
        tokens = _tokenize(combined)
        self._doc_tokens[doc.id] = tokens
        for token in tokens:
            self._postings[token].add(doc.id)
            self._tf[(token, doc.id)] += 1
        self._N += 1

    def build(self, documents: Iterable[IRDocument]) -> "InvertedIndex":
        """Index all documents from an iterable."""
        for doc in documents:
            self.add_document(doc)
        return self

    # ──────────────────────────────────────────
    # Boolean retrieval
    # ──────────────────────────────────────────

    def boolean_and(self, *terms: str) -> set[str]:
        """Return doc IDs that contain ALL of the given terms."""
        if not terms:
            return set()
        sets = [self._postings.get(t.lower(), set()) for t in terms]
        result = sets[0].copy()
        for s in sets[1:]:
            result &= s
        return result

    def boolean_or(self, *terms: str) -> set[str]:
        """Return doc IDs that contain ANY of the given terms."""
        result: set[str] = set()
        for t in terms:
            result |= self._postings.get(t.lower(), set())
        return result

    def boolean_not(self, include_term: str, exclude_term: str) -> set[str]:
        """Return doc IDs that contain include_term but NOT exclude_term."""
        include = self._postings.get(include_term.lower(), set())
        exclude = self._postings.get(exclude_term.lower(), set())
        return include - exclude

    def boolean_query(self, query: str) -> set[str]:
        """
        Parse and execute a simple Boolean query.

        Supports:  term AND term   term OR term   term NOT term
        Examples:  "flood AND Assam"   "landslide OR rockfall"   "cyclone NOT historical"

        Multi-operator queries are not supported; use one operator per query.
        """
        q = query.strip()
        if " AND " in q:
            parts = [p.strip() for p in q.split(" AND ")]
            return self.boolean_and(*parts)
        if " OR " in q:
            parts = [p.strip() for p in q.split(" OR ")]
            return self.boolean_or(*parts)
        if " NOT " in q:
            parts = [p.strip() for p in q.split(" NOT ", 1)]
            return self.boolean_not(parts[0], parts[1])
        # Single term
        return self._postings.get(q.lower(), set())

    # ──────────────────────────────────────────
    # Accessors used by TF-IDF and BM25
    # ──────────────────────────────────────────

    def df(self, token: str) -> int:
        """Document frequency of a token."""
        return len(self._postings.get(token.lower(), set()))

    def tf(self, token: str, doc_id: str) -> int:
        """Raw term frequency of token in document."""
        return self._tf.get((token.lower(), doc_id), 0)

    def doc_len(self, doc_id: str) -> int:
        """Number of tokens in a document."""
        return len(self._doc_tokens.get(doc_id, []))

    def avg_doc_len(self) -> float:
        if not self._doc_tokens:
            return 0.0
        return sum(len(v) for v in self._doc_tokens.values()) / len(self._doc_tokens)

    @property
    def N(self) -> int:
        return self._N

    def get_document(self, doc_id: str) -> IRDocument | None:
        return self._docs.get(doc_id)

    def all_documents(self) -> list[IRDocument]:
        return list(self._docs.values())

    def vocabulary(self) -> set[str]:
        return set(self._postings.keys())

    def tokenize(self, text: str) -> list[str]:
        """Expose tokenizer so other modules use a consistent implementation."""
        return _tokenize(text)
