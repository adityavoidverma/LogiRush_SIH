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
_HAS_ST: bool = False

def _try_import():
    """Attempt to import sentence_transformers at call time, not module load time.
    Returns (SentenceTransformer_class_or_None, success_bool).
    """
    try:
        from sentence_transformers import SentenceTransformer as ST  # type: ignore
        import numpy  # noqa: F401 — verify numpy is usable too
        return ST, True
    except Exception as e:
        logger.warning(
            "Dense retrieval unavailable: %s. "
            "Hybrid search will use BM25 + TF-IDF only. "
            "To enable: pip install sentence-transformers torch",
            e,
        )
        return None, False


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

        ST, ok = _try_import()
        if not ok or ST is None:
            self._model = None
            return

        try:
            self._model = ST(model_name)
            logger.info("Loaded embedding model: %s", model_name)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to load embedding model %s: %s", model_name, e)
            self._model = None

    def build(self, documents: list["IRDocument"]) -> "DenseRetriever":
        """Encode all documents and store embeddings."""
        if self._model is None:
            return self

        _, ok = _try_import()
        if not ok:
            return self

        self._docs = documents
        texts = [f"{d.title}. {d.text}" for d in documents]
        logger.info("Encoding %d documents with %s …", len(texts), self._model_name)
        try:
            self._embeddings = self._model.encode(
                texts, show_progress_bar=False, batch_size=64, normalize_embeddings=True
            )
            self._ready = True
            logger.info("Dense index built: %d vectors", len(self._docs))
        except Exception as e:  # pragma: no cover
            logger.warning("Dense encoding failed: %s", e)
        return self

    def query(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        """
        Retrieve top-K documents by cosine similarity to the query embedding.

        Returns
        -------
        list of (doc_id, score) sorted by score descending.  Score in [0, 1].
        Returns [] if model is unavailable.
        """
        if not self._ready or self._embeddings is None or self._model is None:
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
