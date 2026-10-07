# src/ir/ranking/authority.py
"""Source authority scoring — transparent lookup, no invented numbers."""

from src.ir.config import SOURCE_AUTHORITY


def authority_score(source_type: str) -> float:
    """
    Return an authority score in [0, 1] for a given source_type string.
    Unrecognised types return the lowest defined score.
    """
    key = (source_type or "unverified").lower().replace("-", "_").replace(" ", "_")
    return SOURCE_AUTHORITY.get(key, SOURCE_AUTHORITY["unverified"])
