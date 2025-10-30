"""Prompt templates and JSON tool-calling instructions."""
from __future__ import annotations

from textwrap import dedent

BASE_SYSTEM_PROMPT = dedent(
    """
    You are lam-agent-unified, a local-first research assistant.
    Always prioritize factual accuracy, cite sources when available, and
    never fabricate URLs or references. When you need to call a tool,
    return ONLY a JSON object with fields "tool" and "args" matching the
    provided JSON schema. When you answer directly, respond in plain text.
    """
).strip()

TOOL_INSTRUCTIONS = dedent(
    """
    Tool usage contract:
    {
      "tool": "<tool_name>",
      "args": { ... } // must match the provided schema exactly
    }
    Do not wrap the JSON inside code fences. If validation fails, you will
    receive guidance and must retry with corrected JSON.
    """
).strip()

EXAMPLE_TOOL_CALL = {
    "tool": "web_search_ddg",
    "args": {"query": "history of langchain", "max_results": 3},
}

DEFAULT_SYSTEM_PROMPT = f"{BASE_SYSTEM_PROMPT}\n\n{TOOL_INSTRUCTIONS}"


def build_messages(user_message: str, mode: str) -> list[dict]:
    return [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT + f"\nActive mode: {mode}."},
        {"role": "user", "content": user_message},
    ]
