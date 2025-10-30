"""FastAPI server exposing unified agent functionality."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.adapters import (
    AGENTS_AVAILABLE,
    get_agents_adapter,
    get_orchestrator,
    get_research_adapter,
    get_ui_adapter,
)
from app.config import settings
from app.logging import tracer
from app import memory, rag, reflection
from app.schemas import (
    AgentsChatRequest,
    AgentsChatResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MemoryQueryRequest,
    MemorySearchResponse,
    RAGIndexRequest,
    RAGIndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    ResearchRequest,
    ResearchResponse,
    ReflectionResponse,
)

app = FastAPI(title="lam-agent-unified", version="0.1.0")


def orchestrator_dep() -> Any:
    return get_orchestrator()


def research_dep() -> Any:
    return get_research_adapter()


def ui_dep() -> Any:
    return get_ui_adapter()


def agents_dep() -> Any:
    if not AGENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="openai-agents not installed")
    return get_agents_adapter()


@app.get("/health", response_model=HealthResponse)
def health(orchestrator=Depends(orchestrator_dep), research=Depends(research_dep), ui=Depends(ui_dep)) -> HealthResponse:
    return HealthResponse(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        web_enabled=settings.enable_web,
        frontend_enabled=settings.frontend_enabled,
        submodules={
            "langgraph": orchestrator.external_enabled,
            "deerflow": research.external_enabled,
            "copilotkit": ui.external_enabled,
        },
        agents_available=AGENTS_AVAILABLE,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, orchestrator=Depends(orchestrator_dep)) -> ChatResponse:
    result = orchestrator.run(request.message, mode=request.mode)
    return ChatResponse(**result)


@app.post("/rag/index", response_model=RAGIndexResponse)
def rag_index(request: RAGIndexRequest) -> RAGIndexResponse:
    directory = Path(request.dir) if request.dir else settings.docs_dir
    stats = rag.build_index(directory)
    return RAGIndexResponse(documents_indexed=stats.documents_indexed, dim=stats.dim)


@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
    try:
        results = rag.query_index(request.question, k=request.k)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RAGQueryResponse(results=results)


@app.post("/research", response_model=ResearchResponse)
def research(request: ResearchRequest, adapter=Depends(research_dep)) -> ResearchResponse:
    plan = adapter.plan(request.query)
    search_results = adapter.search(request.query, k=request.max_results)
    urls = [item.get("href") for item in search_results if item.get("href")]
    pages = adapter.crawl(urls, depth=request.depth, max_pages=request.max_results)
    synthesis = adapter.synthesize(pages)
    return ResearchResponse(pages=pages, synthesis=synthesis)


@app.post("/memory/search", response_model=MemorySearchResponse)
def memory_search(request: MemoryQueryRequest) -> MemorySearchResponse:
    episodes = memory.search_memory(request.query, k=request.k)
    return MemorySearchResponse(episodes=episodes)


@app.post("/agents/chat", response_model=AgentsChatResponse)
def agents_chat(request: AgentsChatRequest, adapter=Depends(agents_dep)) -> AgentsChatResponse:
    result = adapter.run(request.prompt)
    return AgentsChatResponse(**result)


@app.post("/reflection/run", response_model=ReflectionResponse)
def reflection_run(limit: int = 5) -> ReflectionResponse:
    record = reflection.run_reflection(limit=limit)
    return ReflectionResponse(notes=record["notes"], episode_count=record["episode_count"])


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_directories()
    tracer.append("startup", {"event": "startup", "mode": settings.mode})
