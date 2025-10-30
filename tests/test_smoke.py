from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.orchestrator import LangGraphAdapter
from app.logging import JsonTracer


class DummyClient:
    def generate(self, messages, stream=False):
        return {"message": {"content": "Test reply"}}


@pytest.fixture(autouse=True)
def setup_env(monkeypatch, tmp_path):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir(exist_ok=True)
    monkeypatch.setattr("app.logging.tracer", JsonTracer(trace_dir))
    monkeypatch.setattr("app.adapters.orchestrator.tracer", JsonTracer(trace_dir))
    monkeypatch.setattr("app.config.settings.trace_dir", trace_dir, raising=False)
    monkeypatch.setattr("app.adapters.orchestrator.get_client", lambda: DummyClient())
    monkeypatch.setattr("app.rag.query_index", lambda query, k=4: [{"path": "doc.txt", "snippet": "local chunk"}])
    monkeypatch.setattr("app.tools_web.web_search_ddg", lambda q, max_results=5: [])
    monkeypatch.setattr("app.tools_web.crawl", lambda urls, depth=1, max_pages=8: [])
    yield


def test_orchestrator_run():
    orchestrator = LangGraphAdapter()
    result = orchestrator.run("What is LangGraph?", mode="offline")
    assert "reply" in result
    assert result["meta"]["retrieved"] == 1


def test_tracing_output(tmp_path, monkeypatch):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir(exist_ok=True)
    local_tracer = JsonTracer(trace_dir)
    monkeypatch.setattr("app.logging.tracer", local_tracer)
    monkeypatch.setattr("app.adapters.orchestrator.tracer", local_tracer)
    monkeypatch.setattr("app.adapters.orchestrator.get_client", lambda: DummyClient())
    monkeypatch.setattr("app.rag.query_index", lambda query, k=4: [])
    monkeypatch.setattr("app.tools_web.web_search_ddg", lambda q, max_results=5: [])
    monkeypatch.setattr("app.tools_web.crawl", lambda urls, depth=1, max_pages=8: [])

    orchestrator = LangGraphAdapter()
    orchestrator.run("Explain FAISS", mode="offline")

    files = list(trace_dir.glob("*.jsonl"))
    assert files, "Expected trace file to be written"
