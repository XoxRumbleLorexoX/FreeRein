"""Structured JSONL tracing utilities."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from uuid import uuid4

from .config import settings


class JsonTracer:
    """Append-only JSONL tracer with minimal overhead."""

    def __init__(self, trace_dir: Path | str | None = None) -> None:
        self.trace_dir = Path(trace_dir or settings.trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, request_id: str) -> Path:
        return self.trace_dir / f"{request_id}.jsonl"

    def append(self, request_id: str, payload: Dict[str, Any]) -> None:
        record = payload.copy()
        record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with self._file_path(request_id).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    @contextmanager
    def span(self, request_id: Optional[str] = None, **meta: Any) -> Generator[str, None, None]:
        rid = request_id or uuid4().hex
        start = datetime.utcnow()
        self.append(rid, {"event": "start", **meta})
        try:
            yield rid
        except Exception as exc:  # pragma: no cover - re-raised after logging
            self.append(rid, {"event": "error", "error": repr(exc)})
            raise
        else:
            duration = (datetime.utcnow() - start).total_seconds()
            self.append(rid, {"event": "end", "duration": duration})


def new_trace_id() -> str:
    return uuid4().hex


def get_tracer() -> JsonTracer:
    return JsonTracer()


tracer = get_tracer()
