# ADR-0023: ทำ RAG เวอร์ชัน serverless บน Cloudflare Workers AI + Vectorize เพื่อเปรียบเทียบ

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 5

## บริบท
phase 1-4 self-host ทุกอย่าง ซึ่งได้ความรู้เชิงลึกแต่ต้องดูแลเยอะ
ในงานจริงต้องเลือกบ่อยว่าจะ self-host หรือใช้ managed service จึงควรมีข้อมูลจริงไว้เทียบ

## การตัดสินใจ
- Worker `rag-edge` ใช้ API เดียวกับ rag-api (`/ingest`, `/ask`) จึงใช้ `ingest.py` และ `run_eval.py` ชุดเดิมได้
- Workers AI: `@cf/baai/bge-m3` (embedding 1024 มิติเท่ากับฝั่ง self-host) + LLM ที่ตั้งใน `vars`
- Vectorize index `rag-docs` (1024, cosine) สร้างด้วย `wrangler` ผ่าน Makefile
- ชื่อโมเดลอยู่ใน `wrangler.jsonc` ไม่ hardcode เพราะ catalog ของ Workers AI เปลี่ยนบ่อย
- `/ingest` ต้องใช้ bearer token (เก็บเป็น `wrangler secret`) เพราะ URL เป็น public

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Cloudflare (เลือก) | free tier ใช้ได้จริง, deploy ไม่กี่วินาที, ต่อยอดจาก Cloudflare-Lab ได้ | vendor lock-in, โมเดลจำกัดตาม catalog |
| Oracle Cloud Always Free (ARM VM) | ได้ k8s/VM จริงฟรี | สมัครยาก, ทรัพยากรจำกัด |
| AWS Bedrock / GCP Vertex | ระดับ enterprise | free tier ไม่พอ, มีโอกาสโดนเก็บเงิน |

## ผลที่ตามมา
- ✅ เทียบได้ด้วยตัวเลขจาก eval set ชุดเดียวกัน: คุณภาพ (hit rate), latency, ค่าใช้จ่าย และภาระในการดูแล
- ⚠️ เอกสารถูกส่งไปประมวลผลที่ Cloudflare ห้ามใช้กับข้อมูลจริงที่เป็นความลับ
- ⚠️ free tier มี quota รายวัน (neurons) ถ้ารัน load test จะหมดเร็ว
- 🔁 เขียนสรุปผลการเปรียบเทียบเป็น ADR ฉบับใหม่ ว่าถ้าเป็นงานจริงจะเลือกแบบไหนเพราะอะไร
