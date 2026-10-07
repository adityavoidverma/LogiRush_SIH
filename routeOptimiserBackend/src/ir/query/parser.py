# src/ir/query/parser.py
"""
Logistics query parser.

Extracts structured fields from a natural-language logistics query:
    origin, destination, cargo, hazard, date, urgency, intent

Uses keyword/pattern matching — no external NLP dependency required.
The parser is inspectable and deterministic.
"""

from __future__ import annotations

import re
from src.ir.schemas import ParsedQuery
from src.ir.ranking.geographic import CITY_COORDS, _normalise

# ──────────────────────────────────────────────────────────────────
# Known city names (from geographic module) + aliases
# ──────────────────────────────────────────────────────────────────
_KNOWN_PLACES: set[str] = set(CITY_COORDS.keys()) | {
    "northeast india", "ner", "north east", "northeast",
    "assam", "meghalaya", "manipur", "mizoram", "nagaland",
    "tripura", "sikkim", "arunachal pradesh", "west bengal",
    "bihar", "odisha", "uttarakhand", "himachal pradesh",
    "rajasthan", "kerala", "andhra pradesh", "maharashtra",
    "karnataka", "tamil nadu", "jammu", "kashmir", "ladakh",
    "punjab", "haryana", "gujarat", "madhya pradesh", "chhattisgarh",
    "jharkhand", "telangana", "goa", "pan india", "india",
    "new delhi",
}

_CARGO_KEYWORDS: dict[str, list[str]] = {
    "medicine":   ["medicine", "medicines", "medical", "drugs", "pharmaceutical", "medication", "hospital supplies"],
    "relief":     ["relief", "relief material", "disaster relief", "humanitarian", "aid"],
    "perishable": ["perishable", "perishables", "vegetable", "vegetables", "fruit", "fruits", "agricultural"],
    "food":       ["food", "grain", "grains", "ration", "rations", "provisions"],
    "general":    ["cargo", "goods", "freight", "load", "shipment", "supplies"],
}

_HAZARD_KEYWORDS: dict[str, list[str]] = {
    "flood":      ["flood", "flooding", "waterlogged", "inundation", "submerged"],
    "landslide":  ["landslide", "landslip", "rockfall", "debris", "slope failure"],
    "cyclone":    ["cyclone", "storm", "hurricane"],
    "rainfall":   ["rain", "rainfall", "cloudburst", "downpour", "heavy rain"],
    "heat":       ["heat", "heatwave", "hot"],
    "road_block": ["block", "blocked", "closure", "closed", "disruption", "traffic"],
    "accident":   ["accident", "crash", "collision"],
    "infra":      ["bridge", "infrastructure", "pothole", "damage"],
}

_URGENCY_KEYWORDS: dict[str, str] = {
    "urgent": "high", "immediately": "high", "asap": "high",
    "emergency": "critical", "critical": "critical",
    "low priority": "low", "flexible": "low",
}

_INTENT_PATTERNS: list[tuple[str, str]] = [
    (r"\b(can|should|safe|possible|viable)\b.*\b(transport|ship|send|move|deliver)\b", "route_risk"),
    (r"\b(route|way|path|road|highway)\b",                                              "route_risk"),
    (r"\b(risk|danger|hazard|warning|alert)\b",                                         "hazard_info"),
    (r"\b(alternative|alternate|bypass|detour)\b",                                      "route_risk"),
]

_PREPOSITIONS = r"(?:from|between|via|through|near|at|in|around|to)"


def _extract_places(text: str) -> tuple[str | None, str | None]:
    """
    Extract (origin, destination) from a query string.

    Tries patterns like:
      from X to Y
      between X and Y
      X to Y
    Falls back to scanning for known place names.
    """
    t = text.lower()

    # from X to Y
    m = re.search(r"\bfrom\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+today|\s+\?|$|\s+by|\s+for|\s+on)", t)
    if m:
        return _match_place(m.group(1).strip()), _match_place(m.group(2).strip())

    # between X and Y
    m = re.search(r"\bbetween\s+([a-z\s]+?)\s+and\s+([a-z\s]+?)(?:\s+\?|$|\s+today)", t)
    if m:
        return _match_place(m.group(1).strip()), _match_place(m.group(2).strip())

    # X to Y (without "from")
    m = re.search(r"\b([a-z\s]{3,20}?)\s+to\s+([a-z\s]{3,20}?)(?:\s+\?|$|\s+today)", t)
    if m:
        p1 = _match_place(m.group(1).strip())
        p2 = _match_place(m.group(2).strip())
        if p1 and p2:
            return p1, p2

    # Scan for any known places
    found = []
    for place in sorted(_KNOWN_PLACES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(place) + r"\b", t):
            found.append(place)
            if len(found) == 2:
                break

    if len(found) >= 2:
        return found[0], found[1]
    if len(found) == 1:
        return found[0], None
    return None, None


def _match_place(candidate: str) -> str | None:
    """Return the canonical place name if candidate matches a known place."""
    c = _normalise(candidate)
    if c in _KNOWN_PLACES:
        return c.title()
    for p in sorted(_KNOWN_PLACES, key=len, reverse=True):
        if c in p or p in c:
            return p.title()
    # Return raw if non-trivial
    if len(c) > 3:
        return candidate.title()
    return None


def _extract_cargo(text: str) -> str | None:
    t = text.lower()
    for cargo, keywords in _CARGO_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return cargo
    return None


def _extract_hazard(text: str) -> str | None:
    t = text.lower()
    for hazard, keywords in _HAZARD_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return hazard
    return None


def _extract_urgency(text: str) -> str:
    t = text.lower()
    for kw, level in _URGENCY_KEYWORDS.items():
        if kw in t:
            return level
    return "normal"


def _extract_intent(text: str) -> str:
    t = text.lower()
    for pattern, intent in _INTENT_PATTERNS:
        if re.search(pattern, t):
            return intent
    return "general"


def _extract_date(text: str) -> str | None:
    t = text.lower()
    if "today" in t:
        return "today"
    if "tomorrow" in t:
        return "tomorrow"
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)
    return None


def parse_query(raw_query: str) -> ParsedQuery:
    """
    Parse a natural-language logistics query into structured fields.

    Example
    -------
    >>> parse_query("Can I transport medicine from Guwahati to Kolkata today?")
    ParsedQuery(origin='Guwahati', destination='Kolkata', cargo='medicine', ...)
    """
    origin, destination = _extract_places(raw_query)
    cargo   = _extract_cargo(raw_query)
    hazard  = _extract_hazard(raw_query)
    urgency = _extract_urgency(raw_query)
    intent  = _extract_intent(raw_query)
    date    = _extract_date(raw_query)

    return ParsedQuery(
        raw=raw_query,
        origin=origin,
        destination=destination,
        cargo=cargo,
        hazard=hazard,
        date=date,
        urgency=urgency,
        intent=intent,
    )
