"""Lightweight episodic memory built on FAISS + JSONL storage."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

from .config import settings
from .embeddings import DEFAULT_EMBED_MODEL, get_encoder

MEMORY_DIR = Path(settings.memory_dir)
INDEX_FILE = MEMORY_DIR / "episodic.faiss"
META_FILE = MEMORY_DIR / "episodes.json"
LOG_FILE = MEMORY_DIR / "episodes.jsonl"


@dataclass
class Episode:
    episode_id: str
    timestamp: float
    query: str
    response: str
    mode: str
    sources: List[str]
    meta: Dict[str, Any]


def _ensure_dirs() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> Tuple[faiss.Index | None, List[Dict[str, Any]]]:
    if not INDEX_FILE.exists() or not META_FILE.exists():
        return None, []
    index = faiss.read_index(str(INDEX_FILE))
    metadata: List[Dict[str, Any]] = json.loads(META_FILE.read_text(encoding="utf-8"))
    return index, metadata


def _write_index(index: faiss.Index, metadata: List[Dict[str, Any]]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def record_episode(query: str, response: str, mode: str, sources: List[str], meta: Dict[str, Any]) -> None:
    """Persist an interaction to episodic memory."""
    if not query or not response:
        return
    _ensure_dirs()
    encoder = get_encoder(DEFAULT_EMBED_MODEL)
    text = f"Question: {query}\nAnswer: {response}"
    embedding = encoder.encode([text], convert_to_numpy=True)
    faiss.normalize_L2(embedding)
    dim = embedding.shape[1]

    index, metadata = _load_index()
    if index is None:
        index = faiss.IndexFlatIP(dim)
    elif index.d != dim:
        # rebuild index if dimensionality changed
        index = faiss.IndexFlatIP(dim)
        metadata = []

    index.add(embedding)

    episode: Dict[str, Any] = {
        "episode_id": uuid.uuid4().hex,
        "timestamp": time.time(),
        "query": query,
        "response": response,
        "mode": mode,
        "sources": sources,
        "meta": meta,
    }
    metadata.append(episode)
    _write_index(index, metadata)

    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(episode, ensure_ascii=False) + "\n")


def search_memory(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Return similar prior episodes for the given prompt."""
    if not query:
        return []
    index, metadata = _load_index()
    if index is None or not metadata:
        return []

    encoder = get_encoder(DEFAULT_EMBED_MODEL)
    vector = encoder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(vector)
    scores, indices = index.search(vector, k)

    hits: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1 or idx >= len(metadata):
            continue
        episode = metadata[idx].copy()
        episode["score"] = float(score)
        hits.append(episode)
    return hits


def load_recent(limit: int = 10) -> List[Dict[str, Any]]:
    """Load the most recent episodes from the JSON metadata."""
    _, metadata = _load_index()
    if not metadata:
        return []
    return sorted(metadata, key=lambda item: item.get("timestamp", 0), reverse=True)[:limit]
