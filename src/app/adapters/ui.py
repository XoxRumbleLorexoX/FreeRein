"""UI adapter exposing CopilotKit-inspired capabilities."""
from __future__ import annotations

import importlib
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from app.config import settings


class AbstractUIBridge(ABC):
    @abstractmethod
    def render_chat_panel(self) -> Dict[str, Any]: ...


class CopilotKitAdapter(AbstractUIBridge):
    def __init__(self) -> None:
        self._external_available = self._attempt_import()

    def _attempt_import(self) -> bool:
        ext_path = Path("src_ext/copilotkit").resolve()
        if ext_path.exists():
            sys.path.insert(0, str(ext_path))
            try:
                importlib.import_module("packages")  # noqa: F401
                return True
            except Exception:
                return False
        return False

    def render_chat_panel(self) -> Dict[str, Any]:
        base_config = {
            "frontendEnabled": settings.frontend_enabled,
            "copilotkit": False,
            "message": "Local chat UI active.",
        }
        if self._external_available:
            base_config.update({"copilotkit": True, "message": "CopilotKit features enabled."})
        return base_config

    @property
    def external_enabled(self) -> bool:
        return self._external_available


def get_ui_adapter() -> CopilotKitAdapter:
    return CopilotKitAdapter()
