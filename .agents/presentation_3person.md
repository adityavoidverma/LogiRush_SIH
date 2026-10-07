# LogiRush — 3-Person Presentation Script
**Track: Retrieval-Augmented Generation & Trustworthy Answers**

---

```
PERSON A  →  IR Theory & Evaluation  (the "why it works" person)
PERSON B  →  Code Walkthrough        (the "how it's built" person)
PERSON C  →  Full Platform & Novelty (the "what else it does" person)
```

Suggested total time: **8–10 minutes**
- Person C opens (1.5 min) — sets the problem, motivates why IR is needed
- Person A presents (3 min) — IR pipeline, evaluation, metrics
- Person B presents (3 min) — live code, intermediate output, show the internals
- Person C closes (1.5 min) — the wider platform, novelty, future work

---

---

# PERSON C — Opening: The Problem & Platform (1.5 min)

> *You open. Set the stage. Make the professor care before the IR details land.*

---

**Say:**

"Northeast India — 8 states, Himalayan terrain, rivers that double in size overnight
during monsoon. The roads that connect these states close without warning.
A flood on NH27. A landslide near Sikkim. A cyclone approaching Odisha.

The people who need to move medicine, food, and relief supplies have no
single system that tells them: is this route safe *today*, and *why*?

LogiRush is that system. It has three layers:

A **field reporting app** — anyone on the ground can file an incident with GPS coordinates.

A **control-room console** — controllers review, verify, and close corridors.
A dual-countersign mechanism means no single person can close a highway alone.

And the layer we're presenting today — the **Intelligence Search engine** — which
takes every hazard document, every field report, every IMD bulletin, and makes them
*searchable and queryable* through a RAG pipeline that grounds every answer in evidence."

*[hand off to Person A]*

---

---

# PERSON A — IR Pipeline & Evaluation (3 min)

> *You explain the theory. Use precise terminology. This is the IR professor's territory —
> show you understand what you built, not just that you built it.*

---

## 1 — The corpus (30 sec)

"Our retrieval corpus has **1,023 documents** — hazard incident reports, IMD alerts,
infrastructure advisories, and seasonal risk profiles across all 36 Indian states and UTs.
Documents carry metadata: source, date, location, severity, highway, state.

The corpus is synthetic — generated from real Indian geography and hazard patterns.
We are honest about that. LIVE incidents from our database are merged in at query time,
so any field report that has been filed appears immediately in retrieval."

---

## 2 — The index and retrieval methods (45 sec)

"We build a **positional inverted index** at startup.
For every token we store a posting list: the set of documents containing it,
and the position of every occurrence. This supports BM25, TF-IDF,
phrase search, and proximity search from the same data structure.

We have four retrieval methods:

- **TF-IDF** — our baseline. Term frequency times inverse document frequency.
  No length normalisation.

- **BM25** with k₁ = 1.5 and b = 0.75. Adds Okapi length normalisation on top of TF-IDF.
  Term frequency saturates — the 50th occurrence of 'flood' contributes almost nothing
  over the 10th. That is the right behaviour for long field reports.

- **Dense retrieval** — we encode every document with `all-MiniLM-L6-v2`,
  a 384-dimension sentence embedding model. At query time we embed the query
  and retrieve by cosine similarity. This catches semantic synonyms —
  'cold chain logistics' retrieves medicine transport documents even without
  the word 'medicine'.

- **Hybrid fusion** — score = 0.45 × max(BM25, TF-IDF) + 0.35 × semantic
  + 0.10 × freshness + 0.10 × authority.
  Freshness is a step-function decay — a document from today scores 1.0,
  from last month scores 0.15.
  Authority is sourced from the document's `source_type` field —
  government sources score 1.0, unverified field reports score 0.30."

---

## 3 — Query expansion (20 sec)

"Before retrieval, queries go through a **query expander**.
The term 'flood' expands to: flooding, inundation, waterlogging, river overflow, flash flood.
The term 'medicine' expands to: medical supplies, pharmaceutical, cold chain.
This improves recall without hurting precision because we expand the query,
not the index — the original query terms still dominate scoring."

---

## 4 — Evaluation results (45 sec)

"We evaluated on 25 queries with hand-curated relevance judgements.
Metrics at top-5:

| Method   | P@5   | R@5   | MRR   |
|----------|-------|-------|-------|
| TF-IDF   | 0.296 | 0.611 | 0.800 |
| BM25     | 0.312 | 0.653 | 0.805 |
| Dense    | 0.248 | 0.516 | 0.673 |
| Hybrid   | 0.272 | 0.591 | 0.772 |

BM25 leads on precision. That is expected — our judgement set is precision-heavy,
built around queries with exact highway names and city names that BM25 handles well.

Dense retrieval scores lower here, but it is not weaker — it wins on semantic queries
where the exact term is absent. The judgement set does not fully capture that.

MRR of 0.805 for BM25 means the first relevant document is at rank 1 or 2
for most queries. For a logistics operator, rank 1 is what matters."

---

## 5 — Honest limitation (20 sec)

"Two honest gaps.

First: our relevance judgements cover the 23 seed documents. The 1,000 generated
documents are not yet judged — so recall is underestimated.

Second: the corpus is synthetic. We do not scrape live IMD or NDMA feeds.
A cyclone that made landfall this morning is not in the seed corpus.
Live field incidents do flow in, but the base corpus has a freshness ceiling."

*[hand off to Person B]*

---

---

# PERSON B — Code Walkthrough (3 min)

> *You show the actual internals. Open the files, show intermediate output live.
> An IR professor will respect seeing the postings, the weights, the score breakdown —
> not just the final screen.*

---

## 1 — Open config.py (30 sec)

Open: `routeOptimiserBackend/src/ir/config.py`

"Everything tunable is in one file. No magic numbers in retriever code.

```python
BM25_K1 = 1.5   # term-frequency saturation
BM25_B  = 0.75  # document-length normalisation

HYBRID_WEIGHTS = {
    "bm25":      0.45,
    "semantic":  0.35,
    "freshness": 0.10,
    "authority": 0.10,
}

FRESHNESS_SCHEDULE = [
    (0,   1.00),  # today
    (1,   0.90),  # yesterday
    (7,   0.55),  # last week
    (30,  0.15),  # last month
    (999, 0.05),  # older
]
```

You change this file, you retune the entire engine. No code changes anywhere else."

---

## 2 — Show the inverted index (30 sec)

Open: `routeOptimiserBackend/src/ir/indexing/inverted_index.py`

"This is a classic positional inverted index.
Three data structures:

```python
self._postings:   token → set of doc_ids          # Boolean retrieval
self._positions:  token → {doc_id: [pos0, pos1]}  # phrase + proximity
self._tf:         (token, doc_id) → raw count      # BM25 / TF-IDF
```

Phrase search walks the position lists for each token in the phrase
and checks for consecutive positions. O(n·k) where n is candidate docs
and k is phrase length.

Proximity search finds the minimum distance between two terms'
position lists per document. Same data structure, same index build."

---

## 3 — Show a phrase search live (30 sec)

On the app, open **Phrase Search** tab. Type:
```
NH27 flooding
```

"The result shows document ID, match count, and a snippet with the matched
tokens highlighted. What it is actually doing: tokenizing 'nh27 flooding'
to ['nh27', 'flooding'], finding their position lists, then checking for
consecutive offsets in the same document. If 'nh27' appears at position 14
and 'flooding' at position 15 in DOC_F001 — that is a phrase match."

---

## 4 — Show the hybrid scorer (30 sec)

Open: `routeOptimiserBackend/src/ir/retrieval/hybrid.py`

"The fusion happens here. For every candidate document:

```python
lexical  = max(bm25_score, tfidf_score)
raw      = (w_bm25 * lexical
          + w_sem  * semantic_score
          + w_fresh * freshness_score(doc.date)
          + w_auth  * authority_score(doc.source_type))
final    = raw * (0.5 + 0.5 * geographic_score)
```

Geographic relevance is a *post-fusion multiplier*, not a fused weight.
It can halve a score if the document is geographically irrelevant,
but cannot push it above the fusion score. Clean separation."

---

## 5 — Show the Why panel live (30 sec)

Run query: `flood risk in Assam NH27` — method: Hybrid.
Click **"Why ranked #1? ↗"** on the top result.

"The panel shows every signal that contributed:
BM25 relevance, TF-IDF, semantic similarity, freshness, geographic, authority —
and which ones actually drove the final score given the chosen method.

For hybrid: all bars are bright.
Switch to BM25-only: BM25 bar bright, everything else dimmed.

This is the trustworthiness requirement of the RAG track —
the operator sees not just what the system said, but *exactly why*."

---

## 6 — Show the RAG layer (30 sec)

Open: `routeOptimiserBackend/src/ir/rag.py` (briefly)

"The RAG pipeline takes the top-K retrieved documents, injects them
as context into a prompt, and calls Groq's API.

If Groq is unavailable: structured fallback. The system assembles an answer
directly from the retrieved document texts — no LLM, no hallucination,
still citable. Trustworthy means it fails safely, not silently."

*[hand off to Person C]*

---

---

# PERSON C — Closing: Full Platform & Novelty (1.5 min)

> *You close. Show the wider system. The IR module sits inside something much bigger —
> make the professor see the full picture.*

---

## 1 — The Accessibility Map (30 sec)

Open the **Accessibility Map** page in the app.

"Every road corridor in NER has a live accessibility score —
a deterministic, auditable formula:

```
score = 100 − (0.25·weather + 0.30·landslide + 0.20·flood
              + 0.15·incident + 0.10·delay)
```

This feeds from Open-Meteo live rainfall, our ML disaster prediction model,
and any verified incidents on that corridor.

The map is not decorative. The route planner queries these scores for every
segment in the path. A corridor scoring below 40 can be excluded from routing
entirely. The logistics operator sees it on the map and knows why."

---

## 2 — Disaster prediction (20 sec)

"We have a Random Forest model trained on NER corridor features —
elevation, terrain class, historical event rates, rainfall thresholds.
It predicts disruption probability per corridor.

It is the *only* ML model in the system. Everything else — routing, scoring,
ranking — is deterministic and auditable. That is a deliberate design choice:
a logistics controller needs to explain every decision. A black box is not acceptable."

---

## 3 — Incident lifecycle & dual countersign (20 sec)

"Anyone can file an incident — anonymously, with GPS, from the field app.
It enters a review queue. A verifier examines it. To *close* a corridor —
that is, to block routing through it — two independent verifiers must
countersign, each within their assigned jurisdiction.

Single accounts cannot act alone. That is the safety design.
And every decision is appended to an immutable audit trail — never overwritten."

---

## 4 — The novelty claim (20 sec)

"Most logistics platforms give you a route. We give you a *grounded reason*
for that route — evidence cited, scores shown, every assumption auditable.

The IR module is not a search bar bolted onto a maps app.
It is the intelligence layer that turns unstructured hazard text into
structured, citable answers — answers that a logistics controller
can act on and defend.

That is the novelty."

---

---

# Quick Reference Card — numbers to have ready

| Fact | Value |
|------|-------|
| Corpus | 1,023 documents |
| BM25 k₁ / b | 1.5 / 0.75 |
| Hybrid weights | 0.45 BM25 · 0.35 semantic · 0.10 freshness · 0.10 authority |
| Embedding model | all-MiniLM-L6-v2, 384 dimensions |
| RAG LLM | Groq qwen3.8-27b → OpenAI gpt-4o-mini → structured fallback |
| Evaluation | 25 queries, P@5 BM25=0.312, MRR BM25=0.805 |
| Accessibility formula | 100 − (0.25·weather + 0.30·landslide + 0.20·flood + 0.15·incident + 0.10·delay) |
| Test count | 174 test functions, 206 pass |
| Dual countersign | two independent verifiers required to close a corridor |
| Field app | Expo React Native, offline queue, idempotent sync via UUID |

---

# Demo page order

| Time | Person | Page / File |
|------|--------|-------------|
| 0:00 | C | App home / overview |
| 1:30 | A | `/search` — run query, show results, evaluation table on page |
| 2:15 | B | VSCode: `config.py` → `inverted_index.py` → `hybrid.py` |
| 3:30 | B | App: Phrase Search tab, Proximity Search tab, Why panel |
| 5:30 | C | Accessibility Map page |
| 6:30 | C | Incidents page (show review queue, audit trail) |
| 7:30 | C | Shipment Planner (show route with risk score) |
| 8:30 | All | Questions |
