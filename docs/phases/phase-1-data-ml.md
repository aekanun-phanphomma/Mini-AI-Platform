# Phase 1 — Data & ML Foundations

**เป้าหมาย:** pipeline ที่ reproduce ได้ตั้งแต่ดึงข้อมูลจนได้โมเดลใน registry
**ADR:** [0008](../adr/0008-dvc-s3-data-versioning.md) · [0009](../adr/0009-mlflow-tracking-registry.md) · [0010](../adr/0010-baseline-model-first.md) · [0024](../adr/0024-secrets-handling.md)
**เวลา:** 1-2 สัปดาห์ (รวมการทดลองและอ่านเพิ่ม)

## ภาพรวม
```
params.yaml ─┐
             ▼
 ingest ──▶ prepare ──▶ train ──▶ MLflow (params, metrics, model)
   │           │          │         └─▶ Registry: news-classifier@champion
   ▼           ▼          ▼
         DVC cache ──push──▶ S3 (SeaweedFS) bucket "dvc"
 Git เก็บ: code, dvc.yaml, dvc.lock (hash), params.yaml, metrics.json
```

## ขั้นตอน
```bash
cd ~/code/Mini-AI-Platform/phase-1-data-ml
make up            # S3 + Postgres + MLflow
docker compose ps  # รอจน mlflow เป็น healthy
make dvc-init      # ทำครั้งเดียว
git add .dvc .dvcignore && git commit -m "phase1: init dvc"
make pipeline      # uv sync + dvc repro
make push          # dvc push → S3
git add dvc.lock metrics.json uv.lock && git commit -m "phase1: baseline model"
```
เปิดดู:
- MLflow: http://localhost:5000 → experiment `news-classifier` → ดู params/metrics/artifacts และแท็บ Models
- S3 master: http://localhost:9333

## ✅ Checkpoint
```bash
dvc repro              # รันซ้ำ: ทุก stage ต้องขึ้น "didn't change, skipping"
dvc dag                # เห็น ingest → prepare → train
make exp               # ลอง C หลายค่า เทียบใน `dvc exp show`
```
MLflow ต้องมี registered model `news-classifier` ที่มี alias `champion`

## 💥 Break it
1. **ข้อมูลหาย:** `rm -rf data models .dvc/cache` แล้ว `dvc pull` ต้องได้ทุกอย่างกลับมา
2. **Reproducibility:** แก้ `train.C` ใน `params.yaml` → `dvc repro` ต้องรันใหม่เฉพาะ stage train
3. **Quality gate:** ตั้ง `register_threshold: 0.99` → run ต้องไม่ถูก register
4. **Time travel:** `git checkout HEAD~1 -- dvc.lock && dvc checkout` ได้โมเดลเวอร์ชันก่อนหน้า

## 🧠 ต้องตอบได้
- Git เก็บอะไร และ DVC เก็บอะไร? ถ้าลบ S3 bucket จะเสียอะไร?
- ทำไม client ไม่ต้องมี S3 credential ตอน log model ใน MLflow?
- "registered" กับ "champion" ต่างกันอย่างไร? ใครควรตัดสินว่าโมเดลไหนได้เป็น champion?

## 🔧 Troubleshooting
| อาการ | วิธีแก้ |
|---|---|
| `dvc push` → 403 / signature | ตรวจว่า `.dvc/config.local` ตรงกับ `.env` (`make dvc-init` ใหม่) |
| MLflow connection refused | `docker compose logs mlflow` (ส่วนใหญ่รอ Postgres หรือ s3-init) |
| `load_dataset` ช้า/ล้ม | ต้องมี internet ครั้งแรก หลังจากนั้นใช้ cache ใน `~/.cache/huggingface` |
