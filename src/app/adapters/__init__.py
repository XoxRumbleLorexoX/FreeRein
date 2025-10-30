"""Adapter layer for optional integrations."""
from .agents import AGENTS_AVAILABLE, OllamaAgentsAdapter, get_agents_adapter
from .orchestrator import AbstractOrchestrator, LangGraphAdapter, get_orchestrator
from .research import AbstractResearch, DeerFlowAdapter, get_research_adapter
from .ui import AbstractUIBridge, CopilotKitAdapter, get_ui_adapter

__all__ = [
    "AbstractOrchestrator",
    "LangGraphAdapter",
    "get_orchestrator",
    "AbstractResearch",
    "DeerFlowAdapter",
    "get_research_adapter",
    "AbstractUIBridge",
    "CopilotKitAdapter",
    "get_ui_adapter",
    "OllamaAgentsAdapter",
    "get_agents_adapter",
    "AGENTS_AVAILABLE",
]
