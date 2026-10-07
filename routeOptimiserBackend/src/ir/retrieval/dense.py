# src/ir/retrieval/dense.py
"""
Dense semantic retrieval using sentence embeddings.

Uses sentence-transformers with the all-MiniLM-L6-v2 model by default.
No external vector database is needed — embeddings are held in memory as a
numpy array and searched with cosine similarity.  For the corpus sizes
expected in this project (hundreds to low thousands of documents) this is
faster than spinning up Qdrant/FAISS and avoids an extra dependency.

If sentence-transformers is not installed the retriever falls back to a
stub that returns empty results, so the rest of the IR stack keeps working.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.ir.config import EMBEDDING_MODEL

if TYPE_CHECKING:
    from src.ir.schemas import IRDocument

logger = logging.getLogger("ir.dense")

_IMPORT_ERROR: Exception | None = None
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except ImportError as _e:
    _HAS_ST = False
    _IMPORT_ERROR = _e


class DenseRetriever:
    """
    Semantic retrieval over the corpus using a sentence-transformer model.

    Call build() once after constructing to encode all documents.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._model_name = model_name
        self._docs: list["IRDocument"] = []
        self._embeddings = None     # numpy array shape (N, dim)
        self._ready = False

        if not _HAS_ST:
            logger.warning(
                "sentence-transformers not installed (%s). "
                "Dense retrieval disabled — install it with: "
                "pip install sentence-transformers",
                _IMPORT_ERROR,
            )
            return

        try:
            self._model = SentenceTransformer(model_name)
            logger.info("Loaded embedding model: %s", model_name)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to load embedding model %s: %s", model_name, e)
            self._model = None

    def build(self, documents: list["IRDocument"]) -> "DenseRetriever":
        """Encode all documents and store embeddings."""
        if not _HAS_ST or self._model is None:
            return self

        self._docs = documents
        texts = [f"{d.title}. {d.text}" for d in documents]
        logger.info("Encoding %d documents with %s …", len(texts), self._model_name)
        self._embeddings = self._model.encode(
            texts, show_progress_bar=False, batch_size=64, normalize_embeddings=True
        )
        self._ready = True
        logger.info("Dense index built: %d vectors", len(self._docs))
        return self

    def query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Retrieve top-K documents by cosine similarity to the query embedding.

        Returns
        -------
        list of (doc_id, score) sorted by score descending.  Score in [0, 1].
        Returns [] if model is unavailable.
        """
        if not self._ready or self._embeddings is None:
            return []

        try:
            import numpy as np
            q_emb = self._model.encode(
                [query_text], show_progress_bar=False, normalize_embeddings=True
            )
            # cosine similarity = dot product when both are L2-normalised
            sims = (self._embeddings @ q_emb.T).flatten()
            top_indices = np.argsort(sims)[::-1][:top_k]
            return [
                (self._docs[i].id, float(sims[i]))
                for i in top_indices
                if float(sims[i]) > 0.0
            ]
        except Exception as e:  # pragma: no cover
            logger.warning("Dense query failed: %s", e)
            return []

    @property
    def is_ready(self) -> bool:
        return self._ready
