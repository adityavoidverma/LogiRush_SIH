# src/ir/corpus.py
"""
LogiRush Logistics Corpus.

Every document in this file is clearly labelled with provenance:
  SYNTHETIC  — fabricated for demonstration; never presented as a real event.
  SAMPLED    — derived from known patterns / open data; representative but not live.
  LIVE       — injected at runtime from the live incident database.

The corpus is Pan-India and multi-hazard.  NER documents are included but the
collection covers major corridors across all Indian states and hazard types.
"""

from __future__ import annotations

from src.ir.schemas import IRDocument

# ─────────────────────────────────────────────────────────────────────
# SEED CORPUS
# DO NOT add real government data here without explicit attribution.
# Label everything SYNTHETIC or SAMPLED honestly.
# ─────────────────────────────────────────────────────────────────────
SEED_DOCUMENTS: list[IRDocument] = [

    # ── Floods ────────────────────────────────────────────────────────
    IRDocument(
        id="DOC_F001",
        title="NH27 severe flooding near Guwahati",
        text=(
            "Severe flooding has been reported on NH27 near Guwahati, Assam. "
            "Waterlogging has rendered large sections of the highway impassable. "
            "River overflow from the Brahmaputra has inundated the road surface "
            "at multiple points between Guwahati and Shillong junction. "
            "Vehicles above 2 tonnes are advised to avoid the corridor."
        ),
        source="IMD",
        source_type="government",
        date="2026-09-05",
        location="Guwahati, Assam",
        hazard="flood",
        severity="high",
        latitude=26.1445, longitude=91.7362,
        route="NH27", state="Assam", highway="NH27",
        tags=["flood", "NH27", "Guwahati", "Assam", "road closure", "Brahmaputra"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_F002",
        title="Brahmaputra flooding disrupts Assam logistics",
        text=(
            "The Brahmaputra river is running well above danger level at Tezpur. "
            "Flooding has disrupted transport between Guwahati and Tinsukia along NH715. "
            "Several river-crossing ferries have been suspended. "
            "Cargo movement for perishables is severely impacted."
        ),
        source="ASDMA",
        source_type="government",
        date="2026-09-04",
        location="Tezpur, Assam",
        hazard="flood",
        severity="high",
        latitude=26.6333, longitude=92.8000,
        route="NH715", state="Assam",
        tags=["flood", "Brahmaputra", "Tezpur", "Assam", "NH715", "ferry suspension"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_F003",
        title="Kolkata suburban roads waterlogged after heavy rainfall",
        text=(
            "Heavy monsoon rainfall over the past 48 hours has caused waterlogging "
            "on suburban roads in South Kolkata and along the Eastern Bypass. "
            "Delivery vehicles report delays of 2-4 hours. NH16 entry from Howrah "
            "is partially blocked. Relief cargo movement through Kolkata port is unaffected."
        ),
        source="IMD",
        source_type="government",
        date="2026-09-03",
        location="Kolkata, West Bengal",
        hazard="flood",
        severity="medium",
        latitude=22.5726, longitude=88.3639,
        state="West Bengal", highway="NH16",
        tags=["flood", "waterlogging", "Kolkata", "West Bengal", "NH16", "monsoon"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_F004",
        title="Bihar floods: NH31 submerged near Muzaffarpur",
        text=(
            "Floods in North Bihar have submerged sections of NH31 near Muzaffarpur. "
            "The Bagmati and Gandak rivers are in spate. "
            "Trucking from Nepal border crossings to Patna is halted. "
            "NDRF teams have been deployed for relief operations."
        ),
        source="NDMA",
        source_type="government",
        date="2026-08-28",
        location="Muzaffarpur, Bihar",
        hazard="flood",
        severity="high",
        latitude=26.1209, longitude=85.3647,
        state="Bihar", highway="NH31",
        tags=["flood", "Bihar", "NH31", "Muzaffarpur", "NDRF", "road submerged"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_F005",
        title="Kerala coastal flooding — NH66 disrupted",
        text=(
            "Coastal flooding along NH66 in Ernakulam district has disrupted logistics. "
            "The India Meteorological Department has issued a red alert for heavy rainfall. "
            "KSRTC buses suspended on the coastal route. Cargo vessels advised to stay in port."
        ),
        source="IMD",
        source_type="government",
        date="2026-08-25",
        location="Ernakulam, Kerala",
        hazard="flood",
        severity="high",
        latitude=9.9816, longitude=76.2999,
        state="Kerala", highway="NH66",
        tags=["flood", "Kerala", "Ernakulam", "NH66", "coastal flood", "red alert"],
        provenance="SYNTHETIC",
    ),

    # ── Landslides ─────────────────────────────────────────────────────
    IRDocument(
        id="DOC_L001",
        title="NH10 landslide blocks Sikkim-Bengal corridor",
        text=(
            "A major landslide on NH10 near Rangpo has completely blocked the Sikkim-West Bengal "
            "corridor. Debris flow has covered approximately 200 metres of the highway. "
            "No alternative road route is currently available. Air transport is recommended "
            "for urgent medical supplies to Gangtok."
        ),
        source="BRO",
        source_type="government",
        date="2026-09-02",
        location="Rangpo, Sikkim",
        hazard="landslide",
        severity="critical",
        latitude=27.1760, longitude=88.5313,
        route="NH10", state="Sikkim", highway="NH10",
        tags=["landslide", "NH10", "Sikkim", "Rangpo", "road blocked", "debris flow", "BRO"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_L002",
        title="Manipur hill-section landslides on NH2",
        text=(
            "Multiple slope failures recorded on NH2 between Imphal and Dimapur. "
            "Rockfall risk is high due to sustained heavy rainfall over the Manipur hills. "
            "One-way traffic regulation in force. Convoy movement restricted to daylight hours."
        ),
        source="PWD Manipur",
        source_type="government",
        date="2026-09-01",
        location="Senapati, Manipur",
        hazard="landslide",
        severity="high",
        latitude=25.2741, longitude=94.0181,
        route="NH2", state="Manipur", highway="NH2",
        tags=["landslide", "NH2", "Manipur", "slope failure", "rockfall", "convoy"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_L003",
        title="Himachal Pradesh: Manali-Leh highway blocked by landslides",
        text=(
            "Heavy rainfall has triggered landslides on the Manali-Leh highway (NH3) near "
            "Rohtang Pass. The highway is closed to civilian traffic. "
            "Army convoys are using alternate tracks. "
            "Tourists and cargo trucks stranded at Keylong."
        ),
        source="HPSDMA",
        source_type="government",
        date="2026-09-01",
        location="Rohtang, Himachal Pradesh",
        hazard="landslide",
        severity="critical",
        latitude=32.3729, longitude=77.2432,
        state="Himachal Pradesh", highway="NH3",
        tags=["landslide", "NH3", "Himachal Pradesh", "Manali", "Rohtang", "highway blocked"],
        provenance="SYNTHETIC",
    ),

    # ── Cyclone ────────────────────────────────────────────────────────
    IRDocument(
        id="DOC_C001",
        title="Cyclone alert for Odisha coast — port closures expected",
        text=(
            "IMD has issued a cyclone watch for the Odisha coast. "
            "Paradip and Gopalpur ports are on high alert. "
            "Fishing vessels recalled to shore. "
            "NH16 and NH203 may face disruption as the storm approaches. "
            "Logistics companies advised to pre-position stocks inland."
        ),
        source="IMD",
        source_type="government",
        date="2026-09-06",
        location="Paradip, Odisha",
        hazard="cyclone",
        severity="high",
        latitude=20.3164, longitude=86.6090,
        state="Odisha", highway="NH16",
        tags=["cyclone", "Odisha", "Paradip", "port closure", "NH16", "coastal"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_C002",
        title="Andhra Pradesh cyclone warning — coastal highway NH16 at risk",
        text=(
            "A deep depression in the Bay of Bengal is expected to intensify into a cyclone. "
            "Visakhapatnam and Kakinada ports have suspended operations. "
            "NH16 coastal sections near Bheemunipatnam are at risk of flooding and debris. "
            "NDRF units pre-positioned."
        ),
        source="IMD",
        source_type="government",
        date="2026-08-30",
        location="Visakhapatnam, Andhra Pradesh",
        hazard="cyclone",
        severity="high",
        latitude=17.6868, longitude=83.2185,
        state="Andhra Pradesh", highway="NH16",
        tags=["cyclone", "Andhra Pradesh", "Visakhapatnam", "NH16", "Bay of Bengal"],
        provenance="SYNTHETIC",
    ),

    # ── Extreme Rainfall ───────────────────────────────────────────────
    IRDocument(
        id="DOC_R001",
        title="IMD red alert: extreme rainfall in Meghalaya",
        text=(
            "IMD has issued a red alert for extreme rainfall in Meghalaya. "
            "Cherrapunji has recorded 320 mm in 24 hours. "
            "NH6 connecting Shillong to Silchar is at high risk of washouts. "
            "Flash floods reported in East Khasi Hills district."
        ),
        source="IMD",
        source_type="government",
        date="2026-09-05",
        location="Cherrapunji, Meghalaya",
        hazard="rainfall",
        severity="critical",
        latitude=25.2701, longitude=91.7318,
        state="Meghalaya", highway="NH6",
        tags=["rainfall", "Meghalaya", "Cherrapunji", "NH6", "red alert", "flash flood", "Shillong"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_R002",
        title="Heavy rainfall causes delays on NH44 in Nagaland",
        text=(
            "Persistent heavy rainfall has caused road surface damage and minor landslides "
            "on NH44 between Kohima and Dimapur. "
            "Travel time has increased by approximately 3 hours. "
            "Cargo operators are advised to check road conditions before departure."
        ),
        source="PWD Nagaland",
        source_type="government",
        date="2026-09-03",
        location="Kohima, Nagaland",
        hazard="rainfall",
        severity="medium",
        latitude=25.6700, longitude=94.1100,
        state="Nagaland", highway="NH44",
        tags=["rainfall", "Nagaland", "NH44", "Kohima", "road damage"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_R003",
        title="Mumbai-Pune Expressway slowed by heavy rain",
        text=(
            "Heavy rainfall on the Western Ghats has reduced visibility and caused speed "
            "restrictions on the Mumbai-Pune Expressway. "
            "MSRDC has reduced the speed limit to 60 km/h. "
            "Cargo vehicles report 90-minute delays. No closures at this time."
        ),
        source="MSRDC",
        source_type="government",
        date="2026-09-04",
        location="Mumbai-Pune Expressway, Maharashtra",
        hazard="rainfall",
        severity="medium",
        latitude=18.5204, longitude=73.8567,
        state="Maharashtra",
        tags=["rainfall", "Maharashtra", "Mumbai", "Pune", "Expressway", "speed restriction"],
        provenance="SYNTHETIC",
    ),

    # ── Heat ───────────────────────────────────────────────────────────
    IRDocument(
        id="DOC_H001",
        title="Rajasthan heatwave: road surface damage on NH48",
        text=(
            "Extreme heat in Rajasthan (daytime temperatures exceeding 48°C) has caused "
            "road surface deformation on sections of NH48. "
            "Fuel tankers are advised to avoid peak-daytime travel (11 AM – 4 PM). "
            "Driver fatigue and vehicle overheating incidents have been reported."
        ),
        source="IMD",
        source_type="government",
        date="2026-06-10",
        location="Jaisalmer, Rajasthan",
        hazard="heat",
        severity="high",
        latitude=26.9157, longitude=70.9083,
        state="Rajasthan", highway="NH48",
        tags=["heat", "heatwave", "Rajasthan", "NH48", "road damage", "summer"],
        provenance="SYNTHETIC",
    ),

    # ── Road Blockage / Accidents ──────────────────────────────────────
    IRDocument(
        id="DOC_A001",
        title="Multi-vehicle accident on NH58 near Haridwar",
        text=(
            "A multi-vehicle pile-up on NH58 near Haridwar has blocked the highway. "
            "Clearance operations are in progress. "
            "Trucks are being diverted via SH57. "
            "Estimated clearance time: 6 hours."
        ),
        source="Traffic Police",
        source_type="verified_org",
        date="2026-09-06",
        location="Haridwar, Uttarakhand",
        hazard="accident",
        severity="medium",
        latitude=29.9457, longitude=78.1642,
        state="Uttarakhand", highway="NH58",
        tags=["accident", "NH58", "Haridwar", "Uttarakhand", "road block", "diversion"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_A002",
        title="Infrastructure: bridge weight restriction on NH716 Tripura",
        text=(
            "A critical bridge on NH716 in Tripura has been placed under a weight restriction "
            "of 12 tonnes following structural inspection findings. "
            "Heavy cargo trucks must use the NH44 bypass via Silchar. "
            "This affects the primary Agartala-Guwahati freight corridor."
        ),
        source="NHAI",
        source_type="government",
        date="2026-08-20",
        location="Udaipur, Tripura",
        hazard="infra",
        severity="high",
        latitude=23.5370, longitude=91.4849,
        state="Tripura", highway="NH716",
        tags=["infrastructure", "bridge", "weight restriction", "NH716", "Tripura", "Agartala", "NHAI"],
        provenance="SYNTHETIC",
    ),

    # ── Pan-India Corridors ────────────────────────────────────────────
    IRDocument(
        id="DOC_P001",
        title="Delhi-Guwahati freight corridor disruption summary",
        text=(
            "The Delhi-Guwahati freight corridor (NH27 / NH44) is experiencing cumulative "
            "disruption due to monsoon flooding in Bihar and Assam. "
            "Average transit time has increased from 72 hours to 120 hours. "
            "Shippers are advised to use rail alternatives where feasible. "
            "CONCOR reports normal operations on the NFR rail network."
        ),
        source="Ministry of Road Transport",
        source_type="government",
        date="2026-09-04",
        location="Delhi-Guwahati Corridor",
        hazard="flood",
        severity="high",
        state="Multi-state",
        tags=["corridor", "Delhi", "Guwahati", "NH27", "NH44", "freight", "disruption", "monsoon"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_P002",
        title="Guwahati to Kolkata: current road conditions",
        text=(
            "The Guwahati-Kolkata corridor via NH27 and NH12 is currently affected by: "
            "flooding near Dhubri (Assam-West Bengal border), road damage in North Bengal, "
            "and slow traffic at Siliguri. Recommended alternative: Assam-Bangladesh-Bangladesh "
            "transit route is not available for general cargo. "
            "Rail via NFR remains the most reliable option for medicine and relief material."
        ),
        source="NHAI",
        source_type="government",
        date="2026-09-05",
        location="Guwahati-Kolkata Corridor",
        hazard="flood",
        severity="high",
        state="Multi-state",
        tags=["Guwahati", "Kolkata", "NH27", "NH12", "corridor", "Dhubri", "West Bengal", "medicine"],
        provenance="SYNTHETIC",
    ),
    IRDocument(
        id="DOC_P003",
        title="Arunachal Pradesh: Itanagar connectivity impacted by landslides",
        text=(
            "Multiple landslides have reduced Itanagar to a single access corridor. "
            "NH415 between Banderdewa and Itanagar is partially blocked. "
            "Supply of medicines, fuel, and food is at risk. "
            "State government has requisitioned helicopter services for critical supplies."
        ),
        source="APDMA",
        source_type="government",
        date="2026-09-03",
        location="Itanagar, Arunachal Pradesh",
        hazard="landslide",
        severity="critical",
        latitude=27.0844, longitude=93.6053,
        state="Arunachal Pradesh", highway="NH415",
        tags=["landslide", "Arunachal Pradesh", "Itanagar", "NH415", "helicopter", "supply chain"],
        provenance="SYNTHETIC",
    ),

    # ── Historical / Background ────────────────────────────────────────
    IRDocument(
        id="DOC_B001",
        title="NER monsoon season logistics risk profile",
        text=(
            "The Northeast India monsoon season (June-September) historically increases "
            "logistics disruption risk by 60-80% compared to dry months. "
            "Key risk factors: Brahmaputra flooding, hill-road landslides on NH2/NH6/NH10, "
            "and isolation of Sikkim, Arunachal Pradesh, and Mizoram. "
            "Medicine and relief cargo should be pre-positioned before June."
        ),
        source="LogiRush Risk Engine",
        source_type="trusted_dataset",
        date="2026-01-01",
        location="Northeast India",
        hazard="flood",
        severity="medium",
        state="Multi-state",
        tags=["NER", "Northeast India", "monsoon", "risk profile", "logistics", "historical"],
        provenance="SAMPLED",
    ),
    IRDocument(
        id="DOC_B002",
        title="Pan-India hazard risk calendar",
        text=(
            "Seasonal hazard risk profile for India: "
            "June-September: flood risk (Bihar, Assam, West Bengal, Kerala, Odisha); "
            "cyclone risk (Bay of Bengal coast: Odisha, AP, Tamil Nadu); "
            "landslide risk (Himalayas, NER, Western Ghats). "
            "October-November: post-monsoon cyclone season (Coromandel Coast). "
            "April-June: heat risk (Rajasthan, MP, Vidarbha)."
        ),
        source="LogiRush Risk Engine",
        source_type="trusted_dataset",
        date="2026-01-01",
        location="Pan-India",
        hazard="flood",
        severity="low",
        tags=["hazard calendar", "Pan-India", "flood", "cyclone", "landslide", "heat", "seasonal"],
        provenance="SAMPLED",
    ),
    IRDocument(
        id="DOC_B003",
        title="Medicine cold-chain transport guidelines for NER",
        text=(
            "Medical supply cold-chain transport in Northeast India must account for: "
            "road accessibility during monsoon, limited backup storage facilities, "
            "helicopter contingency for Sikkim and Arunachal Pradesh. "
            "Priority corridors: Guwahati (hub) → state capitals. "
            "Critical buffer stock of 30 days recommended at Guwahati regional warehouse."
        ),
        source="Ministry of Health",
        source_type="government",
        date="2026-03-15",
        location="Northeast India",
        hazard="flood",
        severity="medium",
        tags=["medicine", "cold chain", "NER", "Guwahati", "Sikkim", "Arunachal Pradesh", "healthcare"],
        provenance="SAMPLED",
    ),
    IRDocument(
        id="DOC_B004",
        title="NH27 route profile: Guwahati to Shillong",
        text=(
            "NH27 connects Guwahati, Assam to Shillong, Meghalaya (approximately 103 km). "
            "Known hazard zones: Jorabat interchange flood risk during heavy monsoon; "
            "steep gradient sections with landslide susceptibility near Nongpoh. "
            "Alternative: Umiam bypass (NH6). Typical transit: 2.5-3.5 hours."
        ),
        source="NHAI",
        source_type="government",
        date="2026-04-01",
        location="Guwahati-Shillong Corridor",
        hazard="flood",
        severity="low",
        state="Assam",
        tags=["NH27", "Guwahati", "Shillong", "Meghalaya", "route profile", "NHAI"],
        provenance="SAMPLED",
    ),
]


def get_seed_documents() -> list[IRDocument]:
    """Return the static seed corpus."""
    return list(SEED_DOCUMENTS)


def build_corpus(live_incidents: list[dict] | None = None) -> list[IRDocument]:
    """
    Build the full retrieval corpus.

    Merges:
      1. The static seed documents (SYNTHETIC / SAMPLED).
      2. Live incidents from the database (LIVE provenance).

    Parameters
    ----------
    live_incidents : list of incident dicts from the database (optional)
    """
    docs = get_seed_documents()

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


def _sev_label(severity) -> str:
    try:
        s = int(severity)
    except (TypeError, ValueError):
        return "medium"
    if s >= 4:
        return "critical"
    if s == 3:
        return "high"
    if s == 2:
        return "medium"
    return "low"


def _inc_tags(inc: dict) -> list[str]:
    tags = []
    for key in ("type", "location", "state", "segment_id", "source"):
        val = inc.get(key)
        if val:
            tags.append(str(val))
    return tags
