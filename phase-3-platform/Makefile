.RECIPEPREFIX = >
.DEFAULT_GOAL := help
SHELL := /bin/bash
CLUSTER := ailab
ROOT := $(abspath ..)

.PHONY: help cluster-up cluster-down image set-repo bootstrap destroy argocd-password lint render ingest eval status

help:  ## แสดงคำสั่งทั้งหมด
> @grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

cluster-up:  ## สร้าง k3d cluster
> k3d cluster create --config k3d/cluster.yaml
> kubectl get nodes -o wide

cluster-down:  ## ลบ cluster ทั้งหมด
> k3d cluster delete $(CLUSTER)

image:  ## build rag-api แล้ว import เข้า cluster (ใช้ก่อนตั้ง CI)
> docker build -t rag-api:dev $(ROOT)/apps/rag-api
> k3d image import rag-api:dev -c $(CLUSTER)

set-repo:  ## ใส่ URL ของ repo: make set-repo REPO=https://github.com/aekanun-phanphomma/Mini-AI-Platform.git
> @test -n "$(REPO)" || (echo "usage: make set-repo REPO=https://github.com/aekanun-phanphomma/Mini-AI-Platform.git" && exit 1)
> sed -i "s#REPO_URL#$(REPO)#g" $(ROOT)/gitops/apps/*.yaml
> echo 'repo_url = "$(REPO)"' > infra/terraform.tfvars
> @echo "แล้ว git commit + push ก่อน bootstrap (Argo CD อ่านจาก GitHub ไม่ได้อ่านจากเครื่อง)"

bootstrap:  ## OpenTofu: ติดตั้ง Argo CD + root app
> cd infra && tofu init && tofu apply
> @echo "Argo CD: http://argocd.localhost:8080  (user: admin, pass: make argocd-password)"

destroy:
> cd infra && tofu destroy

argocd-password:
> @kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo

lint:  ## ตรวจ chart + tofu (เหมือนใน CI)
> helm lint charts/ai-deps charts/rag-api -f charts/rag-api/values-lab.yaml
> cd infra && tofu fmt -check && tofu init -backend=false -input=false >/dev/null && tofu validate

render:  ## ดู manifest ที่ Helm จะสร้าง (debug template)
> helm template rag-api charts/rag-api -f charts/rag-api/values-lab.yaml

status:  ## ดูสถานะทุกอย่าง
> kubectl -n argocd get applications
> kubectl -n ai get pods,svc,ingress,pvc

ingest:  ## ส่งเอกสารเข้า rag-api ใน cluster
> python3 $(ROOT)/phase-2-llm-rag/scripts/ingest.py --url http://localhost:8080 --host rag.localhost

eval:  ## รัน eval กับ rag-api ใน cluster
> python3 $(ROOT)/phase-2-llm-rag/eval/run_eval.py --url http://localhost:8080 --host rag.localhost
