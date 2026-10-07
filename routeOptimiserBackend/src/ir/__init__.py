# src/ir/__init__.py
"""
LogiRush IR Engine — Pan-India Multi-Hazard Logistics Intelligence Search.

Provides hybrid information retrieval over a logistics-domain corpus:
  - Inverted index + TF-IDF (classical IR)
  - BM25 (strong lexical baseline)
  - Dense retrieval via sentence embeddings
  - Hybrid score fusion with configurable weights
  - Freshness, geographic, and source-authority re-ranking
  - Query parsing and expansion
  - Evaluation tooling (P@K, Recall@K, MRR, latency)
"""
