# lam-agent-unified

Local-first research agent stack that keeps everything on your machine. You get orchestration, deep research flows, and an optional chat UI without touching hosted services.

---

## What you get
- Run fully offline, or blend local RAG with targeted web crawling when you enable it.
- FastAPI backend, Typer CLI, optional React UI, plus an openai-agents bridge that speaks Ollama.
- Episodic memory + reflection loops so the agent can build context over time.
- Built-in adapters for LangGraph, DeerFlow, and CopilotKit when their submodules are present.
- JSONL traces and cautious web tooling so you can inspect behaviour safely.

---

## Before you start
- Python 3.11
- [Ollama](https://ollama.com/download) running locally (`ollama serve`)
- `git`, `make`
- Optional for the UI: Node.js 18+

Once those are ready, pull a model:

```bash
ollama pull llama3:8b
```

---

## Quick start (5 steps)
1. Clone and create a virtual environment.
   ```bash
   git clone <your fork> lam-agent-unified
   cd lam-agent-unified
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the sample environment file and tweak if needed.
   ```bash
   cp .env.example .env
   ```
3. Start the API (force the standard asyncio loop so DuckDuckGo search works).
   ```bash
   PYTHONPATH=src uvicorn app.server:app --host 0.0.0.0 --port 8000 --loop asyncio
   ```
4. Visit `http://localhost:8000/docs` and try a `POST /chat` request.
5. (Optional) Run CLI commands in another terminal while the API is live.
   ```bash
   PYTHONPATH=src python -m app.cli chat "Summarise Lam Research" --mode offline
   ```

---

## Optional add-ons
- **Build a local RAG index** (populate `data/docs/` first):
  ```bash
  PYTHONPATH=src python -m app.cli rag-index --dir data/docs
  ```
- **Query the RAG index**:
  ```bash
  PYTHONPATH=src python -m app.cli rag-query "Key ideas" --k 4
  ```
- **React frontend**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  The UI talks to the running API and adapts if CopilotKit is missing.

- **Search episodic memory**:
  ```bash
  PYTHONPATH=src python -m app.cli memory-search "What did we answer about LangGraph last time?"
  ```
- **Trigger a self-review**:
  ```bash
  PYTHONPATH=src python -m app.cli reflect --limit 5
  ```
- **Drive the Agents SDK through Ollama**:
  ```bash
  PYTHONPATH=src python -m app.cli agents-chat "Draft a weekly research plan"
  ```

---

## Docker route
Prefer containers? Make sure Ollama runs on the host (reachable at `http://host.docker.internal:11434`), then:

```bash
make docker-up
# or
docker-compose up --build
```

The `./data` folder is volume mounted so traces and indexes persist.

---

## API & CLI at a glance
- `GET /health`
- `POST /chat {"message": "...", "mode": "offline|web|hybrid"}`
- `POST /rag/index {"dir": "optional/path"}`
- `POST /rag/query {"question": "...", "k": 4}`
- `POST /research {"query": "...", "depth": 1, "max_results": 5}`
- `POST /memory/search {"query": "...", "k": 3}`
- `POST /agents/chat {"prompt": "..."}` (requires `openai-agents`)
- `POST /reflection/run?limit=5`

Helpful CLI shortcuts:
```bash
PYTHONPATH=src python -m app.cli research "LangChain roadmap" --depth 1 --max-results 5
PYTHONPATH=src python -m app.cli print-config
PYTHONPATH=src python -m app.cli memory-list --limit 5
PYTHONPATH=src python -m app.cli agents-chat "Map out a crawl plan"
```

---

## Episodic memory & self-improvement
- Memory episodes live in `data/memory/episodic.faiss` + `episodes.json`; query them with `/memory/search` or `app.cli memory-search`.
- Every run appends to memory automatically and can be reflected on with `/reflection/run` or `app.cli reflect`.
- Reflections emit Markdown guidance into `data/memory/reflections.jsonl` so you can bake insights back into prompts or configs.

---

## Using openai-agents with Ollama
The repo ships with an Ollama-backed model provider for [openai-agents-python](https://github.com/openai/openai-agents-python).

1. Dependencies are pinned in `requirements.txt`; if you pulled updates run:
   ```bash
   pip install -r requirements.txt
   ```
2. From the CLI:
   ```bash
   PYTHONPATH=src python -m app.cli agents-chat "Outline a tooling upgrade plan"
   ```
3. From the API hit `POST /agents/chat` with `{"prompt": "..."}`. The health endpoint reports `agents_available: true` once the SDK is importable.

---

## Submodules & adapters
Everything works out of the box using bundled fallbacks. Pull upstream repos later if you need the full projects:

```bash
bash scripts/add_submodules.sh
bash scripts/update_submodules.sh
```

Remove them with `bash scripts/remove_submodules.sh`. The `/health` endpoint reports which adapters are active.

---

## Tracing and safety
- Requests generate JSONL traces in `data/traces/<request_id>.jsonl`. Clean them with `make traces-clean`.
- The crawler honours `robots.txt`, limits download size to 1 MB, and can be disabled via `.env` (`ENABLE_WEB=false`).

---

## Troubleshooting
| Issue | Fix |
| --- | --- |
| `Vector store not built` | Run `python -m app.cli rag-index` after adding docs. |
| Ollama errors | Ensure Ollama is running and the model (`OLLAMA_MODEL`) exists locally. |
| Missing submodules | Use `scripts/add_submodules.sh` or rely on the fallbacks. |
| Frontend empty | Set `FRONTEND_ENABLED=true` and start the backend before `npm run dev`. |

---

## Development tips
- Keep dependencies pinned in `requirements.txt` and `frontend/package.json`.
- Run `make test` for fast smoke tests (no live Ollama calls required).
- Adjust configs in `.env` and re-run the API.

---

## License
[MIT](./LICENSE)
