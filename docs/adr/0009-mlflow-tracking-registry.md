# ADR-0009: ใช้ MLflow สำหรับ experiment tracking และ model registry

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 1

## บริบท
แต่ละครั้งที่เทรนต้องรู้ว่าใช้ params อะไร ได้ metrics เท่าไหร่ มาจาก git commit ไหน
และโมเดลตัวไหนกำลังใช้งานอยู่ (champion) ถ้าบันทึกใน spreadsheet จะผิดพลาดง่ายและค้นย้อนหลังลำบาก

## การตัดสินใจ
- รัน MLflow server ด้วย docker compose โดย backend store = **Postgres** (metadata) และ artifact store = **S3** (bucket `mlflow`)
- ใช้ `--artifacts-destination` (proxied artifact): client อัปโหลดผ่าน MLflow server จึงไม่ต้องถือ S3 credential
- build image เองจาก `python:3.12-slim` แล้ว pin `mlflow==2.17.2` ให้ตรงกับ client (image ทางการไม่มี psycopg2/boto3)
- ใช้ **alias `champion`** แทน stage แบบเก่า (Staging/Production) ซึ่ง MLflow deprecate แล้ว

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| MLflow self-host (เลือก) | open source, เป็นมาตรฐานของวงการ, มี registry | ต้องดูแล server เอง |
| Weights & Biases | UI ดีมาก | SaaS, free tier มีข้อจำกัด |
| MLflow แบบ file store (`./mlruns`) | ไม่ต้องมี server | ใช้ร่วมกันหลายคนไม่ได้, ไม่เหมือน production |

## ผลที่ตามมา
- ✅ ทุก run มี tag `git_commit` จึงตามกลับไปหา code ได้ (lineage)
- ✅ consumer โหลดโมเดลด้วย `models:/news-classifier@champion` ได้โดยไม่ต้องรู้เลข version
- ⚠️ MLflow server ในแล็บไม่มี authentication ห้ามเปิดออก internet
- ⚠️ client กับ server ต้องใช้เวอร์ชันตรงกัน ไม่งั้น API อาจไม่เข้ากัน
