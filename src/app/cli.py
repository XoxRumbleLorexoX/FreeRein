"""CLI entrypoint using Typer."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from app import memory, rag, reflection
from app.adapters import AGENTS_AVAILABLE, get_agents_adapter, get_orchestrator, get_research_adapter
from app.config import settings

app = typer.Typer(name="lam-agent-unified")


@app.command()
def chat(message: str, mode: str = typer.Option("hybrid", help="offline|web|hybrid")) -> None:
    orchestrator = get_orchestrator()
    result = orchestrator.run(message, mode=mode)
    print(result["reply"])
    if result.get("sources"):
        print("[bold cyan]Sources:[/bold cyan]", result["sources"])


@app.command("rag-index")
def rag_index(dir: Path = typer.Option(settings.docs_dir, exists=True)) -> None:
    stats = rag.build_index(dir)
    print(f"Indexed {stats.documents_indexed} documents (dim={stats.dim}).")


@app.command("rag-query")
def rag_query(question: str, k: int = typer.Option(4, min=1, max=10)) -> None:
    results = rag.query_index(question, k=k)
    print(json.dumps(results, indent=2))


@app.command()
def research(query: str, depth: int = typer.Option(1, min=0, max=3), max_results: int = typer.Option(5, min=1, max=10)) -> None:
    adapter = get_research_adapter()
    plan = adapter.plan(query)
    print("Plan:", plan)
    search_results = adapter.search(query, k=max_results)
    urls = [item.get("href") for item in search_results if item.get("href")]
    pages = adapter.crawl(urls, depth=depth, max_pages=max_results)
    synthesis = adapter.synthesize(pages)
    print(json.dumps({"synthesis": synthesis, "pages": pages}, indent=2))


@app.command("print-config")
def print_config() -> None:
    data = settings.model_dump()
    print(json.dumps(data, indent=2, default=str))


@app.command("memory-search")
def memory_search(query: str, k: int = typer.Option(3, min=1, max=10)) -> None:
    hits = memory.search_memory(query, k=k)
    print(json.dumps(hits, indent=2, ensure_ascii=False))


@app.command("memory-list")
def memory_list(limit: int = typer.Option(5, min=1, max=50)) -> None:
    episodes = memory.load_recent(limit)
    print(json.dumps(episodes, indent=2, ensure_ascii=False))


@app.command("reflect")
def reflect(limit: int = typer.Option(5, min=1, max=20)) -> None:
    try:
        record = reflection.run_reflection(limit=limit)
    except RuntimeError as exc:
        typer.echo(f"[reflection] {exc}")
        raise typer.Exit(code=1)
    print(record["notes"])


@app.command("agents-chat")
def agents_chat(prompt: str) -> None:
    if not AGENTS_AVAILABLE:
        typer.echo("openai-agents is not installed. Install with `pip install openai-agents`.")
        raise typer.Exit(code=1)
    adapter = get_agents_adapter()
    result = adapter.run(prompt)
    print(result["reply"])


if __name__ == "__main__":
    app()
