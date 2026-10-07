# Requirements: Corpus Expansion & Provenance Filter Removal

**Status:** Approved  
**Created:** 2026-10-07  
**Session:** Corpus expansion feature

---

## 1. Overview

### Current State
The LogiRush IR system currently has:
- **~24 static seed documents** (SEED_DOCUMENTS in `corpus.py`)
- **Provenance labels** on every document: SYNTHETIC, SAMPLED, LIVE
- **Provenance dropdown filter** in the Corpus Browser UI allowing users to filter by provenance type
- Documents covering multiple hazards (floods, landslides, cyclones, heat, accidents) across India

### Proposed Changes
1. **Remove the provenance filter** from the Corpus Browser UI
2. **Massively expand the document corpus** to create a large, realistic dataset for the IR system

---

## 2. Goals

### Primary Goals
- [ ] **Scale the corpus** from ~24 documents to **hundreds or thousands** of documents
- [ ] **Remove provenance UI filter** - simplify the Corpus Browser interface
- [ ] Maintain **high-quality, realistic** logistics/hazard documents
- [ ] Ensure the expanded corpus is **well-distributed** across:
  - Geographic regions (all Indian states, focus on NER)
  - Hazard types (floods, landslides, cyclones, heat, accidents, infrastructure)
  - Severity levels (low, medium, high, critical)
  - Time periods (historical events, seasonal patterns, current alerts)

### Secondary Goals
- [ ] Ensure IR performance remains fast with large corpus (indexing, search, ranking)
- [ ] Maintain document quality and realistic language
- [ ] Keep provenance tracking internally (backend) for future audit/transparency needs
- [ ] Provide easy regeneration/reseeding of the corpus

---

## 3. Requirements

### 3.1 Frontend Changes

#### Remove Provenance Filter
- **Current behavior:** Corpus Browser has a dropdown with options: "All provenance", "SYNTHETIC", "SAMPLED", "LIVE"
- **New behavior:** Remove the provenance dropdown entirely from the UI
- **Keep:** Display provenance badges on individual document cards (for transparency)
- **Files affected:**
  - `routeOptimiserFrontend/src/pages/IntelligenceSearch.jsx` (CorpusBrowser component)

### 3.2 Backend Changes

#### Corpus Size
- **Target:** Generate **500-2000 documents** initially (configurable)
- **Distribution:**
  - 60% hazard/incident reports (floods, landslides, cyclones, etc.)
  - 20% infrastructure alerts (bridge closures, road work, weight restrictions)
  - 10% logistics advisories (seasonal patterns, route guidance)
  - 10% background/reference material (safety guidelines, regional profiles)

#### Document Variety
Each document should vary realistically in:
- **Length:** 50-300 words
- **Detail level:** Some terse field reports, some detailed assessments
- **Language style:** Official IMD bulletins, field reports, news-style summaries
- **Metadata richness:** Varying levels of location precision, dates, sources

#### Geographic Coverage
- **Pan-India coverage** with heavier weighting for:
  - North-East Region (NER) states: Assam, Meghalaya, Manipur, Nagaland, Mizoram, Tripura, Arunachal Pradesh, Sikkim
  - Major logistics corridors: NH27, NH44, NH37, NH31, NH10, NH58, NH66
  - High-risk zones: Himalayan foothills, coastal regions, floodplains

#### Hazard Type Distribution
| Hazard Type | Percentage | Est. Docs (out of 1000) |
|-------------|-----------|------------------------|
| Floods | 30% | 300 |
| Landslides | 25% | 250 |
| Cyclones | 10% | 100 |
| Heavy Rainfall | 15% | 150 |
| Road Accidents | 10% | 100 |
| Infrastructure Issues | 8% | 80 |
| Heat/Weather | 2% | 20 |

#### Data Generation Strategy

**Option A: Template-based generation (recommended for first pass)**
- Create document templates with randomized variations
- Use real Indian geography (cities, highways, coordinates)
- Vary severity, dates, sources, language patterns
- Fast, predictable, fully controlled

**Option B: LLM-assisted generation**
- Use AI to generate realistic incident reports
- More varied language, more realistic
- Slower, requires API calls or local model
- Risk of repetitive patterns if not carefully prompted

**Option C: Hybrid approach**
- Core corpus from templates (80%)
- LLM-generated "color" documents for variety (20%)

**Decision needed from user:** Which generation strategy?

#### Provenance Strategy
- **Remove from user-facing filters** but **keep in document metadata**
- All generated documents marked as `"SYNTHETIC"`
- LIVE incidents still injected at runtime from database
- Future: could add SAMPLED documents from real open datasets with attribution

#### Performance Considerations
- **Indexing time:** BM25, TF-IDF, sentence embedding all scale differently
  - BM25/TF-IDF: near-linear with corpus size
  - Dense embeddings: slower if generating fresh, but one-time cost
- **Search latency:** Should remain <500ms for typical queries with 1000-2000 docs
- **Memory:** Embedding model (all-MiniLM-L6-v2) + 2000 doc embeddings ≈ 100-200MB RAM
- **Storage:** Database grows with LIVE incidents; seed corpus stays in code

#### Code Changes Required
- **`src/ir/corpus.py`:**
  - Replace manual SEED_DOCUMENTS list with generator function
  - Create `generate_corpus(count=1000)` function
  - Keep existing `build_corpus()` logic for merging LIVE incidents
- **New file: `src/ir/corpus_generator.py`:**
  - Document generation logic
  - Templates, randomization, geographic data
- **`src/api/ir_routes.py`:**
  - Remove `provenance` query parameter from `/api/ir/corpus` endpoint
  - Keep provenance in document responses (for badges)

---

## 4. Out of Scope

- Fetching real-time data from external APIs (IMD, news sources) — keep everything synthetic for now
- Multi-language support (Hindi, Bengali, etc.) — English only
- Document versioning / update tracking
- User-submitted corpus expansion

---

## 5. Success Criteria

### Must Have
- [ ] Provenance dropdown removed from Corpus Browser UI
- [ ] Corpus expanded to **at least 500 documents**
- [ ] Documents are **realistic and varied** (not obviously templated)
- [ ] Search performance remains **<1 second** for typical queries
- [ ] All three retrieval methods (BM25, TF-IDF, Dense) work correctly with expanded corpus
- [ ] Geographic distribution covers **all NER states + major national corridors**

### Nice to Have
- [ ] 1000+ documents in corpus
- [ ] Temporal realism (documents span multiple seasons/years)
- [ ] Clustering/deduplication to avoid too-similar documents
- [ ] Admin endpoint to regenerate corpus on demand

---

## 6. ~~Open Questions~~ → Decisions Made ✓

1. **Target corpus size:** ✓ **1000 documents**
2. **Generation strategy:** ✓ **Hybrid** (template-based core + varied examples)
3. **Provenance badges:** ✓ **Remove completely** from UI
4. **Geographic balance:** ✓ **Balanced pan-India** distribution
5. **Temporal spread:** Recent focus (2025-2026) with some historical context
6. **LIVE incidents:** ✓ **Keep merging LIVE** — prioritize real incident integration

---

## 7. Next Steps

Once requirements are approved:
1. Create technical design document
2. Break down into implementation tasks
3. Start with backend corpus generation
4. Frontend UI cleanup (remove provenance filter)
5. Testing with large corpus
6. Performance validation
