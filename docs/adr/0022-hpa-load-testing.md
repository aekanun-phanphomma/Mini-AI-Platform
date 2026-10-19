# ADR-0022: HPA ตาม CPU + load test ด้วย k6 เพื่อหาคอขวดจริง

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 4

## บริบท
ต้องรู้ว่าระบบรับโหลดได้เท่าไหร่และคอขวดอยู่ที่ไหน
มักเข้าใจกันว่าเปิด autoscaling แล้วจะเร็วขึ้นเอง แต่ใน RAG ส่วนที่หนักจริงคือ LLM ไม่ใช่ API

## การตัดสินใจ
- เปิด HPA ให้ rag-api (CPU 60%, 1-4 replicas, scale down stabilization 120s)
- ใช้ **k6** (`loadtest/k6.js`) ramp 1 → 6 VUs และกำหนด SLO ด้วย thresholds (error < 5%, p95 < 60s)
- ดู Grafana panel "rag-api replicas vs CPU" คู่กับ "Ollama CPU"
- ตั้งใจให้ HPA scale rag-api แล้ว latency **ไม่ลดลง** เพื่อให้เห็นว่าคอขวดอยู่ที่ Ollama (มี replica เดียวและใช้ CPU เต็ม)

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| HPA ตาม CPU (เลือก) | มีใน k8s อยู่แล้ว | CPU ไม่ใช่ตัวชี้วัดที่ดีสำหรับ API ที่ส่วนใหญ่รอ I/O |
| KEDA ตาม queue length / RPS | scale ตาม demand จริง | เพิ่ม component |
| Locust | เขียนด้วย Python | หนักกว่า k6 เมื่อใช้ VU จำนวนมาก |

## ผลที่ตามมา
- ✅ ได้บทเรียนว่า scale ส่วนที่ไม่ใช่คอขวดไม่ช่วยอะไร ต้องวัดก่อนแล้วค่อย scale
- ⚠️ เพิ่ม replica ของ Ollama บน CPU ตัวเดียวกันก็ไม่ช่วย เพราะแย่ง core เดียวกัน ทางแก้จริงคือ GPU, batching (vLLM), โมเดลเล็กลง หรือ cache คำตอบ
- 🔁 แบบฝึกหัด: เพิ่ม semantic cache (เก็บคำถามที่คล้ายกันใน Qdrant) แล้ววัดใหม่
