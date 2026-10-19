# ADR-0011: ใช้ Ollama serve โมเดลเล็กที่รันบน CPU ได้ ทั้ง LLM และ embedding

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 2

## บริบท
ต้องมี LLM และ embedding model ที่รันบนโน้ตบุ๊กไม่มี GPU, ฟรี, รองรับภาษาไทย และเรียกผ่าน HTTP API ได้
เป้าหมายคือเข้าใจ inference serving (memory, latency, cold start, throughput) มากกว่าได้คำตอบที่ฉลาดที่สุด

## การตัดสินใจ
- **Ollama** เป็น inference server ตัวเดียวสำหรับทั้ง chat และ embedding
- chat: `qwen2.5:1.5b` (quantized ~1GB, รองรับภาษาไทยพอใช้)
- embedding: `bge-m3` (multilingual, 1024 มิติ, รองรับภาษาไทยดี)
- ดึงโมเดลด้วย one-shot container (compose) หรือ Job (k8s) ไม่ดึงมือ
- `OLLAMA_KEEP_ALIVE=30m` เก็บโมเดลไว้ใน RAM เพื่อลด cold start

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Ollama (เลือก) | ติดตั้งง่าย, ใช้ GGUF quantized, รองรับทั้ง embed + chat | throughput ต่ำเมื่อมี request พร้อมกันหลายตัว |
| vLLM | throughput สูง (continuous batching, PagedAttention) | ต้องมี GPU |
| llama.cpp server | เบาที่สุด | ต้องจัดการไฟล์โมเดลเอง |
| OpenAI / Claude API | คุณภาพสูงสุด | เสียเงิน, ไม่ได้เรียน serving |
| sentence-transformers ใน rag-api | ไม่ต้องมี service เพิ่ม | image ใหญ่ (torch), แต่ละ replica โหลดโมเดลของตัวเอง |

## ผลที่ตามมา
- ✅ เห็นของจริงว่า LLM บน CPU ช้า (หลายวินาทีต่อคำตอบ) จึงเข้าใจว่าทำไม GPU และ batching สำคัญ
- ✅ เปลี่ยนโมเดลได้ด้วย env (`CHAT_MODEL`) โดยไม่ต้องแก้ code
- ⚠️ โมเดล 1.5B ตอบผิดหรือแต่งข้อมูล (hallucinate) ได้ง่าย ต้องวัดด้วย eval (ADR-0014)
- ⚠️ ถ้าเปลี่ยน embedding model ต้องสร้าง collection ใหม่และ ingest ใหม่ทั้งหมด เพราะ vector จากคนละโมเดลเทียบกันไม่ได้
- 🔁 ถ้ามี GPU ให้ลอง vLLM + `Qwen2.5-7B-Instruct` แล้วเทียบ latency/throughput
