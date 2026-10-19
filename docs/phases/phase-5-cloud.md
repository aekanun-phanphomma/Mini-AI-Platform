# Phase 5 — Edge / Managed: Cloudflare Workers AI + Vectorize

**เป้าหมาย:** ทำ RAG แบบเดียวกันด้วย managed service แล้วเทียบกับ self-host ด้วยตัวเลข
**ADR:** [0023](../adr/0023-cloudflare-edge-comparison.md) · [0024](../adr/0024-secrets-handling.md)
**เวลา:** 2-4 วัน
**ต้องมี:** บัญชี Cloudflare (ฟรี)

## ขั้นตอน
```bash
cd ~/code/Mini-AI-Platform/phase-5-cloud
make install
make login           # เปิด URL ใน browser ของ Windows แล้วอนุญาต
make index           # Vectorize: rag-docs (1024 dims, cosine)
npx --prefix rag-edge wrangler ai models --search bge   # ตรวจว่าโมเดลใน wrangler.jsonc ยังมีอยู่
make secret          # สุ่ม INGEST_TOKEN → wrangler secret
make deploy          # ได้ URL https://rag-edge.<subdomain>.workers.dev
make ingest URL=https://rag-edge.<subdomain>.workers.dev
make eval   URL=https://rag-edge.<subdomain>.workers.dev
```
> Vectorize ทำ index แบบ async ถ้า eval ทันทีหลัง ingest แล้วค้นไม่เจอ ให้รอ 10-30 วินาที

## 📊 ตารางเปรียบเทียบ (กรอกเอง)
| | self-host (k3d) | Cloudflare |
|---|---|---|
| retrieval_hit_rate | | |
| answer_hit_rate | | |
| latency p50 / p95 | | |
| ค่าใช้จ่าย / 1,000 คำถาม | ไฟฟ้า + เครื่อง | ดู dashboard (neurons) |
| เวลาตั้งค่าครั้งแรก | | |
| สิ่งที่ต้องดูแลเอง | | |
| ข้อมูลออกนอกเครื่องไหม | | |

จากนั้นเขียน **ADR-0025** สรุปว่าถ้าเป็นงานจริงจะเลือกแบบไหน เพราะอะไร (เช่น ข้อมูลลับ → self-host, ต้อง scale ทั่วโลก → edge, หรือ hybrid)

## 💥 Break it
1. `/ingest` โดยไม่ใส่ token ต้องได้ 401
2. `make tail` แล้วยิงคำถามยาวมาก ๆ ดู error และ log
3. สร้าง index ใหม่ที่ 768 dims แล้วชี้ binding ไป ดูว่า upsert พังอย่างไร (dimension mismatch เหมือนใน phase 2)

## ต่อยอด
- เก็บเอกสารต้นฉบับใน **R2** แล้วใช้ Queue สั่ง ingest อัตโนมัติเมื่อมีไฟล์ใหม่
- ใช้ **AI Gateway** ทำ cache + rate limit + logging ของการเรียก LLM
- เขียน Cloudflare resource ด้วย Terraform provider `cloudflare/cloudflare` แทนการใช้ wrangler CLI
