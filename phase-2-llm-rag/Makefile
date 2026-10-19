.RECIPEPREFIX = >
.DEFAULT_GOAL := help
SHELL := /bin/bash
API ?= http://localhost:8000

.PHONY: help up down logs ingest ask eval test

help:  ## แสดงคำสั่งทั้งหมด
> @grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

up:  ## build rag-api + start Ollama/Qdrant (ครั้งแรกโหลดโมเดล ~3GB)
> docker compose up -d --build
> @echo "API docs : $(API)/docs"
> @echo "Qdrant   : http://localhost:6333/dashboard"

down:
> docker compose down

logs:
> docker compose logs -f --tail=100 rag-api ollama-pull

ingest:  ## ส่ง sample-docs เข้า vector DB
> python3 scripts/ingest.py --url $(API)

ask:  ## ถามคำถาม: make ask Q="ลาพักร้อนได้กี่วัน"
> curl -s $(API)/ask -H 'Content-Type: application/json' \
>   -d "$$(jq -n --arg q "$(Q)" '{question:$$q}')" | jq

eval:  ## รัน evaluation set
> python3 eval/run_eval.py --url $(API)

test:  ## unit test ของ rag-api
> cd ../apps/rag-api && uv venv -q && uv pip install -q -r pyproject.toml --extra dev \
>   && .venv/bin/ruff check . && .venv/bin/pytest -q
