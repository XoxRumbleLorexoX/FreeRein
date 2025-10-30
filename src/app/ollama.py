"""Thin HTTP client around the Ollama REST interface."""
from __future__ import annotations

import json
from typing import Any, Dict, Generator, Iterable

import httpx
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from .config import settings

DEFAULT_TIMEOUT = 60


class OllamaError(RuntimeError):
    """Raised when the Ollama backend returns an error."""


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self._client = httpx.Client(timeout=DEFAULT_TIMEOUT)

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - network failure details
            raise OllamaError(f"Ollama request failed: {exc}") from exc

    def _payload(self, **overrides: Any) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "options": {
                "temperature": settings.temperature,
                "num_ctx": settings.num_ctx,
            },
        }
        payload.update(overrides)
        return payload

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def _post(self, path: str, json_payload: Dict[str, Any], stream: bool = False) -> httpx.Response:
        url = f"{self.base_url}{path}"
        if stream:
            request = self._client.build_request("POST", url, json=json_payload)
            response = self._client.send(request, stream=True)
        else:
            response = self._client.post(url, json=json_payload)
        self._raise_for_status(response)
        return response

    def generate(self, messages: Iterable[Dict[str, Any]], stream: bool = False) -> Any:
        payload = self._payload(messages=list(messages), stream=stream)
        try:
            response = self._post("/api/chat", payload, stream=stream)
        except RetryError as exc:  # pragma: no cover - network
            raise OllamaError("Exceeded retries when contacting Ollama") from exc

        if stream:
            return self._streaming_chunks(response)
        return response.json()

    def _streaming_chunks(self, response: httpx.Response) -> Generator[Dict[str, Any], None, None]:
        try:
            for line in response.iter_lines():
                if not line:
                    continue
                yield json.loads(line)
        finally:  # pragma: no branch
            response.close()


def get_client() -> OllamaClient:
    return OllamaClient()
