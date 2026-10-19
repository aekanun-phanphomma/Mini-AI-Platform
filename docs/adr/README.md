# Architecture Decision Records

ADR = บันทึกสั้น ๆ ว่า **ตัดสินใจอะไร เพราะอะไร และแลกกับอะไร**
เครื่องมือเปลี่ยนไปเรื่อย ๆ แต่เหตุผลเบื้องหลังการเลือกยังใช้ได้ และเป็นสิ่งที่สัมภาษณ์งาน Platform/MLOps ถามบ่อยที่สุด

วิธีใช้: อ่าน ADR ของ phase ก่อนลงมือ ถ้าจะเปลี่ยนการตัดสินใจ ให้เขียน ADR ใหม่ด้วย [template.md](template.md)
แล้วเปลี่ยนสถานะของ ADR เดิมเป็น `Superseded by ADR-XXXX` ห้ามแก้เนื้อหา ADR เดิม

| # | หัวข้อ | Phase |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | บันทึกการตัดสินใจด้วย ADR | - |
| [0002](0002-monorepo.md) | ใช้ monorepo เดียว | - |
| [0003](0003-wsl2-linux-filesystem.md) | WSL2 + เก็บ repo ใน Linux filesystem | 0 |
| [0004](0004-docker-engine-in-wsl.md) | ใช้ Docker Engine ใน WSL แทน Docker Desktop | 0 |
| [0005](0005-ansible-workstation.md) | ตั้งค่าเครื่องด้วย Ansible | 0 |
| [0006](0006-pin-tool-versions.md) | pin เวอร์ชันเครื่องมือ + versioned symlink | 0 |
| [0007](0007-uv-for-python.md) | ใช้ uv จัดการ Python | 0-4 |
| [0008](0008-dvc-s3-data-versioning.md) | DVC + S3 (SeaweedFS) สำหรับ version ข้อมูล | 1 |
| [0009](0009-mlflow-tracking-registry.md) | MLflow สำหรับ tracking และ model registry | 1 |
| [0010](0010-baseline-model-first.md) | เริ่มจาก baseline model + champion/challenger | 1 |
| [0011](0011-ollama-small-models.md) | Ollama + โมเดลเล็กที่รันบน CPU ได้ | 2 |
| [0012](0012-qdrant-vector-db.md) | Qdrant เป็น vector database | 2 |
| [0013](0013-stateless-rag-service.md) | RAG service แบบ stateless (12-factor) | 2 |
| [0014](0014-evaluation-before-tuning.md) | มี evaluation set ก่อนปรับจูน RAG | 2 |
| [0015](0015-k3d-local-kubernetes.md) | k3d สำหรับ Kubernetes บนเครื่อง | 3 |
| [0016](0016-helm-charts.md) | เขียน Helm chart เองสำหรับ app และ dependency | 3 |
| [0017](0017-opentofu-bootstrap-argocd-gitops.md) | OpenTofu bootstrap + Argo CD GitOps | 3 |
| [0018](0018-github-actions-ghcr.md) | GitHub Actions + GHCR + image tag write-back | 3 |
| [0019](0019-prometheus-grafana-ai-metrics.md) | Prometheus/Grafana + metric เฉพาะของ AI | 4 |
| [0020](0020-psi-drift-detection.md) | ตรวจ drift ด้วย PSI ที่เขียนเอง | 4 |
| [0021](0021-prefect-orchestration.md) | Prefect สำหรับ orchestration ของการ retrain | 4 |
| [0022](0022-hpa-load-testing.md) | HPA + load test ด้วย k6 | 4 |
| [0023](0023-cloudflare-edge-comparison.md) | Cloudflare Workers AI + Vectorize เป็นตัวเปรียบเทียบ | 5 |
| [0024](0024-secrets-handling.md) | การจัดการ secret | ทุก phase |
