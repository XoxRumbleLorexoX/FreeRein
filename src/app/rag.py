"""Local retrieval-augmented generation helpers backed by FAISS."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import numpy as np

from .config import settings
from .embeddings import DEFAULT_EMBED_MODEL, get_encoder
INDEX_FILE = Path("data/vectorstore/index.faiss")
META_FILE = Path("data/vectorstore/metadata.json")


@dataclass
class IndexStats:
    documents_indexed: int
    dim: int


def _load_documents(directory: Path) -> List[Tuple[str, str]]:
    docs: List[Tuple[str, str]] = []
    for path in directory.rglob("*"):
        if path.suffix.lower() not in {".txt", ".md", ""}:
            continue
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        docs.append((str(path), content))
    return docs


def build_index(directory: Path | None = None) -> IndexStats:
    directory = Path(directory or settings.docs_dir)
    directory.mkdir(parents=True, exist_ok=True)
    documents = _load_documents(directory)
    if not documents:
        raise RuntimeError(f"No documents found in {directory}")

    model = get_encoder(DEFAULT_EMBED_MODEL)
    texts = [content for _, content in documents]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_FILE))

    metadata = [{"path": path, "content": content} for path, content in documents]
    META_FILE.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")

    return IndexStats(documents_indexed=len(documents), dim=dim)


def _load_index() -> Tuple[faiss.Index, List[Dict[str, str]]]:
    if not INDEX_FILE.exists() or not META_FILE.exists():
        raise RuntimeError("Vector store not built. Run rag-index first.")
    index = faiss.read_index(str(INDEX_FILE))
    metadata: List[Dict[str, str]] = json.loads(META_FILE.read_text(encoding="utf-8"))
    return index, metadata


def query_index(question: str, k: int = 4) -> List[Dict[str, str]]:
    model = get_encoder(DEFAULT_EMBED_MODEL)
    index, metadata = _load_index()
    query_vec = model.encode([question], convert_to_numpy=True)
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, k)

    hits: List[Dict[str, str]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        doc_meta = metadata[idx]
        snippet = doc_meta.get("content", "")[:512]
        hits.append({
            "path": doc_meta.get("path"),
            "score": float(score),
            "snippet": snippet,
        })
    return hits
