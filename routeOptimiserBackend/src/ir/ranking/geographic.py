# src/ir/ranking/geographic.py
"""
Geographic relevance scoring.

A document is geographically relevant to a query if:
  - Its location / state / tags match the query origin, destination, or route.
  - Its coordinates are physically close to the queried corridor.

This is a transparent, rule-based implementation — no ML.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ir.schemas import IRDocument, ParsedQuery


# Major Indian city → (lat, lon) for rough distance calculations.
# Extend this table as the corpus grows.
CITY_COORDS: dict[str, tuple[float, float]] = {
    "guwahati":        (26.1445, 91.7362),
    "shillong":        (25.5788, 91.8933),
    "imphal":          (24.8170, 93.9368),
    "aizawl":          (23.7271, 92.7176),
    "kohima":          (25.6700, 94.1100),
    "agartala":        (23.8315, 91.2868),
    "gangtok":         (27.3314, 88.6138),
    "itanagar":        (27.0844, 93.6053),
    "kolkata":         (22.5726, 88.3639),
    "delhi":           (28.6139, 77.2090),
    "mumbai":          (19.0760, 72.8777),
    "chennai":         (13.0827, 80.2707),
    "hyderabad":       (17.3850, 78.4867),
    "bangalore":       (12.9716, 77.5946),
    "bengaluru":       (12.9716, 77.5946),
    "patna":           (25.5941, 85.1376),
    "bhubaneswar":     (20.2961, 85.8245),
    "jaipur":          (26.9124, 75.7873),
    "lucknow":         (26.8467, 80.9462),
    "chandigarh":      (30.7333, 76.7794),
    "thiruvananthapuram": (8.5241, 76.9366),
    "trivandrum":      (8.5241, 76.9366),
    "kochi":           (9.9312, 76.2673),
    "ernakulam":       (9.9816, 76.2999),
    "visakhapatnam":   (17.6868, 83.2185),
    "tezpur":          (26.6333, 92.8000),
    "silchar":         (24.8333, 92.7789),
    "dibrugarh":       (27.4728, 94.9120),
    "jorhat":          (26.7465, 94.2026),
    "nagaon":          (26.3460, 92.6841),
    "siliguri":        (26.7271, 88.3953),
    "darjeeling":      (27.0360, 88.2627),
    "rangpo":          (27.1760, 88.5313),
    "haridwar":        (29.9457, 78.1642),
    "manali":          (32.2432, 77.1892),
    "paradip":         (20.3164, 86.6090),
    "muzaffarpur":     (26.1209, 85.3647),
    "cherrapunji":     (25.2701, 91.7318),
    "jaisalmer":       (26.9157, 70.9083),
    "srinagar":        (34.0837, 74.7973),
    "leh":             (34.1526, 77.5770),
}

# State name fragments → list of cities in that state (for tag matching)
STATE_CITIES: dict[str, list[str]] = {
    "assam":             ["guwahati", "tezpur", "silchar", "dibrugarh", "jorhat", "nagaon"],
    "meghalaya":         ["shillong", "cherrapunji"],
    "manipur":           ["imphal"],
    "mizoram":           ["aizawl"],
    "nagaland":          ["kohima"],
    "tripura":           ["agartala"],
    "sikkim":            ["gangtok", "rangpo"],
    "arunachal pradesh": ["itanagar"],
    "west bengal":       ["kolkata", "siliguri", "darjeeling"],
    "bihar":             ["patna", "muzaffarpur"],
    "odisha":            ["bhubaneswar", "paradip"],
    "uttarakhand":       ["haridwar"],
    "himachal pradesh":  ["manali", "chandigarh"],
    "rajasthan":         ["jaipur", "jaisalmer"],
    "kerala":            ["kochi", "ernakulam", "trivandrum", "thiruvananthapuram"],
    "andhra pradesh":    ["visakhapatnam", "hyderabad"],
    "maharashtra":       ["mumbai"],
    "karnataka":         ["bangalore", "bengaluru"],
    "jammu kashmir":     ["srinagar"],
    "ladakh":            ["leh"],
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _coords_for(place: str) -> tuple[float, float] | None:
    key = _normalise(place)
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    # partial match
    for city, coords in CITY_COORDS.items():
        if key in city or city in key:
            return coords
    return None


def geographic_score(
    doc: "IRDocument",
    parsed_query: "ParsedQuery | None" = None,
) -> float:
    """
    Return a geographic relevance score in [0, 1].

    Logic:
      1. Exact place-name match in doc text/tags/location → 1.0
      2. Same state as origin or destination → 0.7
      3. Coordinate proximity (< 100 km of origin or destination) → 0.5–0.9
      4. Corridor tag match (highway tag shared) → 0.6
      5. No geographic signal → 0.1 (base relevance)
    """
    if parsed_query is None:
        return 0.1

    origin      = _normalise(parsed_query.origin or "")
    destination = _normalise(parsed_query.destination or "")

    doc_text  = _normalise(f"{doc.title} {doc.text} {doc.location} {' '.join(doc.tags)}")
    doc_state = _normalise(doc.state or "")

    # 1. Exact name match
    for place in (origin, destination):
        if place and place in doc_text:
            return 1.0

    # 2. State match
    for place in (origin, destination):
        if not place:
            continue
        for state, cities in STATE_CITIES.items():
            if place in cities or place == state or place in state:
                if state in doc_state or state in doc_text:
                    return 0.70

    # 3. Coordinate proximity
    origin_coords      = _coords_for(parsed_query.origin or "")
    destination_coords = _coords_for(parsed_query.destination or "")

    if doc.latitude is not None and doc.longitude is not None:
        for coords in filter(None, [origin_coords, destination_coords]):
            dist = _haversine_km(coords[0], coords[1], doc.latitude, doc.longitude)
            if dist < 50:
                return 0.90
            if dist < 150:
                return 0.75
            if dist < 400:
                return 0.50

    # 4. Highway / route tag overlap
    doc_tags_lower = {t.lower() for t in doc.tags}
    query_tags = set(_normalise(t) for t in (parsed_query.expanded_terms or []))
    if doc_tags_lower & query_tags:
        return 0.60

    return 0.10
