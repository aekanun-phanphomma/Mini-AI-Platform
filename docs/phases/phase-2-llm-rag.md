# Phase 2 — LLM & RAG

**เป้าหมาย:** RAG service ที่ตอบคำถามจากเอกสารภาษาไทย และวัดคุณภาพเป็นตัวเลขได้
**ADR:** [0011](../adr/0011-ollama-small-models.md) · [0012](../adr/0012-qdrant-vector-db.md) · [0013](../adr/0013-stateless-rag-service.md) · [0014](../adr/0014-evaluation-before-tuning.md)
**เวลา:** 1-2 สัปดาห์

## ภาพรวม
```
ingest:  .md → chunk (800 ตัวอักษร, overlap 150) → bge-m3 embed → Qdrant
ask:     question → embed → top-k search → prompt(context + question) → qwen2.5 → answer + sources
```
อ่าน code ตามลำดับนี้: `apps/rag-api/app/settings.py` → `rag.py` → `main.py` → `metrics.py`

## ขั้นตอน
```bash
cd ~/code/Mini-AI-Platform/phase-2-llm-rag
make up                 # ครั้งแรกโหลดโมเดล ~3GB: `make logs` ดูความคืบหน้า
make ingest             # {"documents": 3, "chunks": ...}
make ask Q="ลาพักร้อนได้กี่วัน"
make eval               # retrieval_hit_rate, answer_hit_rate, latency
make test               # unit test (ไม่ต้องใช้ Ollama)
```
เปิดดู: API docs http://localhost:8000/docs · Qdrant http://localhost:6333/dashboard · metrics http://localhost:8000/metrics

## ✅ Checkpoint
- `make eval` ผ่าน quality gate (retrieval ≥ 0.8, answer ≥ 0.6)
- คำถามเรื่องสัตว์เลี้ยงต้องได้คำตอบ "ไม่ทราบ" ถ้าโมเดลแต่งคำตอบขึ้นมา (hallucinate) ให้บันทึกไว้
- `make ingest` ซ้ำ 2 ครั้ง จำนวน point ใน Qdrant ต้องไม่เพิ่ม (deterministic ID)

## 🧪 การทดลอง (บันทึกผล eval ทุกครั้ง)
| ทดลอง | วิธี |
|---|---|
| chunk size | `docker compose down -v` แล้ว `CHUNK_SIZE=300 make up && make ingest eval` (ต้องล้าง collection เดิม) |
| top_k | `TOP_K=1 make up && make eval` เทียบกับ `TOP_K=8` |
| model | `CHAT_MODEL=qwen2.5:3b make up` (ช้ากว่า แต่ตอบดีกว่าไหม?) |
| prompt | แก้ `SYSTEM_PROMPT` ใน `rag.py` |

## 💥 Break it
1. `docker compose stop ollama` → `/ask` ต้องได้ 502 (ไม่ใช่ 500 หรือค้าง) และ `/readyz` ต้องได้ 503
2. เปลี่ยน `EMBED_MODEL` เป็น `nomic-embed-text` (768 มิติ) โดยไม่เปลี่ยน `EMBED_DIM` แล้วดูว่าพังอย่างไร และทำไม
3. ใส่เอกสารที่ขัดแย้งกับเอกสารเดิม (เช่น ลาพักร้อน 15 วัน) แล้วดูว่าโมเดลตอบอะไร

## 🧠 ต้องตอบได้
- ทำไมตัด chunk ตามจำนวนตัวอักษร ไม่ตัดตามคำ (สำหรับภาษาไทย)?
- retrieval ถูกแต่คำตอบผิด กับ retrieval ผิด ต้องแก้ต่างกันอย่างไร?
- ทำไม liveness ไม่เช็ก Ollama แต่ readiness เช็ก?
