"""Adapter connecting openai-agents to the local Ollama runtime."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict, Iterable, List, Optional

from app.config import settings
from app.logging import tracer
from app.ollama import OllamaClient, get_client

try:  # pragma: no cover - optional dependency
    from agents import Agent, ModelSettings, RunConfig, Runner
    from agents.items import ModelResponse, TResponseInputItem
    from agents.models.interface import Model, ModelProvider, ModelTracing
    from agents.tool import Tool
    from agents.usage import Usage
    from openai.types.responses import ResponseOutputMessage, ResponseOutputText

    AGENTS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Agent = None
    ModelSettings = None
    RunConfig = None
    Runner = None
    Model = object  # type: ignore
    ModelProvider = object  # type: ignore
    ModelResponse = object  # type: ignore
    Tool = object  # type: ignore
    Usage = object  # type: ignore
    ResponseOutputMessage = None
    ResponseOutputText = None
    ModelTracing = object  # type: ignore
    TResponseInputItem = Dict[str, Any]
    AGENTS_AVAILABLE = False


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _prepare_messages(
    system_instructions: str | None,
    input_items: str | List[TResponseInputItem],
) -> List[Dict[str, str]]:
    """Convert agents input items into an Ollama-friendly message list."""
    messages: List[Dict[str, str]] = []
    if system_instructions:
        messages.append({"role": "system", "content": system_instructions})

    if isinstance(input_items, str):
        messages.append({"role": "user", "content": input_items})
        return messages

    for item in input_items:
        role = item.get("role", "user")
        content = item.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            text_parts: List[str] = []
            for chunk in content:
                if isinstance(chunk, dict) and chunk.get("type") in {"input_text", "output_text"}:
                    text_parts.append(chunk.get("text", ""))
                elif isinstance(chunk, dict) and "text" in chunk:
                    text_parts.append(chunk["text"])
            text = "\n".join(filter(None, text_parts))
        else:
            text = json.dumps(content, ensure_ascii=False)
        messages.append({"role": role, "content": text})
    return messages


class OllamaAgentsModel(Model):  # type: ignore[misc]
    """Minimal Model implementation that routes calls to Ollama."""

    def __init__(self, client: Optional[OllamaClient] = None) -> None:
        self._client = client or get_client()

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | List[TResponseInputItem],
        model_settings: ModelSettings,
        tools: List[Tool],
        output_schema: Any,
        handoffs: List[Any],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any,
    ) -> ModelResponse:
        messages = _prepare_messages(system_instructions, input)
        response_payload = await asyncio.to_thread(self._client.generate, messages, False)
        reply = response_payload.get("message", {}).get("content", "")

        output_text = ResponseOutputText(
            text=reply,
            annotations=[],
            type="output_text",
        )
        output_message = ResponseOutputMessage(
            id=f"ollama-{uuid.uuid4().hex}",
            role="assistant",
            status="completed",
            type="message",
            content=[output_text],
        )
        usage = Usage(
            requests=1,
            input_tokens=_estimate_tokens(json.dumps(messages)),
            output_tokens=_estimate_tokens(reply),
            total_tokens=_estimate_tokens(json.dumps(messages)) + _estimate_tokens(reply),
        )
        return ModelResponse(output=[output_message], usage=usage, response_id=None)

    def stream_response(  # pragma: no cover - streaming pending
        self,
        system_instructions: str | None,
        input: str | List[TResponseInputItem],
        model_settings: ModelSettings,
        tools: List[Tool],
        output_schema: Any,
        handoffs: List[Any],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any,
    ):
        raise NotImplementedError("Streaming not yet supported for Ollama agents.")


class OllamaModelProvider(ModelProvider):  # type: ignore[misc]
    """Return a single Ollama-backed model irrespective of name."""

    def __init__(self, client: Optional[OllamaClient] = None) -> None:
        self._model = OllamaAgentsModel(client=client)

    def get_model(self, model_name: str | None) -> Model:
        return self._model


class OllamaAgentsAdapter:
    """High-level helper that exposes openai-agents with Ollama responses."""

    def __init__(self, instructions: Optional[str] = None) -> None:
        if not AGENTS_AVAILABLE:
            raise RuntimeError("openai-agents is not installed. Run `pip install openai-agents`.")
        self._provider = OllamaModelProvider()
        self._agent = Agent(
            name="ollama-agent",
            instructions=instructions
            or "You are a local agent running purely on Ollama. Be concise and cite tools when used.",
            model="ollama",
            model_settings=ModelSettings(temperature=settings.temperature),
        )
        self._run_config = RunConfig(model_provider=self._provider, model="ollama")

    def run(self, prompt: str) -> Dict[str, Any]:
        """Execute the configured agent synchronously and return structured output."""
        with tracer.span(component="agents", mode="ollama") as span_id:
            result = Runner.run_sync(self._agent, prompt, run_config=self._run_config)
            reply = result.final_output if isinstance(result.final_output, str) else str(result.final_output)
            tracer.append(span_id, {"event": "agents_result", "reply_length": len(reply)})
        return {
            "reply": reply,
            "raw_items": [
                item.raw_item.model_dump(exclude_none=True) if hasattr(item.raw_item, "model_dump") else item.raw_item
                for item in result.new_items
            ],
        }

    @property
    def external_enabled(self) -> bool:
        return True


def get_agents_adapter() -> OllamaAgentsAdapter:
    return OllamaAgentsAdapter()


__all__ = ["OllamaAgentsAdapter", "get_agents_adapter", "AGENTS_AVAILABLE"]
