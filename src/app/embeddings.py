"""Shared embedding utilities used across local memory and RAG."""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=4)
def get_encoder(model_name: str = DEFAULT_EMBED_MODEL) -> SentenceTransformer:
    """Return a cached sentence transformer encoder."""
    return SentenceTransformer(model_name)


__all__ = ["DEFAULT_EMBED_MODEL", "get_encoder"]
