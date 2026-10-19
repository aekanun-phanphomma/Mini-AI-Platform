.RECIPEPREFIX = >
.DEFAULT_GOAL := help
SHELL := /bin/bash
ROOT := $(abspath ..)
VALUES := $(ROOT)/phase-3-platform/charts/rag-api/values-lab.yaml

.PHONY: help enable drift drift-shift flow flow-shift flow-serve prefect-ui loadtest hpa

help:  ## แสดงคำสั่งทั้งหมด
> @grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

enable:  ## เปิด monitoring + metrics + HPA ผ่าน GitOps (แก้ไฟล์ แล้วให้ commit/push เอง)
> cp gitops/monitoring.yaml $(ROOT)/gitops/apps/monitoring.yaml
> yq -i '.autoscaling.enabled = true | .metrics.serviceMonitor.enabled = true | .metrics.prometheusRule.enabled = true | .metrics.dashboard.enabled = true' $(VALUES)
> git -C $(ROOT) status --short
> @echo
> @echo "ขั้นต่อไป: git add -A && git commit -m 'phase 4: enable observability' && git push"
> @echo "Argo CD sync แล้ว (1-3 นาที) เปิด http://grafana.localhost:8080 (admin/admin) → Dashboards → RAG API"

drift:  ## ตรวจ drift: train vs test (ไม่ควร drift)
> uv run python drift/drift.py

drift-shift:  ## ตรวจ drift กับข้อมูลที่จำลองให้เปลี่ยน (ควร drift)
> uv run python drift/drift.py --simulate-shift; test $$? -eq 2 && echo "drift detected as expected"

flow:  ## รัน retrain flow ครั้งเดียว
> uv run python pipelines/retrain_flow.py

flow-shift:  ## รัน flow โดยจำลอง drift → ต้อง retrain
> uv run python pipelines/retrain_flow.py --simulate-shift

flow-serve:  ## รัน flow ตาม schedule (ตี 2 ทุกวัน)
> uv run python pipelines/retrain_flow.py --serve

prefect-ui:  ## Prefect UI ที่ http://localhost:4200
> uv run prefect server start

loadtest:  ## k6 load test กับ rag-api ใน cluster
> k6 run loadtest/k6.js

hpa:  ## ดู HPA แบบ real-time (เปิดอีก terminal ระหว่าง loadtest)
> kubectl -n ai get hpa -w
