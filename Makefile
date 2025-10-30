.PHONY: install run cli test rag-index rag-query research frontend docker-build docker-up docker-down traces-clean

install:
	python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	PYTHONPATH=src uvicorn app.server:app --host 0.0.0.0 --port $${PORT:-8000}

cli:
	PYTHONPATH=src python -m app.cli $(ARGS)

test:
	PYTHONPATH=src pytest -q

rag-index:
	PYTHONPATH=src python -m app.cli rag-index --dir $${DIR:-data/docs}

rag-query:
	PYTHONPATH=src python -m app.cli rag-query --question "$${QUESTION}" --k $${K:-4}

research:
	PYTHONPATH=src python -m app.cli research --query "$${QUERY}" --depth $${DEPTH:-1} --max-results $${MAX:-5}

frontend:
	cd frontend && npm install && npm run dev

docker-build:
	docker build -t lam-agent-unified .

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

traces-clean:
	rm -f data/traces/*.jsonl
