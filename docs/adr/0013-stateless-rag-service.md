# ADR-0013: RAG service แบบ stateless (FastAPI) ตั้งค่าด้วย environment variables

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 2 (deploy ใน 3, scale ใน 4)

## บริบท
service เดียวกันต้องรันได้ทั้งบน docker compose, Kubernetes และใน CI test
และต้อง scale เพิ่ม replica ได้ใน phase 4

## การตัดสินใจ
- **FastAPI** + `httpx` (async) + `qdrant-client` (async)
- **Stateless**: ไม่เก็บอะไรใน memory หรือ disk ของ process (เอกสารอยู่ใน Qdrant, โมเดลอยู่ใน Ollama)
- **Config ผ่าน env** ด้วย `pydantic-settings` ตามหลัก 12-factor
- endpoint: `/ingest`, `/ask`, `/healthz` (liveness), `/readyz` (readiness), `/metrics` (Prometheus)
- liveness ไม่เช็ก dependency เพราะถ้า Ollama ล่มแล้ว k8s restart rag-api ก็ไม่ได้ช่วยอะไร
- Docker image: `python:3.12-slim`, copy dependency layer ก่อน code, รันเป็น non-root (UID 10001), ใน k8s ใช้ `readOnlyRootFilesystem`

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| FastAPI เขียนเอง (เลือก) | เห็นทุกขั้นตอน, เบา, เพิ่ม metric ได้ตามต้องการ | ต้องเขียนเองมากกว่า |
| LangChain / LlamaIndex | มี component สำเร็จรูป | abstraction หนา ทำให้ debug ยากและไม่เห็นว่าข้างในทำอะไร |
| Open WebUI / AnythingLLM | มี UI ครบ | ไม่ได้เรียนการสร้าง service |

## ผลที่ตามมา
- ✅ image เดียวใช้ได้ทุก environment (build once, deploy many)
- ✅ เพิ่ม replica ได้ทันที ไม่ต้องใช้ sticky session
- ⚠️ ยังไม่มี auth / rate limit ห้ามเปิดออก internet
- 🔁 แบบฝึกหัด: เพิ่ม streaming response (SSE) แล้วดูว่า time-to-first-token ต่างจาก total latency อย่างไร
