"""Default LangGraph-powered orchestration graph."""
from __future__ import annotations

import time
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from app import memory, rag, tools_web
from app.logging import JsonTracer


class AgentState(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    mode: str
    retrieved_chunks: List[Dict[str, Any]]
    web_results: List[Dict[str, Any]]
    pages: List[Dict[str, Any]]
    sources: List[str]
    memory_hits: List[Dict[str, Any]]
    reply: str
    meta: Dict[str, Any]
    client: Any
    tracer: JsonTracer
    trace_id: str


def _log(state: AgentState, node: str, **payload: Any) -> None:
    tracer = state.get("tracer")
    trace_id = state.get("trace_id")
    if not tracer or not trace_id:
        return
    tracer.append(trace_id, {"node": node, **payload})


def _last_user_message(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages:
        return ""
    return messages[-1].get("content", "")


def route_logic(state: AgentState) -> str:
    mode = state.get("mode", "hybrid").lower()
    if mode not in {"offline", "web", "hybrid"}:
        mode = "hybrid"
    return mode


def route_node(state: AgentState) -> AgentState:
    query = _last_user_message(state)
    try:
        state["memory_hits"] = memory.search_memory(query, k=3)
    except Exception:
        state["memory_hits"] = []
    return state


def retrieve_node(state: AgentState) -> AgentState:
    start = time.time()
    query = _last_user_message(state)
    try:
        chunks = rag.query_index(query, k=4)
    except Exception:
        chunks = []
    state["retrieved_chunks"] = chunks
    duration = time.time() - start
    _log(state, "retrieve", duration=duration, hits=len(chunks))
    return state


def research_plan_node(state: AgentState) -> AgentState:
    start = time.time()
    query = _last_user_message(state)
    plans = [query]
    if state.get("mode") == "hybrid":
        plans.append(f"context around {query}")
    duration = time.time() - start
    state["plan"] = plans
    _log(state, "plan", duration=duration, seeds=plans)
    return state


def search_node(state: AgentState) -> AgentState:
    start = time.time()
    query = _last_user_message(state)
    try:
        results = tools_web.web_search_ddg(query, max_results=5)
    except Exception:
        results = []
    state["web_results"] = results
    duration = time.time() - start
    _log(state, "search", duration=duration, results=len(results))
    return state


def crawl_node(state: AgentState) -> AgentState:
    start = time.time()
    urls = [item.get("href") for item in state.get("web_results", []) if item.get("href")]
    try:
        pages = tools_web.crawl(urls, depth=1, max_pages=5)
    except Exception:
        pages = []
    state["pages"] = pages
    duration = time.time() - start
    _log(state, "crawl", duration=duration, pages=len(pages))
    return state


def synthesize_node(state: AgentState) -> AgentState:
    start = time.time()
    client = state.get("client")
    query = _last_user_message(state)
    retrieved_chunks = state.get("retrieved_chunks", [])
    pages = state.get("pages", [])
    memory_hits = state.get("memory_hits", [])

    context_parts: List[str] = []
    sources: List[str] = []

    for chunk in retrieved_chunks:
        context_parts.append(f"Local: {chunk.get('snippet')}")
        if path := chunk.get("path"):
            sources.append(path)

    for episode in memory_hits:
        context_parts.append(f"Memory: {episode.get('response', '')[:400]}")
        sources.append(f"memory://{episode.get('episode_id')}")

    for page in pages:
        context_parts.append(f"Web: {page.get('text', '')[:500]}")
        if url := page.get("url"):
            sources.append(url)

    prompt = "\n\n".join(context_parts)
    messages = [
        {"role": "system", "content": "Answer the question with the provided context and cite sources."},
        {"role": "user", "content": f"Question: {query}\n\nContext:\n{prompt}"},
    ]

    reply = ""
    if client:
        try:
            response = client.generate(messages, stream=False)
            reply = response.get("message", {}).get("content", "")
        except Exception:
            reply = "Unable to generate response at this time."
    state["reply"] = reply or "No answer generated."
    state["sources"] = sources
    duration = time.time() - start
    _log(state, "synthesize", duration=duration, sources=len(sources))
    return state


def respond_node(state: AgentState) -> Dict[str, Any]:
    reply = state.get("reply", "No response.")
    sources = state.get("sources", [])
    meta = {
        "mode": state.get("mode"),
        "retrieved": len(state.get("retrieved_chunks", [])),
        "web_results": len(state.get("web_results", [])),
        "pages": len(state.get("pages", [])),
        "memory_hits": len(state.get("memory_hits", [])),
    }
    _log(state, "respond", duration=0, reply_length=len(reply))
    return {"reply": reply, "sources": sources, "meta": meta}


def build_default_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("route", route_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("plan", research_plan_node)
    graph.add_node("search", search_node)
    graph.add_node("crawl", crawl_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("route")

    def _route_decision(state: AgentState) -> str:
        return route_logic(state)

    graph.add_conditional_edges(
        "route",
        _route_decision,
        {
            "offline": "retrieve",
            "web": "plan",
            "hybrid": "retrieve",
        },
    )

    graph.add_conditional_edges(
        "retrieve",
        lambda state: "respond" if state.get("mode") == "offline" else "plan",
        {
            "respond": "respond",
            "plan": "plan",
        },
    )

    graph.add_edge("plan", "search")
    graph.add_edge("search", "crawl")
    graph.add_edge("crawl", "synthesize")
    graph.add_edge("synthesize", "respond")

    compiled = graph.compile()

    def runner(state: Dict[str, Any]) -> Dict[str, Any]:
        state.setdefault("mode", "hybrid")
        return compiled.invoke(state)

    return runner
