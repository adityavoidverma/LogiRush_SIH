# Implementation Plan: Corpus Expansion & Provenance Filter Removal

## Overview
Expand the LogiRush IR corpus from 24 to 1000 documents using a deterministic generator, and remove the provenance filter UI from the frontend Corpus Browser and backend API.

## Feature Decomposition
This task decomposes into 3 independent features:
- **FEAT-001**: Create corpus generator module (backend, new file)
- **FEAT-002**: Integrate generator into corpus.py (backend, modify existing)
- **FEAT-003**: Remove provenance filter UI and API parameter (frontend + backend, modify existing)

FEAT-001 must complete before FEAT-002. FEAT-003 is independent of the other two.

See `/Users/user/Downloads/LogiRush/.agents/tasks/corpus-expansion/features/*.json` for detailed step-by-step plans.

---

## FEAT-001: Corpus Generator Module

### Files
- **Create**: `routeOptimiserBackend/src/ir/corpus_generator.py`

### Generator Design

#### Function Signature
```python
def generate_corpus(count: int = 1000, seed: int = 42) -> list[IRDocument]:
    """
    Generate synthetic logistics/hazard documents with deterministic seeded random.
    Returns exactly `count` IRDocument instances.
    """
```

#### Geographic Data Structure
```python
INDIA_GEO_DATA = {
    "Assam": {
        "cities": [
            {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
            {"name": "Tezpur", "lat": 26.6333, "lon": 92.8000},
            {"name": "Silchar", "lat": 24.8333, "lon": 92.7789},
        ],
        "highways": ["NH27", "NH715", "NH37"],
        "districts": ["Kamrup", "Sonitpur", "Cachar"],
    },
    "Meghalaya": {
        "cities": [
            {"name": "Shillong", "lat": 25.5788, "lon": 91.8933},
            {"name": "Cherrapunji", "lat": 25.2701, "lon": 91.7318},
        ],
        "highways": ["NH6", "NH44"],
        "districts": ["East Khasi Hills", "West Khasi Hills"],
    },
    "West Bengal": {
        "cities": [
            {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
            {"name": "Siliguri", "lat": 26.7271, "lon": 88.3953},
            {"name": "Durgapur", "lat": 23.5204, "lon": 87.3119},
        ],
        "highways": ["NH16", "NH12", "NH19"],
        "districts": ["Kolkata", "Darjeeling", "Bardhaman"],
    },
    "Maharashtra": {
        "cities": [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
            {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
            {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
        ],
        "highways": ["NH48", "NH52", "NH44"],
        "districts": ["Mumbai Suburban", "Pune", "Nagpur"],
    },
    "Karnataka": {
        "cities": [
            {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946},
            {"name": "Mysuru", "lat": 12.2958, "lon": 76.6394},
        ],
        "highways": ["NH275", "NH44", "NH66"],
        "districts": ["Bengaluru Urban", "Mysuru"],
    },
    "Tamil Nadu": {
        "cities": [
            {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
            {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
        ],
        "highways": ["NH16", "NH44", "NH48"],
        "districts": ["Chennai", "Coimbatore"],
    },
    "Kerala": {
        "cities": [
            {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
            {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366},
            {"name": "Ernakulam", "lat": 9.9816, "lon": 76.2999},
        ],
        "highways": ["NH66", "NH47", "NH544"],
        "districts": ["Ernakulam", "Thiruvananthapuram", "Kozhikode"],
    },
    "Odisha": {
        "cities": [
            {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
            {"name": "Cuttack", "lat": 20.5124, "lon": 85.8829},
            {"name": "Paradip", "lat": 20.3164, "lon": 86.6090},
        ],
        "highways": ["NH16", "NH203", "NH20"],
        "districts": ["Khordha", "Cuttack", "Jagatsinghpur"],
    },
    "Bihar": {
        "cities": [
            {"name": "Patna", "lat": 25.5941, "lon": 85.1376},
            {"name": "Muzaffarpur", "lat": 26.1209, "lon": 85.3647},
            {"name": "Gaya", "lat": 24.7955, "lon": 84.9994},
        ],
        "highways": ["NH31", "NH30", "NH19"],
        "districts": ["Patna", "Muzaffarpur", "Gaya"],
    },
    "Rajasthan": {
        "cities": [
            {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
            {"name": "Jaisalmer", "lat": 26.9157, "lon": 70.9083},
            {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125},
        ],
        "highways": ["NH48", "NH11", "NH8"],
        "districts": ["Jaipur", "Jaisalmer", "Udaipur"],
    },
    "Gujarat": {
        "cities": [
            {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
            {"name": "Surat", "lat": 21.1702, "lon": 72.8311},
        ],
        "highways": ["NH48", "NH8", "NH27"],
        "districts": ["Ahmedabad", "Surat"],
    },
    "Uttar Pradesh": {
        "cities": [
            {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
            {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
            {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
        ],
        "highways": ["NH27", "NH19", "NH30"],
        "districts": ["Lucknow", "Agra", "Varanasi"],
    },
    "Madhya Pradesh": {
        "cities": [
            {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
            {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
        ],
        "highways": ["NH44", "NH52", "NH47"],
        "districts": ["Bhopal", "Indore"],
    },
    "Andhra Pradesh": {
        "cities": [
            {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
            {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
        ],
        "highways": ["NH16", "NH44"],
        "districts": ["Visakhapatnam", "Krishna"],
    },
    "Sikkim": {
        "cities": [
            {"name": "Gangtok", "lat": 27.3389, "lon": 88.6065},
            {"name": "Rangpo", "lat": 27.1760, "lon": 88.5313},
        ],
        "highways": ["NH10", "NH717A"],
        "districts": ["East Sikkim", "South Sikkim"],
    },
    "Tripura": {
        "cities": [
            {"name": "Agartala", "lat": 23.8315, "lon": 91.2868},
            {"name": "Udaipur", "lat": 23.5370, "lon": 91.4849},
        ],
        "highways": ["NH44", "NH716"],
        "districts": ["West Tripura", "Gomati"],
    },
    "Manipur": {
        "cities": [
            {"name": "Imphal", "lat": 24.8170, "lon": 93.9368},
            {"name": "Senapati", "lat": 25.2741, "lon": 94.0181},
        ],
        "highways": ["NH2", "NH37"],
        "districts": ["Imphal West", "Senapati"],
    },
    "Nagaland": {
        "cities": [
            {"name": "Kohima", "lat": 25.6700, "lon": 94.1100},
            {"name": "Dimapur", "lat": 25.9067, "lon": 93.7272},
        ],
        "highways": ["NH44", "NH29"],
        "districts": ["Kohima", "Dimapur"],
    },
    "Mizoram": {
        "cities": [
            {"name": "Aizawl", "lat": 23.7271, "lon": 92.7176},
        ],
        "highways": ["NH54", "NH6"],
        "districts": ["Aizawl"],
    },
    "Arunachal Pradesh": {
        "cities": [
            {"name": "Itanagar", "lat": 27.0844, "lon": 93.6053},
            {"name": "Tawang", "lat": 27.5860, "lon": 91.8670},
        ],
        "highways": ["NH415", "NH13"],
        "districts": ["Papum Pare", "Tawang"],
    },
    "Himachal Pradesh": {
        "cities": [
            {"name": "Shimla", "lat": 31.1048, "lon": 77.1734},
            {"name": "Manali", "lat": 32.2396, "lon": 77.1887},
        ],
        "highways": ["NH3", "NH5"],
        "districts": ["Shimla", "Kullu"],
    },
    "Uttarakhand": {
        "cities": [
            {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322},
            {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642},
        ],
        "highways": ["NH58", "NH7"],
        "districts": ["Dehradun", "Haridwar"],
    },
    "Punjab": {
        "cities": [
            {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
            {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
        ],
        "highways": ["NH44", "NH1"],
        "districts": ["Chandigarh", "Ludhiana"],
    },
    "Haryana": {
        "cities": [
            {"name": "Gurugram", "lat": 28.4595, "lon": 77.0266},
            {"name": "Faridabad", "lat": 28.4089, "lon": 77.3178},
        ],
        "highways": ["NH48", "NH19"],
        "districts": ["Gurugram", "Faridabad"],
    },
    "Delhi": {
        "cities": [
            {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090},
        ],
        "highways": ["NH44", "NH48", "NH19"],
        "districts": ["New Delhi", "South Delhi"],
    },
}
```

#### Source List
```python
SOURCE_LIST = [
    {"name": "IMD", "type": "government"},
    {"name": "NDMA", "type": "government"},
    {"name": "NHAI", "type": "government"},
    {"name": "BRO", "type": "government"},
    {"name": "NDRF", "type": "government"},
    {"name": "PWD", "type": "government"},
    {"name": "Traffic Police", "type": "verified_org"},
    {"name": "District Collector", "type": "government"},
    {"name": "ASDMA", "type": "government"},  # Assam
    {"name": "HPSDMA", "type": "government"},  # Himachal Pradesh
    {"name": "KSDMA", "type": "government"},  # Kerala
    {"name": "OSDMA", "type": "government"},  # Odisha
    {"name": "BSDMA", "type": "government"},  # Bihar
    {"name": "MSRDC", "type": "government"},  # Maharashtra
    {"name": "PWD Manipur", "type": "government"},
    {"name": "PWD Nagaland", "type": "government"},
]
```

#### Text Templates by Hazard Type

**Flood (5 templates)**
```python
FLOOD_TEMPLATES = [
    "Severe flooding reported on {highway} near {location}, {state}. Waterlogging has rendered sections of the highway impassable. River overflow from the {river} has inundated the road surface. Vehicles above {weight} tonnes advised to avoid the corridor.",
    "The {river} river is running above danger level at {location}. Flooding has disrupted transport on {highway}. Several river-crossing ferries suspended. Cargo movement for {cargo_type} severely impacted.",
    "Heavy monsoon rainfall has caused waterlogging on {highway} near {location}, {state}. Delivery vehicles report delays of {delay} hours. Relief cargo movement through {nearby_city} is {status}.",
    "Floods in {region} have submerged sections of {highway} near {location}. The {river} is in spate. Trucking from {origin} to {destination} is {status}. {agency} teams deployed for relief operations.",
    "Coastal flooding along {highway} in {district} district has disrupted logistics. {source} has issued a {alert_level} alert for heavy rainfall. {transport_mode} suspended on the coastal route.",
]
```

**Landslide (4 templates)**
```python
LANDSLIDE_TEMPLATES = [
    "A major landslide on {highway} near {location} has completely blocked the {corridor} corridor. Debris flow has covered approximately {distance} metres of the highway. No alternative road route currently available. {alternative_mode} recommended for urgent supplies to {destination}.",
    "Multiple slope failures recorded on {highway} between {origin} and {destination}. Rockfall risk is high due to sustained heavy rainfall over the {region} hills. {restriction} traffic regulation in force.",
    "Heavy rainfall has triggered landslides on {highway} near {location}. The highway is closed to {traffic_type} traffic. {authority} convoys using alternate tracks. {stranded_count} trucks stranded at {checkpoint}.",
    "Landslides on {highway} in {district} district following {duration} of continuous rainfall. Highway partially blocked with debris. Clearance operations expected to take {clearance_time} hours. {alternative} route advised.",
]
```

**Heavy Rainfall (3 templates)**
```python
RAINFALL_TEMPLATES = [
    "{source} has issued a {alert_level} alert for extreme rainfall in {state}. {location} has recorded {rainfall_mm} mm in 24 hours. {highway} connecting {origin} to {destination} is at high risk of {hazard_type}.",
    "Persistent heavy rainfall has caused road surface damage and minor landslides on {highway} between {origin} and {destination}. Travel time has increased by approximately {delay} hours. Cargo operators advised to check road conditions before departure.",
    "Heavy rainfall on the {region} has reduced visibility and caused speed restrictions on {highway}. {authority} has reduced the speed limit to {speed} km/h. Cargo vehicles report {delay}-minute delays. No closures at this time.",
]
```

**Cyclone (3 templates)**
```python
CYCLONE_TEMPLATES = [
    "{source} has issued a cyclone watch for the {state} coast. {port1} and {port2} ports are on high alert. Fishing vessels recalled to shore. {highway} may face disruption as the storm approaches. Logistics companies advised to pre-position stocks inland.",
    "A deep depression in the Bay of Bengal is expected to intensify into a cyclone. {port} port has suspended operations. {highway} coastal sections near {location} are at risk of flooding and debris. {agency} units pre-positioned.",
    "Cyclone {name} approaching the {region} coast. {source} forecasts landfall near {location} within {hours} hours. {highway} traffic suspended. Evacuation orders in effect for {district} district.",
]
```

**Accident (3 templates)**
```python
ACCIDENT_TEMPLATES = [
    "A multi-vehicle pile-up on {highway} near {location} has blocked the highway. Clearance operations in progress. Trucks being diverted via {alternate_route}. Estimated clearance time: {hours} hours.",
    "Tanker overturned on {highway} at {location}, {state}. Fuel spillage has closed both carriageways. {authority} on site. Diversions via {alternate_route} in place. Expected reopening: {time}.",
    "Heavy vehicle accident on {highway} near {location} causing {delay}-hour delays. {casualties} reported. Traffic diverted through {alternate_location}. {restriction} vehicles only on alternate route.",
]
```

**Infrastructure (2 templates)**
```python
INFRA_TEMPLATES = [
    "A critical bridge on {highway} in {state} has been placed under a weight restriction of {weight} tonnes following structural inspection findings. Heavy cargo trucks must use the {alternate_highway} bypass via {alternate_location}. This affects the {corridor} freight corridor.",
    "{highway} maintenance works between {location1} and {location2} causing lane closures. {duration}-day project. Single-lane traffic in operation. Heavy vehicles restricted to {time_window}. Expect {delay}-hour delays during peak hours.",
]
```

**Heat (2 templates)**
```python
HEAT_TEMPLATES = [
    "Extreme heat in {state} (daytime temperatures exceeding {temp}°C) has caused road surface deformation on sections of {highway}. {cargo_type} are advised to avoid peak-daytime travel ({time_window}). Driver fatigue and vehicle overheating incidents reported.",
    "{source} issues heatwave warning for {region}. Temperatures forecast to reach {temp}°C. {highway} between {location1} and {location2} experiencing surface damage. Night-time travel recommended for heavy cargo.",
]
```

### Implementation Steps

1. **Create file structure**  
   - Create `routeOptimiserBackend/src/ir/corpus_generator.py`
   - Import: `from __future__ import annotations`, `import random`, `from datetime import date, timedelta`, `from src.ir.schemas import IRDocument`

2. **Define constants**  
   - `INDIA_GEO_DATA` dict (20+ states as shown above)
   - `SOURCE_LIST` (10+ sources)
   - Template lists for each hazard type
   - Hazard distribution weights: `{"flood": 0.30, "landslide": 0.25, "rainfall": 0.15, "cyclone": 0.10, "accident": 0.10, "infra": 0.08, "heat": 0.02}`
   - Severity distribution weights: `{"low": 0.20, "medium": 0.40, "high": 0.30, "critical": 0.10}`

3. **Implement generate_corpus(count=1000, seed=42)**  
   - Call `random.seed(seed)` first
   - Loop `count` times
   - For each iteration:
     - Select hazard using `random.choices(hazard_types, weights=hazard_weights)`
     - Select severity using `random.choices(severity_types, weights=severity_weights)`
     - Select state from INDIA_GEO_DATA (weighted toward NER states)
     - Select city and highway from that state
     - Select template for the hazard type
     - Fill template placeholders with selected values
     - Generate date: `random_date = date(2024, 1, 1) + timedelta(days=random.randint(0, 1095))`
     - Generate document ID: `f"GEN_{hazard_prefix}{str(counter).zfill(3)}"`
     - Create IRDocument instance with all fields
     - Add to results list
   - Return results

4. **Hazard prefix mapping**  
   ```python
   HAZARD_PREFIX = {
       "flood": "F", "landslide": "L", "rainfall": "R",
       "cyclone": "C", "accident": "A", "infra": "I", "heat": "H"
   }
   ```

5. **Severity phrase mapping**  
   ```python
   SEVERITY_PHRASES = {
       "critical": ["completely blocked", "impassable", "evacuation required", "no alternative route"],
       "high": ["severe disruption", "major delays", "high risk", "restricted access"],
       "medium": ["moderate delays", "caution advised", "partially obstructed", "slow traffic"],
       "low": ["minor delay", "advisory only", "passable with care", "monitoring situation"],
   }
   ```

### Verification

- [ ] 1. Run `cd routeOptimiserBackend && python -c "from src.ir.corpus_generator import generate_corpus; docs = generate_corpus(1000, 42); print(f'Generated {len(docs)} documents')"`
  - Expected output: `Generated 1000 documents`
- [ ] 2. Check determinism: generate twice and compare first 5 doc IDs
- [ ] 3. Check hazard distribution: `from collections import Counter; Counter(d.hazard for d in docs)`
- [ ] 4. Check severity distribution: `Counter(d.severity for d in docs)`
- [ ] 5. Check all docs have valid coordinates and dates

---

## FEAT-002: Integrate Generator into corpus.py

### Files
- **Modify**: `routeOptimiserBackend/src/ir/corpus.py`

### Changes

1. **Add import** at top of file:
   ```python
   from src.ir.corpus_generator import generate_corpus
   ```

2. **Modify `build_corpus()` function**:
   ```python
   def build_corpus(live_incidents: list[dict] | None = None) -> list[IRDocument]:
       """
       Build the full retrieval corpus.
       
       Composition:
       - 24 hand-curated SEED_DOCUMENTS (DOC_*)
       - 1000 generated documents (GEN_*)
       - Live incidents from database (INC_*, if provided)
       
       Total: 1024+ documents.
       """
       # Start with hand-curated seed documents
       docs = list(SEED_DOCUMENTS)
       
       # Add generated documents
       generated = generate_corpus(count=1000, seed=42)
       docs.extend(generated)
       
       # Append live incidents if provided
       if live_incidents:
           for inc in live_incidents:
               doc = IRDocument(
                   id=f"INC_{inc.get('id', 'unknown')}",
                   title=inc.get("type", "incident").replace("_", " ").title()
                       + f" — {inc.get('location', inc.get('segment_id', 'unknown'))}",
                   text=(
                       f"{inc.get('description', '')} "
                       f"Severity: {inc.get('severity', 'unknown')}. "
                       f"Reported by: {inc.get('source', 'field reporter')}."
                   ).strip(),
                   source=inc.get("source", "field"),
                   source_type="verified_field" if inc.get("status") == "verified" else "unverified",
                   date=str(inc.get("created_at", "2026-01-01"))[:10],
                   location=inc.get("location", inc.get("segment_id", "India")),
                   hazard=inc.get("type", "road_block"),
                   severity=_sev_label(inc.get("severity", 1)),
                   latitude=inc.get("latitude"),
                   longitude=inc.get("longitude"),
                   state=inc.get("state"),
                   tags=_inc_tags(inc),
                   provenance="LIVE",
               )
               docs.append(doc)
       
       return docs
   ```

3. **Keep** `SEED_DOCUMENTS` list unchanged
4. **Keep** `get_seed_documents()` function unchanged

### Verification

- [ ] 1. Run `cd routeOptimiserBackend && python -c "from src.ir.corpus import build_corpus; docs = build_corpus(); print(f'Total: {len(docs)}'); print(f'First: {docs[0].id}'); print(f'25th: {docs[24].id}')"`
  - Expected: `Total: 1024`, `First: DOC_F001`, `25th: GEN_F001` (or similar GEN_ prefix)
- [ ] 2. Run full test suite: `cd routeOptimiserBackend && python -m pytest -xvs`
- [ ] 3. Start backend: `python main.py`, check logs for "documents indexed: 1024"

---

## FEAT-003: Remove Provenance Filter UI and API Parameter

### Frontend Changes

**File**: `routeOptimiserFrontend/src/pages/IntelligenceSearch.jsx`  
**Component**: `CorpusBrowser` (starts around line 550)

**Remove these lines:**
1. Line ~570: `const [provF, setProvF] = useState("");`
2. Line ~576: `const PROVS = ["", "SYNTHETIC", "SAMPLED", "LIVE"];`
3. Line ~583-586: The provenance `<select>` dropdown (between state input and Browse button)
   ```jsx
   <select value={provF} onChange={e => setProvF(e.target.value)}
     className="bg-surface border border-white/20 rounded px-3 py-1.5 text-ink text-xs">
     {PROVS.map(p => <option key={p} value={p}>{p || "All provenance"}</option>)}
   </select>
   ```
4. Line ~581: Inside `load()` function: `if (provF) params.set("provenance", provF);`
5. Line ~605: Inside the document row button header: Remove the provenance `<Badge>` that appears next to the severity badge in the collapsed row

**Keep unchanged:**
- Line ~620: Provenance badge in the expanded document details section (this is metadata display, not a filter control)
- `PROV_BADGE` constant (used by EvidenceCard and WhyPanel)
- EvidenceCard component provenance badges
- WhyPanel component provenance badges

### Backend Changes

**File**: `routeOptimiserBackend/src/api/ir_routes.py`  
**Function**: `corpus_browser()` (starts around line 205)

**Remove these lines:**
1. Line ~216: `provenance = (request.args.get("provenance") or "").upper()`
2. Line ~220-221:
   ```python
   if provenance:
       docs = [d for d in docs if d.provenance == provenance]
   ```

**Keep unchanged:**
- `hazard`, `state`, `severity` filters

### Verification

- [ ] 1. Frontend: `cd routeOptimiserFrontend && npm run build`
  - Expected: Build succeeds with no errors
- [ ] 2. Backend: `cd routeOptimiserBackend && python -m pytest -xvs`
  - Expected: All tests pass
- [ ] 3. Manual test:
  - Start backend: `python main.py`
  - Start frontend: `npm run dev`
  - Open Corpus Browser tab
  - Confirm: Filter row shows only Hazard dropdown, State text input, Browse button — no provenance dropdown
  - Click a document to expand
  - Confirm: Provenance badge still appears in the expanded metadata section
- [ ] 4. API test: `curl "http://localhost:5001/api/ir/corpus?hazard=flood"`
  - Expected: Returns flood documents, no error
- [ ] 5. API test: `curl "http://localhost:5001/api/ir/corpus?provenance=LIVE"`
  - Expected: Returns all documents (ignores provenance parameter)

---

## Summary

| Feature | Files Changed | LOC Change | Dependency |
|---|---|---|---|
| FEAT-001 | 1 new file | +400 | None |
| FEAT-002 | 1 modified | +10 | FEAT-001 |
| FEAT-003 | 2 modified | -15 | None |

**Total estimated effort**: 2-3 hours for implementation + testing

**Final corpus size**: 1024 documents (24 seed + 1000 generated)

**Determinism guarantee**: Calling `build_corpus()` multiple times produces identical corpus in identical order (seeded random with seed=42)
