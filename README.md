# AI Platform Lab

แล็บสำหรับเรียน **AI Infra / MLOps / DevOps / Platform Engineering** แบบลงมือทำจริง ใช้เครื่องมือฟรีทั้งหมดและทำได้บนโน้ตบุ๊ก Windows เครื่องเดียว

หลักของแล็บนี้คือ **ทุกอย่างเป็น code** ตั้งแต่การตั้งเครื่อง (WSL, Docker, CLI tools) ไปจนถึง data pipeline, model, Kubernetes, CI/CD และ monitoring
ถ้าเครื่องพังต้องสร้างใหม่ได้ด้วยคำสั่งไม่กี่คำสั่ง

```
[Data] → [Pipeline] → [Train / Embed] → [Registry] → [Serve API] → [Monitor]
   ↑                                                                 │
   └──────────────────── drift → retrain ←───────────────────────────┘
          ทั้งหมดรันบน Kubernetes (k3d) + deploy แบบ GitOps (Argo CD)
```

## Roadmap

| Phase | หัวข้อ | สิ่งที่ได้ | คู่มือ |
|---|---|---|---|
| 0 | Workstation as Code | WSL2 + Docker + CLI tools ติดตั้งด้วย PowerShell + Ansible | [phase-0](docs/phases/phase-0-workstation.md) |
| 1 | Data & ML | DVC + S3 (SeaweedFS) + MLflow, pipeline เทรน classifier | [phase-1](docs/phases/phase-1-data-ml.md) |
| 2 | LLM & RAG | Ollama + Qdrant + FastAPI, evaluation set | [phase-2](docs/phases/phase-2-llm-rag.md) |
| 3 | Platform | k3d, Helm, OpenTofu, Argo CD, GitHub Actions | [phase-3](docs/phases/phase-3-platform.md) |
| 4 | Observability & MLOps loop | Prometheus/Grafana, drift detection, Prefect retrain, k6 + HPA | [phase-4](docs/phases/phase-4-observability.md) |
| 5 | Edge / Cloud | Cloudflare Workers AI + Vectorize เทียบกับ self-host | [phase-5](docs/phases/phase-5-cloud.md) |

การตัดสินใจทุกข้อมีเหตุผลเขียนไว้ใน **[docs/adr](docs/adr/README.md)** ควรอ่าน ADR ของ phase นั้นก่อนลงมือ

## โครงสร้าง repo

```
Mini-AI-Platform/
├── bootstrap/            # Phase 0: Windows (PowerShell) + WSL (Ansible)
├── phase-1-data-ml/      # docker-compose (S3 + MLflow), DVC pipeline, training code
├── apps/rag-api/         # RAG service (ใช้ร่วมกันใน phase 2-4)
├── phase-2-llm-rag/      # docker-compose (Ollama + Qdrant), sample docs, eval
├── phase-3-platform/     # k3d config, Helm charts, OpenTofu bootstrap
├── gitops/apps/          # Argo CD Applications (Git = source of truth)
├── phase-4-observability/# monitoring app, drift, Prefect flow, k6
├── phase-5-cloud/        # Cloudflare Worker (rag-edge)
├── .github/workflows/    # CI/CD
└── docs/                 # ADR + คู่มือแต่ละ phase
```

## Quick start

```powershell
# 1) Windows PowerShell (Run as Administrator)
Set-ExecutionPolicy -Scope Process Bypass
.\bootstrap\windows\setup-wsl.ps1
```

```bash
# 2) ใน Ubuntu (WSL): clone repo มาไว้ใน filesystem ของ Linux (ดู ADR-0003)
mkdir -p ~/code && cd ~/code
git clone https://github.com/aekanun-phanphomma/Mini-AI-Platform.git && cd Mini-AI-Platform
./bootstrap/bootstrap.sh
```

จากนั้นทำตามคู่มือ phase 1 → 5 ตามลำดับ

## สเปกเครื่องที่แนะนำ

- RAM 16GB ขึ้นไป (ให้ WSL ใช้ 10-12GB), disk ว่าง 40GB
- ไม่ต้องมี GPU เพราะใช้โมเดลขนาดเล็ก (≤ 3B) ที่รันบน CPU ได้ (ADR-0011)

## กติกาของแล็บ

1. **ห้ามคลิกสร้างของผ่าน UI** ถ้าทำได้ด้วย code ทุกอย่างต้องอยู่ใน Git
2. **ทุกครั้งที่เปลี่ยนเครื่องมือหรือแนวทาง ให้เขียน ADR ใหม่** ห้ามแก้ ADR เก่า ให้ทำเครื่องหมาย superseded แทน
3. **ทำให้มันพังก่อนแล้วค่อยแก้** แต่ละ phase มีแบบฝึกหัด "Break it" เพราะการเรียน debug คือส่วนที่มีค่าที่สุดของงานนี้
