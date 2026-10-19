.RECIPEPREFIX = >
.DEFAULT_GOAL := help
SHELL := /bin/bash
ROOT := $(abspath ..)
W := cd rag-edge && npx wrangler

.PHONY: help install login index secret deploy ingest eval tail

help:  ## แสดงคำสั่งทั้งหมด
> @grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

install:  ## ติดตั้ง wrangler (เวอร์ชันตาม package.json)
> cd rag-edge && npm install

login:  ## login Cloudflare (เปิด browser)
> $(W) login

index:  ## สร้าง Vectorize index (ทำครั้งเดียว) dimension ต้องตรงกับ embedding model
> $(W) vectorize create rag-docs --dimensions=1024 --metric=cosine

secret:  ## ตั้ง INGEST_TOKEN (สุ่มให้แล้วเก็บไว้ใน .ingest-token ซึ่ง git ignore ไว้)
> test -f .ingest-token || openssl rand -hex 24 > .ingest-token
> cat .ingest-token | ($(W) secret put INGEST_TOKEN)

deploy:  ## deploy worker
> $(W) deploy

# URL=https://rag-edge.<subdomain>.workers.dev
ingest:  ## make ingest URL=https://rag-edge.<you>.workers.dev
> python3 $(ROOT)/phase-2-llm-rag/scripts/ingest.py --url $(URL) --token $$(cat .ingest-token)

eval:  ## เทียบคุณภาพกับ self-host ด้วย eval set เดียวกัน
> python3 $(ROOT)/phase-2-llm-rag/eval/run_eval.py --url $(URL)

tail:  ## ดู log แบบ real-time
> $(W) tail
