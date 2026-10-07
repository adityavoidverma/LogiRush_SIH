# src/ir/query/expansion.py
"""
Query expansion using a domain-specific synonym dictionary.

Improves recall without destroying precision by adding logistics/hazard
synonyms to the original query terms.

The expanded terms are logged so the system is debuggable.
"""

from __future__ import annotations

import logging
import re

from src.ir.config import HAZARD_SYNONYMS, STOP_WORDS

logger = logging.getLogger("ir.expansion")

# Additional logistics/geographic synonyms beyond HAZARD_SYNONYMS
_DOMAIN_SYNONYMS: dict[str, list[str]] = {
    # transport verbs
    "transport": ["shipment", "freight", "cargo", "delivery", "logistics"],
    "ship":      ["transport", "freight", "deliver", "send"],
    "route":     ["corridor", "highway", "road", "path", "NH"],

    # geography
    "ner":          ["northeast india", "northeast", "assam", "meghalaya"],
    "northeast":    ["NER", "northeast india", "assam", "meghalaya"],
    "guwahati":     ["Guwahati", "NH27", "Brahmaputra", "Assam"],
    "kolkata":      ["Kolkata", "West Bengal", "NH12", "NH16"],

    # severity
    "high risk":     ["dangerous", "blocked", "critical", "disrupted"],
    "disruption":    ["blockage", "closure", "delay", "affected"],

    # cargo
    "medicine":   ["medical supplies", "pharmaceutical", "drugs", "healthcare"],
    "relief":     ["humanitarian aid", "disaster relief", "emergency supplies"],
    "perishable": ["cold chain", "agricultural produce", "time sensitive"],
}

# Merge with HAZARD_SYNONYMS
_ALL_SYNONYMS: dict[str, list[str]] = {**HAZARD_SYNONYMS, **_DOMAIN_SYNONYMS}


def expand_query(raw_query: str, parsed_hazard: str | None = None,
                 parsed_cargo: str | None = None) -> list[str]:
    """
    Return a list of expansion terms to append to the raw query.

    Parameters
    ----------
    raw_query     : original user query
    parsed_hazard : hazard type extracted by the parser (optional)
    parsed_cargo  : cargo type extracted by the parser (optional)

    Returns
    -------
    Flat list of expansion terms (no duplicates, no stop-words).
    """
    tokens = re.findall(r"[a-z0-9]+", raw_query.lower())
    expanded: set[str] = set()

    for token in tokens:
        if token in STOP_WORDS:
            continue
        for key, synonyms in _ALL_SYNONYMS.items():
            if token == key.lower() or token in key.lower():
                expanded.update(s.lower() for s in synonyms)

    # Add hazard and cargo expansions explicitly
    if parsed_hazard and parsed_hazard in HAZARD_SYNONYMS:
        expanded.update(s.lower() for s in HAZARD_SYNONYMS[parsed_hazard])
    if parsed_cargo and parsed_cargo in _DOMAIN_SYNONYMS:
        expanded.update(s.lower() for s in _DOMAIN_SYNONYMS[parsed_cargo])

    # Remove terms already in original query
    original_words = set(tokens)
    expansion = sorted(expanded - original_words)

    logger.debug("Query expansion: %s → +%s", raw_query[:60], expansion[:10])
    return expansion
