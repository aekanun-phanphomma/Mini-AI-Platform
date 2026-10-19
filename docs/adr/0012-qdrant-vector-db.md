# ADR-0012: ใช้ Qdrant เป็น vector database

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 2

## บริบท
RAG ต้องเก็บ embedding ของเอกสาร แล้วค้นหา chunk ที่ใกล้กับคำถามที่สุด (nearest neighbor)
ต้องรันบนเครื่องได้, ฟรี และมี API ที่ชัดเจน

## การตัดสินใจ
- ใช้ **Qdrant** (`qdrant/qdrant:v1.12.4`) ใช้ distance แบบ cosine
- payload เก็บ `source` + `text` เพื่อแสดงแหล่งที่มาของคำตอบ
- point ID ได้จาก `uuid5(source#index)` (deterministic) ทำให้ ingest ซ้ำแล้วทับของเดิม ไม่เกิดข้อมูลซ้ำ
- บน k8s รันเป็น StatefulSet + PVC

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Qdrant (เลือก) | เบา, เร็ว, มี dashboard, filter ด้วย payload ได้, client ดี | ต้องดูแลเป็น service แยก |
| pgvector | ใช้ Postgres ที่มีอยู่แล้ว, ใช้ SQL join กับข้อมูลอื่นได้ | ต้อง tune index (HNSW/IVF) เอง |
| Chroma | ง่ายที่สุด | ไม่เหมาะกับ production ขนาดใหญ่ |
| Pinecone / Vectorize | managed | ไม่ได้เรียนการดูแล stateful service (Vectorize ใช้ใน phase 5) |

## ผลที่ตามมา
- ✅ เปิดดูข้อมูลได้ที่ `http://localhost:6333/dashboard`
- ⚠️ ถ้ามีข้อมูล relational อยู่แล้ว pgvector อาจเป็นตัวเลือกที่ง่ายกว่า (ลดจำนวนระบบที่ต้องดูแล)
- 🔁 แบบฝึกหัด: เพิ่ม hybrid search (BM25 + vector) แล้ววัดผลด้วย eval set ว่าดีขึ้นไหม
