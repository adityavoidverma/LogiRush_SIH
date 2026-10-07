# src/ir/config.py
"""
Central configuration for the LogiRush IR Engine.

All magic numbers live here. Change this file to tune retrieval behaviour —
do not scatter weights or thresholds across retriever modules.
"""

from __future__ import annotations

# ─────────────────────────────────────────────
# Retrieval
# ─────────────────────────────────────────────
TOP_K_DEFAULT = 10

# BM25 hyper-parameters
BM25_K1 = 1.5   # term-frequency saturation
BM25_B  = 0.75  # document-length normalisation

# ─────────────────────────────────────────────
# Hybrid score fusion weights  (must sum to 1)
# ─────────────────────────────────────────────
HYBRID_WEIGHTS: dict[str, float] = {
    "bm25":       0.45,
    "semantic":   0.35,
    "freshness":  0.10,
    "authority":  0.10,
}

# ─────────────────────────────────────────────
# Freshness decay
# ─────────────────────────────────────────────
# Scores for documents at these age thresholds (days).
# Anything older than the last bucket scores the last value.
FRESHNESS_SCHEDULE: list[tuple[int, float]] = [
    (0,   1.00),   # today
    (1,   0.90),   # yesterday
    (3,   0.75),   # last 3 days
    (7,   0.55),   # last week
    (14,  0.35),   # last 2 weeks
    (30,  0.15),   # last month
    (999, 0.05),   # older
]

# ─────────────────────────────────────────────
# Source authority
# ─────────────────────────────────────────────
SOURCE_AUTHORITY: dict[str, float] = {
    "government":          1.00,
    "official":            1.00,
    "verified_org":        0.85,
    "trusted_dataset":     0.75,
    "verified_field":      0.65,
    "synthetic":           0.40,
    "unverified":          0.30,
}

# ─────────────────────────────────────────────
# Hazard registry  (add new hazards here only)
# ─────────────────────────────────────────────
HAZARD_SYNONYMS: dict[str, list[str]] = {
    "flood":      ["flooding", "inundation", "waterlogging", "river overflow", "flash flood"],
    "landslide":  ["slope failure", "rockfall", "debris flow", "mudslide", "land slip"],
    "cyclone":    ["storm", "tropical cyclone", "severe cyclonic storm", "hurricane", "typhoon"],
    "rainfall":   ["heavy rain", "extreme rainfall", "cloudburst", "downpour", "precipitation"],
    "heat":       ["heatwave", "extreme heat", "high temperature", "scorching"],
    "road_block": ["road closure", "road block", "highway closure", "traffic disruption"],
    "accident":   ["road accident", "vehicle collision", "crash", "pile-up"],
    "infra":      ["infrastructure damage", "bridge damage", "road damage", "pothole", "subsidence"],
}

# ─────────────────────────────────────────────
# Cargo-aware retrieval weight boosts
# ─────────────────────────────────────────────
# These multipliers modulate how much geographic and freshness signals
# matter per cargo type.  Values > 1 boost; < 1 dampen.
CARGO_RETRIEVAL_BOOSTS: dict[str, dict[str, float]] = {
    "medicine":   {"freshness": 1.4, "geographic": 1.3},
    "relief":     {"freshness": 1.4, "geographic": 1.2},
    "perishable": {"freshness": 1.5, "geographic": 1.1},
    "food":       {"freshness": 1.2, "geographic": 1.1},
    "general":    {"freshness": 1.0, "geographic": 1.0},
}

# ─────────────────────────────────────────────
# Dense retrieval
# ─────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # lightweight, fast, good quality
EMBEDDING_DIM   = 384

# ─────────────────────────────────────────────
# Stop-words (English + common logistics noise)
# ─────────────────────────────────────────────
STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "not", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall",
    "this", "that", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "she", "they", "their", "them",
    "what", "which", "who", "when", "where", "why", "how",
    "can", "today", "now", "transport", "logistics", "route", "road",
}
