"""Guardrails for validating tool calls and retrying generations."""
from __future__ import annotations

import json
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed

from .schemas import ToolCall

T = TypeVar("T", bound=BaseModel)


def parse_tool_call(raw: str) -> ToolCall:
    data = json.loads(raw)
    return ToolCall.model_validate(data)


def validate_with_schema(model: Type[T], data: dict) -> T:
    return model.model_validate(data)


def retry_generation(generate: Callable[[], str], validator: Callable[[str], ToolCall]) -> ToolCall:
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def _attempt() -> ToolCall:
        raw = generate()
        try:
            return validator(raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(f"Invalid tool call: {exc}")

    try:
        return _attempt()
    except RetryError as exc:  # pragma: no cover
        raise RuntimeError("Failed to obtain valid tool call after retries") from exc
