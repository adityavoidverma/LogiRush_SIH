# src/ir/indexing/inverted_index.py
"""
Inverted index over the logistics corpus.

Supports:
  - Boolean retrieval (AND / OR / NOT)
  - Phrase search  — exact consecutive token sequence, e.g. "NH27 flooding"
  - Proximity search — two terms within K tokens of each other
  - Token-level posting lists used by BM25 and TF-IDF
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from src.ir.config import STOP_WORDS
from src.ir.schemas import IRDocument


def _tokenize(text: str) -> list[str]:
    """Lower-case, strip punctuation, remove stop-words, return tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def _tokenize_raw(text: str) -> list[str]:
    """Tokenize without stop-word removal — needed for positional index."""
    return re.findall(r"[a-z0-9]+", text.lower())


class InvertedIndex:
    """
    Classic posting-list inverted index with positional extension.

    Positional posting: token → {doc_id: [pos0, pos1, ...]}
    Used for phrase search and proximity search.
    """

    def __init__(self) -> None:
        # token → set of doc ids  (for fast Boolean)
        self._postings: dict[str, set[str]] = defaultdict(set)
        # token → {doc_id → [positions]}  (for phrase / proximity)
        self._positions: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        # (token, doc_id) → raw term frequency
        self._tf: dict[tuple[str, str], int] = defaultdict(int)
        # doc_id → document
        self._docs: dict[str, IRDocument] = {}
        # doc_id → filtered token list (for BM25)
        self._doc_tokens: dict[str, list[str]] = {}
        # doc_id → raw token list with positions (for phrase/proximity)
        self._doc_raw_tokens: dict[str, list[str]] = {}
        self._N = 0

    # ──────────────────────────────────────────
    # Building
    # ──────────────────────────────────────────

    def add_document(self, doc: IRDocument) -> None:
        """Index a single document."""
        self._docs[doc.id] = doc

        combined = f"{doc.title} {doc.text} {' '.join(doc.tags)}"

        # Filtered tokens for BM25/TF-IDF
        filtered = _tokenize(combined)
        self._doc_tokens[doc.id] = filtered
        for token in filtered:
            self._postings[token].add(doc.id)
            self._tf[(token, doc.id)] += 1

        # Raw tokens with positions for phrase/proximity
        raw = _tokenize_raw(combined)
        self._doc_raw_tokens[doc.id] = raw
        for pos, token in enumerate(raw):
            self._positions[token][doc.id].append(pos)

        self._N += 1

    def build(self, documents: Iterable[IRDocument]) -> "InvertedIndex":
        for doc in documents:
            self.add_document(doc)
        return self

    # ──────────────────────────────────────────
    # Boolean retrieval
    # ──────────────────────────────────────────

    def boolean_and(self, *terms: str) -> set[str]:
        if not terms:
            return set()
        sets = [self._postings.get(t.lower(), set()) for t in terms]
        result = sets[0].copy()
        for s in sets[1:]:
            result &= s
        return result

    def boolean_or(self, *terms: str) -> set[str]:
        result: set[str] = set()
        for t in terms:
            result |= self._postings.get(t.lower(), set())
        return result

    def boolean_not(self, include_term: str, exclude_term: str) -> set[str]:
        include = self._postings.get(include_term.lower(), set())
        exclude = self._postings.get(exclude_term.lower(), set())
        return include - exclude

    def boolean_query(self, query: str) -> set[str]:
        """
        Parse and execute a Boolean query.
        Supports: AND  OR  NOT
        Examples: "flood AND Assam"  "landslide OR rockfall"  "cyclone NOT historical"
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
        return self._postings.get(q.lower(), set())

    # ──────────────────────────────────────────
    # Phrase search
    # ──────────────────────────────────────────

    def phrase_search(self, phrase: str) -> list[dict]:
        """
        Find documents containing the exact phrase (consecutive tokens).

        Parameters
        ----------
        phrase : e.g. "NH27 flooding" or "Brahmaputra overflow"

        Returns
        -------
        list of {"doc_id", "document", "match_positions"} dicts,
        sorted by number of phrase occurrences descending.
        """
        tokens = _tokenize_raw(phrase.lower())
        if not tokens:
            return []

        # Candidate docs must contain all tokens
        candidate_ids = set(self._positions.get(tokens[0], {}).keys())
        for t in tokens[1:]:
            candidate_ids &= set(self._positions.get(t, {}).keys())

        results = []
        for doc_id in candidate_ids:
            match_positions = self._find_phrase_positions(tokens, doc_id)
            if match_positions:
                doc = self._docs[doc_id]
                results.append({
                    "doc_id":          doc_id,
                    "document":        doc,
                    "match_count":     len(match_positions),
                    "match_positions": match_positions,
                    "snippet":         self._snippet(doc, tokens),
                })

        results.sort(key=lambda x: x["match_count"], reverse=True)
        return results

    def _find_phrase_positions(self, tokens: list[str], doc_id: str) -> list[int]:
        """Return starting positions in doc_id where the token sequence occurs."""
        if not tokens:
            return []
        first_positions = self._positions.get(tokens[0], {}).get(doc_id, [])
        matches = []
        for start in first_positions:
            if all(
                start + i in self._positions.get(t, {}).get(doc_id, [])
                for i, t in enumerate(tokens)
            ):
                matches.append(start)
        return matches

    # ──────────────────────────────────────────
    # Proximity search
    # ──────────────────────────────────────────

    def proximity_search(self, term1: str, term2: str, window: int = 10) -> list[dict]:
        """
        Find documents where term1 and term2 appear within `window` tokens of each other.

        Parameters
        ----------
        term1, term2 : search terms
        window       : max token distance (default 10)

        Returns
        -------
        list of {"doc_id", "document", "min_distance"} sorted by distance ascending.
        """
        t1, t2 = term1.lower(), term2.lower()
        ids1 = set(self._positions.get(t1, {}).keys())
        ids2 = set(self._positions.get(t2, {}).keys())
        common = ids1 & ids2

        results = []
        for doc_id in common:
            pos1 = self._positions[t1][doc_id]
            pos2 = self._positions[t2][doc_id]
            min_dist = min(abs(p1 - p2) for p1 in pos1 for p2 in pos2)
            if min_dist <= window:
                doc = self._docs[doc_id]
                results.append({
                    "doc_id":       doc_id,
                    "document":     doc,
                    "min_distance": min_dist,
                    "snippet":      self._snippet(doc, [t1, t2]),
                })

        results.sort(key=lambda x: x["min_distance"])
        return results

    # ──────────────────────────────────────────
    # Snippet helper
    # ──────────────────────────────────────────

    def _snippet(self, doc: IRDocument, highlight_tokens: list[str], context: int = 12) -> str:
        """Return a text snippet centred around the first match of any highlight token."""
        raw = _tokenize_raw(f"{doc.title} {doc.text}")
        highlight_set = set(highlight_tokens)
        for i, token in enumerate(raw):
            if token in highlight_set:
                start = max(0, i - context)
                end   = min(len(raw), i + context)
                snippet_tokens = raw[start:end]
                snippet = " ".join(
                    f"**{t}**" if t in highlight_set else t
                    for t in snippet_tokens
                )
                return ("… " if start > 0 else "") + snippet + (" …" if end < len(raw) else "")
        return doc.text[:150]

    # ──────────────────────────────────────────
    # Accessors
    # ──────────────────────────────────────────

    def df(self, token: str) -> int:
        return len(self._postings.get(token.lower(), set()))

    def tf(self, token: str, doc_id: str) -> int:
        return self._tf.get((token.lower(), doc_id), 0)

    def doc_len(self, doc_id: str) -> int:
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
        return _tokenize(text)
