# src/ir/evaluation/dataset.py
"""
Judged evaluation dataset for the LogiRush IR engine.

Each entry has a query and the set of document IDs that are relevant.
Judgements are based on the SEED corpus in corpus.py.
"""

from __future__ import annotations

JUDGED_QUERIES: list[dict] = [
    # ── Hazard queries ─────────────────────────────────────────────────
    {
        "id": "Q01",
        "query": "flood risk in Assam",
        "relevant_documents": ["DOC_F001", "DOC_F002", "DOC_P001", "DOC_P002", "DOC_B001"],
    },
    {
        "id": "Q02",
        "query": "landslide risk near Sikkim highways",
        "relevant_documents": ["DOC_L001", "DOC_L002", "DOC_L003"],
    },
    {
        "id": "Q03",
        "query": "cyclone impact on Odisha logistics",
        "relevant_documents": ["DOC_C001", "DOC_C002"],
    },
    {
        "id": "Q04",
        "query": "heavy rainfall affecting Kerala roads",
        "relevant_documents": ["DOC_F005", "DOC_R003"],
    },
    {
        "id": "Q05",
        "query": "heat risk for Rajasthan transport",
        "relevant_documents": ["DOC_H001"],
    },
    {
        "id": "Q06",
        "query": "Meghalaya extreme rainfall alert",
        "relevant_documents": ["DOC_R001", "DOC_B001"],
    },
    {
        "id": "Q07",
        "query": "Bihar floods NH31 blocked",
        "relevant_documents": ["DOC_F004", "DOC_P001"],
    },
    {
        "id": "Q08",
        "query": "Manipur highway landslide disruption",
        "relevant_documents": ["DOC_L002", "DOC_P003"],
    },
    # ── Logistics queries ──────────────────────────────────────────────
    {
        "id": "Q09",
        "query": "safe route for medicine from Guwahati to Kolkata",
        "relevant_documents": ["DOC_F001", "DOC_P001", "DOC_P002", "DOC_B003", "DOC_F003"],
    },
    {
        "id": "Q10",
        "query": "alternative route during Assam flooding",
        "relevant_documents": ["DOC_F001", "DOC_F002", "DOC_P001", "DOC_P002", "DOC_B001"],
    },
    {
        "id": "Q11",
        "query": "road disruption between Delhi and Guwahati",
        "relevant_documents": ["DOC_P001", "DOC_F004", "DOC_F001", "DOC_F002"],
    },
    {
        "id": "Q12",
        "query": "medicine cold chain transport northeast India",
        "relevant_documents": ["DOC_B003", "DOC_L001", "DOC_P003", "DOC_B001"],
    },
    {
        "id": "Q13",
        "query": "Arunachal Pradesh supply chain disruption landslide",
        "relevant_documents": ["DOC_P003", "DOC_L002", "DOC_B001"],
    },
    {
        "id": "Q14",
        "query": "NH10 Sikkim road blocked",
        "relevant_documents": ["DOC_L001"],
    },
    {
        "id": "Q15",
        "query": "Guwahati to Kolkata freight corridor monsoon",
        "relevant_documents": ["DOC_P002", "DOC_P001", "DOC_F001", "DOC_F003", "DOC_B001"],
    },
    # ── Multi-hazard queries ───────────────────────────────────────────
    {
        "id": "Q16",
        "query": "flood and landslide risk on northeast route",
        "relevant_documents": ["DOC_F001", "DOC_F002", "DOC_L001", "DOC_L002", "DOC_B001", "DOC_P001"],
    },
    {
        "id": "Q17",
        "query": "cyclone and rainfall impact on coastal logistics",
        "relevant_documents": ["DOC_C001", "DOC_C002", "DOC_R003", "DOC_F005"],
    },
    {
        "id": "Q18",
        "query": "monsoon disruption Pan-India highways",
        "relevant_documents": ["DOC_P001", "DOC_P002", "DOC_B002", "DOC_F004", "DOC_R001"],
    },
    # ── State-specific queries ─────────────────────────────────────────
    {
        "id": "Q19",
        "query": "Tripura cargo freight route",
        "relevant_documents": ["DOC_A002", "DOC_B001"],
    },
    {
        "id": "Q20",
        "query": "Himachal Pradesh highway closure",
        "relevant_documents": ["DOC_L003"],
    },
    {
        "id": "Q21",
        "query": "Uttarakhand road accident diversion",
        "relevant_documents": ["DOC_A001"],
    },
    {
        "id": "Q22",
        "query": "Nagaland road damage heavy rain",
        "relevant_documents": ["DOC_R002"],
    },
    {
        "id": "Q23",
        "query": "Kolkata West Bengal flooding road disruption",
        "relevant_documents": ["DOC_F003", "DOC_P002"],
    },
    {
        "id": "Q24",
        "query": "Mumbai Maharashtra expressway rain",
        "relevant_documents": ["DOC_R003"],
    },
    {
        "id": "Q25",
        "query": "NHAI bridge weight restriction freight",
        "relevant_documents": ["DOC_A002"],
    },
]


def get_queries() -> list[dict]:
    return list(JUDGED_QUERIES)
