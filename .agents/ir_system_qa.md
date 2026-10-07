# LogiRush IR System — Technical Q&A

*Answers verified directly from source code, test files, and git history.*  
*Last updated: 2026-10-07*

---

## Q1 — How many documents are in the corpus, and roughly how many per category?

**Total: 1,023 documents** at index time (plus any LIVE incidents injected at runtime).

| Category | Count | % |
|---|---|---|
| Flood | 300 | 29.3% |
| Landslide | 250 | 24.4% |
| Heavy Rainfall | 150 | 14.7% |
| Cyclone | 100 | 9.8% |
| Road Accident | 100 | 9.8% |
| Infrastructure | 80 | 7.8% |
| Heat / Weather | 20 | 2.0% |
| **Static seed docs** | 23 | 2.2% |
| **Total** | **1,023** | |

The 1,000 generated documents span **36 Indian states and UTs**. NER states (Assam, Meghalaya, Manipur, Nagaland, Mizoram, Tripura, Arunachal Pradesh, Sikkim) are weighted at **2× the rate** of other states. Severity distribution is: low 20%, medium 40%, high 30%, critical 10%.

There are no distinct "cargo" or "corridor/highway" buckets in the generator — every document carries a `highway` tag (drawn from the state's highway list) and a `route` field, but the primary axes are hazard type, state, and severity. The 23 seed documents add dedicated corridor profiles (DOC_P001–P003), background/SAMPLED advisories (DOC_B001–B004), and a handful of specific accident and infrastructure reports.

---

## Q2 — What are your BM25 parameters, k1 and b?

Defined in `src/ir/config.py`:

```
BM25_K1 = 1.5    # term-frequency saturation
BM25_B  = 0.75   # document-length normalisation
```

These are the standard Okapi BM25 defaults. `k1 = 1.5` means TF contribution saturates moderately fast; `b = 0.75` applies a 75% length normalisation. The values are read from config into `BM25Retriever.__init__` and can be tuned without touching the retriever code.

---

## Q3 — What are your fusion weights w1 to w4 (BM25, dense, freshness, authority)?

Defined in `src/ir/config.py` under `HYBRID_WEIGHTS`:

| Signal | Weight | Variable name |
|---|---|---|
| BM25 / lexical (max of BM25, TF-IDF) | **0.45** | `bm25` |
| Dense / semantic | **0.35** | `semantic` |
| Freshness | **0.10** | `freshness` |
| Authority | **0.10** | `authority` |
| **Total** | **1.00** | |

The fusion formula in `hybrid.py` is:

```python
lexical = max(bm25_s, tfidf_s)   # TF-IDF merged into lexical channel
hybrid  = 0.45 * lexical + 0.35 * semantic + 0.10 * freshness + 0.10 * authority
```

A **geographic boost** is applied *after* fusion as a multiplicative factor:
```python
final = hybrid * (0.5 + 0.5 * geographic_score)
```
Geographic relevance can therefore cut a score by up to 50% (score → 0.5 × hybrid) but cannot push it above the hybrid score. Cargo-type multipliers (`CARGO_RETRIEVAL_BOOSTS`) additionally scale freshness (up to 1.5×) and geographic (up to 1.3×) before the fusion step.

---

## Q4 — Which sentence-embedding model do you use for dense retrieval?

**`all-MiniLM-L6-v2`** from the `sentence-transformers` library.

Set in `src/ir/config.py`:
```python
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384
```

Embeddings are generated at startup, stored as a NumPy array (shape `[N, 384]`), and searched by dot-product (equivalent to cosine similarity because embeddings are L2-normalised). No external vector database is used. If `sentence-transformers` is not installed the dense retriever returns empty results gracefully and the system falls back to BM25 + TF-IDF only.

---

## Q5 — Which LLM or API generates the RAG answers?

The RAG layer (`src/ir/rag.py`) tries providers in this priority order:

1. **Groq** (free tier) — model preference list:
   - `qwen/qwen3.8-27b`
   - `openai/gpt-oss-20b`
   - `openai/gpt-oss-120b`
   - Requires `GROQ_API_KEY` environment variable.

2. **OpenAI** — `gpt-4o-mini`
   - Requires `OPENAI_API_KEY` environment variable.

3. **Structured fallback** — no LLM; a deterministic text block is assembled from the top retrieved documents.

The fallback is honest: it surfaces the top evidence with citations but flags that LLM generation is unavailable. The system is designed to function fully without any API key.

---

## Q6 — How many of the 165+ automated tests cover the IR module?

The test suite has **174 test functions** across 15 test files (all in `routeOptimiserBackend/tests/`).

There are **no dedicated IR test files** (`test_ir_*.py` does not exist). IR coverage comes from **21 test functions** scattered across existing test files that touch IR-adjacent topics (search endpoints, places search, analytics, incident impact). The IR engine itself — BM25, TF-IDF, dense retrieval, hybrid fusion, evaluation metrics, corpus generation — has no standalone unit tests at this time.

The 206-test total cited in the workflow notification includes fixtures and parametrised variants; the raw `def test_*` count is 174.

---

## Q7 — What is the GitHub repo link?

**[https://github.com/adityavoidverma/LogiRush_SIH](https://github.com/adityavoidverma/LogiRush_SIH)**

---

## Q8 — Which parts were built during the 36-hour hackathon window, and which came earlier from Smart India Hackathon?

This question cannot be answered from the codebase alone — git commit timestamps and branch history would tell the story precisely.  
**You (the team) need to fill this in.**

Suggested approach:
```bash
git log --oneline --since="<hackathon-start-ISO-date>" --until="<hackathon-end-ISO-date>"
```

From code structure inference:
- The **routing engine, NER graph, and logistics core** (`src/services/`, `src/db/`) look like the SIH foundation.
- The **IR / search module** (`src/ir/`) appears to be a later addition given its self-contained structure, evaluation dataset, and corpus machinery.
- The **corpus expansion to 1,000 documents** was done on 2026-10-07 (today, during this session).

---

## Q9 — Besides Claude, which other AI tools did you use (Copilot, Cursor, ChatGPT, etc.)?

Cannot be determined from the codebase. **Team to fill in.**

---

## Q10 — What pool size did you judge (top-10, top-20 per system)?

The evaluation in `src/ir/evaluation/metrics.py` calls `retrieve_by_method` with `top_k = top_k * 2` (i.e. fetches double the requested K to build the candidate pool), then computes metrics at `top_k = 5` by default.

The **judged pool** is based on the `relevant_documents` sets in `src/ir/evaluation/dataset.py` — these were hand-curated against the original 23 seed documents. No formal pooling methodology (TREC-style round-robin) was used; the sets are editorial judgements.

**Bottom line:** K = 5 for P@K, Recall@K, F1@K; no explicit top-20 pool.

---

## Q11 — For Q1 to Q6 (first 6 queries), how many documents are relevant in total ("#rel.")?

From `src/ir/evaluation/dataset.py`:

| Query ID | Query text | # Relevant docs |
|---|---|---|
| Q01 | flood risk in Assam | 5 |
| Q02 | landslide risk near Sikkim highways | 3 |
| Q03 | cyclone impact on Odisha logistics | 2 |
| Q04 | heavy rainfall affecting Kerala roads | 2 |
| Q05 | heat risk for Rajasthan transport | 1 |
| Q06 | Meghalaya extreme rainfall alert | 2 |

**Total relevant across Q01–Q06: 15 documents** (with overlaps — same doc ID can appear in multiple queries).

---

## Q12 — For each query and system, how many of the top-5 results were relevant?

**These numbers cannot be read from source code — they require running the IR engine live against the expanded corpus.**

The `evaluate` endpoint (`GET /api/ir/evaluate?method=<method>&top_k=5`) will compute this at runtime. The evaluation dataset was written against the original 23 seed documents; with the corpus now at 1,023 the retrieval pool has changed, so new numbers must be measured.

**To get real numbers, run:**
```bash
cd routeOptimiserBackend
python -c "
from src.ir.engine import ir_engine
import json
for method in ['tfidf', 'bm25', 'dense', 'hybrid']:
    r = ir_engine.evaluate(method=method, top_k=5)
    print(json.dumps({'method': method, 'p@5': r['mean_p_at_k'], 'r@5': r['mean_recall_at_k'], 'mrr': r['mrr']}, indent=2))
"
```

---

## Q13 — What is the rank of the first relevant result per query and system? (MRR)

Same answer as Q12 — requires a live run. The MRR is computed by `reciprocal_rank()` in `metrics.py` and surfaced in the `evaluate_retriever` return dict under `"mrr"`.

---

## Q14 — R@10: how many relevant documents in top-10 per query and system?

The evaluation module supports arbitrary K. Run:
```bash
python -c "
from src.ir.engine import ir_engine
import json
for method in ['tfidf', 'bm25', 'dense', 'hybrid']:
    r = ir_engine.evaluate(method=method, top_k=10)
    print(f'{method}: recall@10={r[\"mean_recall_at_k\"]}')
"
```

---

## Q15 — Did any result contradict expectations?

Cannot answer without running evaluations. See Q12 note. Known architectural fact that might produce surprises:

- **TF-IDF and BM25 share the same lexical channel** in hybrid mode — the hybrid formula takes `max(bm25_s, tfidf_s)` as the lexical component, not a blend. In single-method mode they are independent. This means BM25 will almost always beat TF-IDF on the same query in single-method evaluation because BM25 adds IDF and length normalisation on top of TF-IDF's term weighting.
- **Dense retrieval** may underperform on specific highway queries (e.g. "NH10 Sikkim road blocked") because `all-MiniLM-L6-v2` sees highway numbers as near-arbitrary tokens with little semantic neighbourhood.

---

## Q16 — Are phrase/proximity search, query expansion, freshness decay, and authority scoring all implemented?

| Feature | Implemented? | Location |
|---|---|---|
| Phrase search | ✅ Yes | `src/ir/indexing/inverted_index.py` → `phrase_search()`, API at `GET /api/ir/phrase` |
| Proximity search | ✅ Yes | `src/ir/indexing/inverted_index.py` → `proximity_search()`, API at `GET /api/ir/proximity` |
| Query expansion | ✅ Yes | `src/ir/query/expansion.py` → `expand_query()` using `HAZARD_SYNONYMS` from config |
| Freshness decay | ✅ Yes | `src/ir/ranking/freshness.py` → step-function decay schedule in `config.py` (`FRESHNESS_SCHEDULE`) |
| Authority scoring | ✅ Yes | `src/ir/ranking/authority.py` → lookup against `SOURCE_AUTHORITY` dict in config |

All five features are fully implemented and active in the current codebase. None need to be moved to future work.

---

## Q17 — Are the Q1–Q6 queries final?

The full evaluation set has **25 queries (Q01–Q25)**, not just 6.  
The first 6 are:

| ID | Query |
|---|---|
| Q01 | flood risk in Assam |
| Q02 | landslide risk near Sikkim highways |
| Q03 | cyclone impact on Odisha logistics |
| Q04 | heavy rainfall affecting Kerala roads |
| Q05 | heat risk for Rajasthan transport |
| Q06 | Meghalaya extreme rainfall alert |

These are defined in `src/ir/evaluation/dataset.py` and have not been changed since they were written. They are the **canonical queries** for evaluation purposes.

**Note:** The relevance judgements were written against the original 23 seed documents. With the corpus expanded to 1,023 documents, some generated documents will also be genuinely relevant to these queries (e.g. GEN_F-series docs for flood queries) but are not yet listed in `relevant_documents`. If you want precise P@K/R@K numbers for a paper or presentation, the judgement sets should be extended to cover the generated corpus — or restrict evaluation to the 23 seed document IDs only (by filtering retrieved results before scoring).
