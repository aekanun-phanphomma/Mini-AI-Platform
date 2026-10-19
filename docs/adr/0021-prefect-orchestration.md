# ADR-0021: ใช้ Prefect ทำ orchestration ของวงจร drift → retrain

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 4

## บริบท
ต้องรัน "ตรวจ drift → ถ้า drift ให้ retrain → push artifact" ตาม schedule มี retry เมื่อ network ล้ม
และดูประวัติการรันได้ ถ้าใช้ cron + bash จะไม่มี retry, log และ UI

## การตัดสินใจ
- ใช้ **Prefect 3** เขียน flow เป็น Python ธรรมดา (`@flow`, `@task(retries=...)`)
- task เรียกเครื่องมือเดิม (`drift.py`, `dvc repro`, `dvc push`) ไม่เขียน logic ซ้ำ
- รันครั้งเดียว (`make flow`) หรือ schedule ด้วย `flow.serve(cron="0 2 * * *")`
- การ promote โมเดลยังเป็นหน้าที่ของ `train.py` (quality gate + champion/challenger) flow ไม่ได้ตัดสินเอง

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Prefect (เลือก) | Python ล้วน, รันได้โดยไม่ต้องมี server, มี UI | concept เฉพาะของ Prefect (deployment, work pool) |
| Airflow | มาตรฐานองค์กร | หนัก (scheduler + webserver + DB), DAG ไม่ใช่ Python ธรรมดา |
| Argo Workflows / Kubeflow Pipelines | รันบน k8s ตรง ๆ | ซับซ้อน, กิน resource |
| cron + bash | ง่าย | ไม่มี retry/observability |

## ผลที่ตามมา
- ✅ เห็นวงจร MLOps ครบ: monitor → detect → retrain → gate → register
- ⚠️ ในแล็บ retrain ใช้ข้อมูลเดิม จึงไม่ได้โมเดลที่ดีขึ้น ส่วนนี้ใช้สาธิตว่าระบบต่อกันอย่างไร
- 🔁 แบบฝึกหัด: ย้าย flow ไปรันเป็น CronJob บน k3d (ต้องคิดเรื่อง credential ของ S3/MLflow ใน cluster)
