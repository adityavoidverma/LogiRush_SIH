# src/ir/rag.py
"""
Retrieval-Augmented Generation layer.

Grounds the LLM answer in the evidence retrieved by the IR engine.
Falls back gracefully when no LLM key is configured:
  - Still returns the evidence bundle and route recommendation.
  - Notes that grounded generation is unavailable.

The LLM prompt enforces:
  - Only use supplied evidence for factual claims.
  - Do not invent road closures, weather conditions, or statistics.
  - Cite the document IDs used.
  - If evidence is insufficient, say so explicitly.
"""

from __future__ import annotations

import logging
import os

from src.ir.schemas import EvidenceBundle

logger = logging.getLogger("ir.rag")

# ── Supported providers ────────────────────────────────────────────────
# The system tries OpenAI first, then a simple HTTP fallback.
# If neither is available, we return a structured non-LLM response.

_PROMPT_TEMPLATE = """\
You are LogiRush, a logistics risk advisor for India.
Answer the question below using ONLY the evidence provided.
Do not invent road closures, weather conditions, incidents, or statistics.
If the evidence is insufficient for a confident answer, say so explicitly.
Cite evidence by document ID (e.g. [DOC_F001]).

## Query
{query}

## Parsed Intent
- Origin: {origin}
- Destination: {destination}
- Cargo: {cargo}
- Urgency: {urgency}

## Retrieved Evidence
{evidence_text}

## Instructions
1. State the overall risk level: CRITICAL / HIGH / MEDIUM / LOW.
2. State your recommended action (transport now / delay / use alternative route).
3. Explain why, citing the evidence document IDs.
4. If an alternative route is implied by the evidence, mention it.
5. State what evidence was NOT available (if any).
6. Keep the response concise — 150-200 words maximum.
"""


def _format_evidence(bundle: EvidenceBundle, top_n: int = 5) -> str:
    lines = []
    for r in bundle.results[:top_n]:
        doc = r.document
        lines.append(
            f"[{doc.id}] {doc.title}\n"
            f"  Source: {doc.source} ({doc.provenance})\n"
            f"  Date: {doc.date}  Location: {doc.location}\n"
            f"  Hazard: {doc.hazard}  Severity: {doc.severity}\n"
            f"  Text: {doc.text[:300]}\n"
        )
    return "\n".join(lines) if lines else "No relevant evidence found."


def _call_openai(prompt: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai  # type: ignore
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("OpenAI call failed: %s", e)
        return None


def generate_answer(bundle: EvidenceBundle) -> dict:
    """
    Generate a grounded answer from the evidence bundle.

    Returns
    -------
    dict with keys:
      - answer        : str (LLM answer or structured fallback)
      - grounded      : bool (True if LLM was used)
      - evidence_used : list of doc IDs used
      - risk_level    : "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    """
    parsed = bundle.parsed
    evidence_text = _format_evidence(bundle)

    prompt = _PROMPT_TEMPLATE.format(
        query=bundle.query,
        origin=parsed.get("origin", "not specified"),
        destination=parsed.get("destination", "not specified"),
        cargo=parsed.get("cargo", "general"),
        urgency=parsed.get("urgency", "normal"),
        evidence_text=evidence_text,
    )

    evidence_ids = [r.document.id for r in bundle.results[:5]]

    # Try LLM
    llm_answer = _call_openai(prompt)
    if llm_answer:
        risk_level = _infer_risk(llm_answer, bundle)
        return {
            "answer":        llm_answer,
            "grounded":      True,
            "evidence_used": evidence_ids,
            "risk_level":    risk_level,
        }

    # Structured fallback (no LLM available)
    risk_level = _infer_risk_from_evidence(bundle)
    answer = _structured_fallback(bundle, risk_level)
    return {
        "answer":        answer,
        "grounded":      False,
        "evidence_used": evidence_ids,
        "risk_level":    risk_level,
        "note":          "Grounded LLM generation is unavailable (no OPENAI_API_KEY). "
                         "This answer is generated from retrieved evidence.",
    }


def _infer_risk(llm_text: str, bundle: EvidenceBundle) -> str:
    t = llm_text.upper()
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if level in t:
            return level
    return _infer_risk_from_evidence(bundle)


def _infer_risk_from_evidence(bundle: EvidenceBundle) -> str:
    """Derive a risk level from top evidence severity without an LLM."""
    if not bundle.results:
        return "UNKNOWN"
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    top_sev = max(
        (severity_order.get(r.document.severity.lower(), 0) for r in bundle.results[:3]),
        default=0,
    )
    return {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW"}.get(top_sev, "UNKNOWN")


def _structured_fallback(bundle: EvidenceBundle, risk_level: str) -> str:
    """
    Build a structured answer from retrieved evidence when no LLM is available.
    """
    parsed = bundle.parsed
    origin = parsed.get("origin", "origin")
    destination = parsed.get("destination", "destination")
    cargo = parsed.get("cargo", "general cargo")

    if not bundle.results:
        return (
            f"Insufficient verified evidence was found for this query. "
            f"No disruption data could be retrieved for the {origin} → {destination} corridor."
        )

    top = bundle.results[0]
    doc = top.document
    citations = ", ".join(f"[{r.document.id}]" for r in bundle.results[:3])

    action_map = {
        "CRITICAL": "Do NOT transport via this corridor. Seek air or rail alternatives immediately.",
        "HIGH":     "Delay the shipment or use an alternative corridor.",
        "MEDIUM":   "Proceed with caution. Allow extra time and monitor conditions.",
        "LOW":      "Conditions are acceptable. Standard precautions apply.",
        "UNKNOWN":  "Insufficient data. Verify conditions before departure.",
    }

    return (
        f"Route Risk: {risk_level}\n\n"
        f"Recommended Action:\n{action_map.get(risk_level, 'Verify conditions.')}\n\n"
        f"Why:\n"
        f"Top evidence: [{doc.id}] {doc.title} (Source: {doc.source}, {doc.date})\n"
        f"Hazard: {doc.hazard.upper()} — Severity: {doc.severity.upper()}\n"
        f"{doc.text[:200]}\n\n"
        f"Evidence cited: {citations}\n\n"
        f"Limitation: This answer is based on retrieved documents. "
        f"No live closure data has been independently verified."
    )
