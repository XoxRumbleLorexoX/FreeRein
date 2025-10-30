"""Pydantic schemas shared across the application."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ToolCall(BaseModel):
    tool: str
    args: Dict[str, Any]


class ChatRequest(BaseModel):
    message: str
    mode: str = Field(default="hybrid")
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    reply: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class RAGIndexRequest(BaseModel):
    dir: Optional[str] = Field(default=None)


class RAGIndexResponse(BaseModel):
    documents_indexed: int
    dim: int


class RAGQueryRequest(BaseModel):
    question: str
    k: int = Field(default=4, ge=1, le=10)


class RAGQueryResponse(BaseModel):
    results: List[Dict[str, Any]]


class ResearchRequest(BaseModel):
    query: str
    depth: int = Field(default=1, ge=0, le=3)
    max_results: int = Field(default=5, ge=1, le=10)


class ResearchResponse(BaseModel):
    pages: List[Dict[str, Any]]
    synthesis: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    model: str
    base_url: str
    web_enabled: bool
    frontend_enabled: bool
    submodules: Dict[str, bool]
    agents_available: bool = False


class NodeTrace(BaseModel):
    node: str
    duration: float


class ToolSchema(BaseModel):
    name: str
    description: str
    args_schema: Dict[str, Any]


class ToolResult(BaseModel):
    tool: str
    data: Dict[str, Any]


class MemoryQueryRequest(BaseModel):
    query: str
    k: int = Field(default=3, ge=1, le=10)


class MemorySearchResponse(BaseModel):
    episodes: List[Dict[str, Any]]


class AgentsChatRequest(BaseModel):
    prompt: str


class AgentsChatResponse(BaseModel):
    reply: str
    raw_items: List[Dict[str, Any]] = Field(default_factory=list)


class ReflectionResponse(BaseModel):
    notes: str
    episode_count: int
