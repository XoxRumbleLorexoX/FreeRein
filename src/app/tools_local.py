"""Offline tooling for local knowledge and filesystem interactions."""
from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Dict, List

from .config import settings

DOCS_DIR = Path(settings.docs_dir).resolve()


def _safe_path(path: str | Path) -> Path:
    target = (DOCS_DIR / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if DOCS_DIR not in target.parents and target != DOCS_DIR:
        raise PermissionError("Path outside of allowed documents directory")
    return target


def search_local_files(pattern: str, limit: int = 5) -> List[Dict[str, str]]:
    matches: List[Dict[str, str]] = []
    for root, _, filenames in os.walk(DOCS_DIR):
        for filename in filenames:
            if fnmatch.fnmatch(filename.lower(), f"*{pattern.lower()}*"):
                full_path = Path(root) / filename
                matches.append({"path": str(full_path), "name": filename})
                if len(matches) >= limit:
                    return matches
    return matches


def read_file(path: str) -> Dict[str, str]:
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(str(target))
    content = target.read_text(encoding="utf-8")
    return {"path": str(target), "content": content}


def list_dir(path: str = ".") -> Dict[str, List[str]]:
    target = _safe_path(path)
    if not target.exists() or not target.is_dir():
        raise NotADirectoryError(str(target))
    entries = sorted(os.listdir(target))
    return {"path": str(target), "entries": entries}


def write_file(path: str, content: str, overwrite: bool = False) -> Dict[str, str]:
    target = _safe_path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "bytes": len(content.encode("utf-8"))}
