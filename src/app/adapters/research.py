"""Deep research adapter with optional DeerFlow integration."""
from __future__ import annotations

import importlib
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

from app import tools_web
from app.ollama import get_client
from app.prompting import build_messages
from app.config import settings


class AbstractResearch(ABC):
    @abstractmethod
    def plan(self, query: str) -> List[str]: ...

    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[Dict]: ...

    @abstractmethod
    def crawl(self, urls: List[str], depth: int = 1, max_pages: int = 8) -> List[Dict]: ...

    @abstractmethod
    def synthesize(self, pages: List[Dict]) -> Dict[str, str]: ...


class DeerFlowAdapter(AbstractResearch):
    def __init__(self) -> None:
        self._external_available = self._attempt_import()

    def _attempt_import(self) -> bool:
        ext_path = Path("src_ext/deer-flow").resolve()
        if ext_path.exists():
            sys.path.insert(0, str(ext_path))
            try:
                importlib.import_module("deerflow")  # type: ignore  # noqa: F401
                return True
            except Exception:
                return False
        return False

    def plan(self, query: str) -> List[str]:
        if not settings.enable_web:
            return []
        return [query, f"background of {query}", f"latest updates on {query}"]

    def search(self, query: str, k: int = 5) -> List[Dict]:
        return tools_web.web_search_ddg(query, max_results=k)

    def crawl(self, urls: List[str], depth: int = 1, max_pages: int = 8) -> List[Dict]:
        if not urls:
            return []
        return tools_web.crawl(urls, depth=depth, max_pages=max_pages)

    def synthesize(self, pages: List[Dict]) -> Dict[str, str]:
        if not pages:
            return {"summary": "No web pages retrieved.", "sources": []}
        client = get_client()
        content = "\n\n".join(f"Source: {page.get('url')}\n{page.get('text', '')[:800]}" for page in pages)
        messages = [
            {"role": "system", "content": "Summarize the findings with citations."},
            {"role": "user", "content": content},
        ]
        response = client.generate(messages, stream=False)
        reply = response.get("message", {}).get("content", "")
        return {"summary": reply, "sources": [page.get("url") for page in pages]}

    @property
    def external_enabled(self) -> bool:
        return self._external_available


def get_research_adapter() -> DeerFlowAdapter:
    return DeerFlowAdapter()
