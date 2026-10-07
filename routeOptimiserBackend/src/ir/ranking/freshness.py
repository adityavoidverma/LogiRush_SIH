# src/ir/ranking/freshness.py
"""Freshness scoring based on document age."""

from __future__ import annotations

import datetime

from src.ir.config import FRESHNESS_SCHEDULE


def freshness_score(date_str: str, reference_date: datetime.date | None = None) -> float:
    """
    Return a freshness score in [0, 1] for a document dated date_str.

    Parameters
    ----------
    date_str : ISO-8601 date string, e.g. "2026-09-05"
    reference_date : date to measure age against (defaults to today)
    """
    if reference_date is None:
        reference_date = datetime.date.today()

    try:
        doc_date = datetime.date.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return 0.05  # unparseable date → treat as old

    age_days = (reference_date - doc_date).days
    if age_days < 0:
        age_days = 0  # future-dated documents score as fresh

    for threshold, score in FRESHNESS_SCHEDULE:
        if age_days <= threshold:
            return score

    return FRESHNESS_SCHEDULE[-1][1]
