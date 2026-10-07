# src/ir/rag.py
"""
Retrieval-Augmented Generation layer.

Provider priority (first one with a configured key wins):
  1. Groq  — free tier, fast, llama-3.3-70b-versatile
  2. OpenAI — gpt-4o-mini (if OPENAI_API_KEY set)
  3. Structured fallback — no LLM, built from retrieved evidence

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

_PROMPT_TEMPLATE = """\
You are LogiRush, a logistics risk advisor for India.

STRICT RULES — follow exactly:
1. Answer ONLY from the evidence documents listed below. Do not infer, extrapolate, or guess.
2. If no document directly mentions the specific highway, location, or route asked about, say:
   "No direct evidence found for [specific query]. I cannot assess risk for this corridor."
3. Do NOT cite a document about a different highway as evidence for the queried highway.
4. Do NOT infer that nearby flooding means the queried road is also flooded unless a document says so.
5. Cite every factual claim with its document ID e.g. [DOC_F001].
6. If evidence is partial (regional, not specific), say so clearly.

## Query
{query}

## Specific subject of query
- Highway/Route: {highway}
- Origin: {origin}
- Destination: {destination}
- Cargo: {cargo}

## Retrieved Evidence (use ONLY these)
{evidence_text}

## Required output format
**Overall Risk Level:** CRITICAL / HIGH / MEDIUM / LOW / INSUFFICIENT DATA

**Recommended Action:** (one sentence — only if evidence directly supports it)

**Explanation:** (cite specific doc IDs; if no direct evidence say so explicitly)

**Missing Evidence:** (what specific data was not available)

Keep under 200 words. If no document directly covers the queried subject, lead with that.
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
            f"  Relevance score: {r.final_score:.2f}\n"
            f"  Text: {doc.text[:300]}\n"
        )
    if not lines:
        return "NO EVIDENCE FOUND — corpus contains no documents matching this query."
    return "\n".join(lines)


def _extract_highway(query: str) -> str:
    """Pull any NH/SH reference out of the raw query."""
    import re
    m = re.findall(r'\bNH\s*\d+\w*|\bSH\s*\d+\w*|\bNH\w+', query, re.IGNORECASE)
    return ", ".join(m) if m else "not specified"


# ── Provider 1: Groq (free tier) ──────────────────────────────────────
# Model preference order — tries each until one succeeds.
_GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

def _call_groq(prompt: str) -> str | None:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from groq import Groq  # type: ignore
        client = Groq(api_key=api_key)
        for model in _GROQ_MODELS:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.2,
                )
                answer = resp.choices[0].message.content.strip()
                logger.info("Groq LLM answered via %s (%d chars)", model, len(answer))
                return answer
            except Exception as model_err:
                logger.warning("Groq model %s failed: %s — trying next", model, model_err)
        return None
    except Exception as e:
        logger.warning("Groq call failed: %s", e)
        return None


# ── Provider 2: OpenAI ────────────────────────────────────────────────
def _call_openai(prompt: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
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
        answer = resp.choices[0].message.content.strip()
        logger.info("OpenAI LLM answered (%d chars)", len(answer))
        return answer
    except Exception as e:
        logger.warning("OpenAI call failed: %s", e)
        return None


def _call_llm(prompt: str) -> tuple[str | None, str]:
    """
    Try LLM providers in order of preference.

    Returns
    -------
    (answer_text_or_None, provider_name)
    """
    answer = _call_groq(prompt)
    if answer:
        # figure out which model actually answered (logged above)
        return answer, "groq"

    answer = _call_openai(prompt)
    if answer:
        return answer, "openai/gpt-4o-mini"

    return None, "none"


# ── Public entry point ────────────────────────────────────────────────
def generate_answer(bundle: EvidenceBundle) -> dict:
    """
    Generate a grounded answer from the evidence bundle.

    Returns
    -------
    dict with keys:
      - answer        : str
      - grounded      : bool (True if an LLM was used)
      - provider      : str  (which LLM was used, or "none")
      - evidence_used : list[str]
      - risk_level    : "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN"
    """
    parsed = bundle.parsed
    evidence_text = _format_evidence(bundle)

    prompt = _PROMPT_TEMPLATE.format(
        query=bundle.query,
        highway=_extract_highway(bundle.query),
        origin=parsed.get("origin", "not specified"),
        destination=parsed.get("destination", "not specified"),
        cargo=parsed.get("cargo", "general"),
        urgency=parsed.get("urgency", "normal"),
        evidence_text=evidence_text,
    )

    evidence_ids = [r.document.id for r in bundle.results[:5]]

    llm_answer, provider = _call_llm(prompt)

    if llm_answer:
        return {
            "answer":        llm_answer,
            "grounded":      True,
            "provider":      provider if provider != "none" else "groq",
            "evidence_used": evidence_ids,
            "risk_level":    _infer_risk(llm_answer, bundle),
        }

    # Structured fallback
    risk_level = _infer_risk_from_evidence(bundle)
    return {
        "answer":        _structured_fallback(bundle, risk_level),
        "grounded":      False,
        "provider":      "none",
        "evidence_used": evidence_ids,
        "risk_level":    risk_level,
        "note": (
            "LLM generation unavailable — set GROQ_API_KEY (free at console.groq.com) "
            "or OPENAI_API_KEY to enable grounded answers."
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────
def _infer_risk(llm_text: str, bundle: EvidenceBundle) -> str:
    t = llm_text.upper()
    for level in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if level in t:
            return level
    return _infer_risk_from_evidence(bundle)


def _infer_risk_from_evidence(bundle: EvidenceBundle) -> str:
    if not bundle.results:
        return "UNKNOWN"
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    top_sev = max(
        (severity_order.get(r.document.severity.lower(), 0) for r in bundle.results[:3]),
        default=0,
    )
    return {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW"}.get(top_sev, "UNKNOWN")


def _structured_fallback(bundle: EvidenceBundle, risk_level: str) -> str:
    parsed = bundle.parsed
    origin      = parsed.get("origin", "origin")
    destination = parsed.get("destination", "destination")

    if not bundle.results:
        return (
            f"Insufficient verified evidence was found for this query. "
            f"No disruption data could be retrieved for the {origin} → {destination} corridor."
        )

    top  = bundle.results[0]
    doc  = top.document
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
