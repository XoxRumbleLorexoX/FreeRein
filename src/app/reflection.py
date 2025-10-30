"""Background self-reflection utilities for the local agent."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from app import memory
from app.logging import tracer
from app.ollama import get_client

REFLECTION_LOG = Path("data/memory/reflections.jsonl")


def run_reflection(limit: int = 5) -> Dict[str, str]:
    """Generate improvement notes over recent episodes."""
    episodes = memory.load_recent(limit)
    if not episodes:
        raise RuntimeError("No memory episodes available to reflect on yet.")

    snippets: List[str] = []
    for episode in episodes:
        snippets.append(
            f"- Query: {episode.get('query')}\n  Answer: {episode.get('response')}\n  Mode: {episode.get('mode')}"
        )
    interactions = "\n".join(snippets)
    prompt = (
        "You are a critic reviewing an autonomous research assistant. "
        "Inspect the recent interactions and produce:\n"
        "1. A short bullet list of recurring issues.\n"
        "2. Concrete suggestions to improve future answers.\n"
        "3. Optional follow-up questions the agent should ask users.\n\n"
        "Interactions:\n"
        f"\"\"\"\n{interactions}\n\"\"\"\n"
        "Respond in Markdown with headings `Findings`, `Improvements`, and `Follow-ups`."
    )

    client = get_client()
    with tracer.span(component="reflection", mode="offline") as span_id:
        response = client.generate(
            [
                {"role": "system", "content": "You are a rigorous AI reviewer."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        notes = response.get("message", {}).get("content", "")
        tracer.append(span_id, {"event": "reflection_complete", "notes_length": len(notes)})

    record = {
        "timestamp": time.time(),
        "notes": notes,
        "episode_count": len(episodes),
    }
    REFLECTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REFLECTION_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


__all__ = ["run_reflection"]
