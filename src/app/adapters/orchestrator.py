"""Orchestration adapter with optional LangGraph integration."""
from __future__ import annotations

import importlib
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict

from app import graphs, memory
from app.config import settings
from app.logging import tracer
from app.prompting import build_messages
from app.ollama import get_client

GraphCallable = Callable[[dict], dict]


class AbstractOrchestrator(ABC):
    @abstractmethod
    def build_graph(self) -> GraphCallable: ...

    @abstractmethod
    def run(self, query: str, mode: str = "hybrid") -> Dict[str, Any]: ...


class LangGraphAdapter(AbstractOrchestrator):
    def __init__(self) -> None:
        self._graph: GraphCallable | None = None
        self._external_available = self._attempt_import()

    def _attempt_import(self) -> bool:
        ext_path = Path("src_ext/langgraph").resolve()
        if ext_path.exists():
            sys.path.insert(0, str(ext_path))
            try:
                importlib.import_module("langgraph")  # noqa: F401
                return True
            except Exception:
                return False
        return False

    def build_graph(self) -> GraphCallable:
        if self._graph is None:
            self._graph = graphs.build_default_graph()
        return self._graph

    def run(self, query: str, mode: str = "hybrid") -> Dict[str, Any]:
        cleaned_mode = (mode or settings.mode).lower()
        if cleaned_mode not in {"offline", "web", "hybrid"}:
            cleaned_mode = settings.mode_normalized
        graph_callable = self.build_graph()
        messages = build_messages(query, cleaned_mode)
        client = get_client()
        episodic_hits = memory.search_memory(query, k=3)
        with tracer.span(component="orchestrator", mode=cleaned_mode) as trace_id:
            state = {
                "messages": messages,
                "mode": cleaned_mode,
                "client": client,
                "tracer": tracer,
                "trace_id": trace_id,
                "memory_hits": episodic_hits,
            }
            result = graph_callable(state)
            tracer.append(trace_id, {"event": "result", "meta": result.get("meta", {})})
        # enrich meta with episodic info
        result.setdefault("meta", {})
        result["meta"]["memory_hits"] = len(episodic_hits)
        if episodic_hits:
            result["meta"]["memory"] = [
                {"episode_id": hit.get("episode_id"), "score": hit.get("score"), "query": hit.get("query")}
                for hit in episodic_hits
            ]
        memory.record_episode(
            query=query,
            response=result.get("reply", ""),
            mode=cleaned_mode,
            sources=result.get("sources", []),
            meta=result.get("meta", {}),
        )
        return result

    @property
    def external_enabled(self) -> bool:
        return self._external_available


def get_orchestrator() -> LangGraphAdapter:
    return LangGraphAdapter()
