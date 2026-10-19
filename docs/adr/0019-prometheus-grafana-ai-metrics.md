# ADR-0019: kube-prometheus-stack + metric เฉพาะของงาน AI

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 4

## บริบท
service AI ต้องดูมากกว่า CPU/RAM: ต้องรู้ว่าช้าที่ขั้นตอนไหน (embed / search / generate), ใช้ token ไปเท่าไหร่ (cost)
และคุณภาพของ retrieval ลดลงหรือเปล่า

## การตัดสินใจ
- ติดตั้ง **kube-prometheus-stack** (Prometheus Operator + Grafana + kube-state-metrics + node-exporter) ผ่าน Argo CD Application
  ปิด Alertmanager ในแล็บ และใช้ `ServerSideApply=true` เพราะ CRD ใหญ่เกินขนาดที่ client-side apply รับได้
- rag-api expose metric:
  - `rag_requests_total{endpoint,status}` → rate / error (RED)
  - `rag_stage_seconds{stage}` histogram → latency แยกตาม stage
  - `rag_llm_tokens_total{kind}` → token (ตัวแทนของ cost)
  - `rag_retrieval_top_score` → ใช้เป็นตัวแทนของคุณภาพ (ถ้าค่าตกแปลว่าคำถามไม่ตรงกับเอกสาร)
- ทั้ง ServiceMonitor, PrometheusRule (alert) และ Grafana dashboard (ConfigMap) อยู่ใน Helm chart ของ app เป็น code ทั้งหมด

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| kube-prometheus-stack (เลือก) | มาตรฐานของวงการ, ครบในชุดเดียว | กิน RAM ~1.5GB |
| Grafana Cloud free | ไม่ต้องดูแล | ส่งข้อมูลออกนอกเครื่อง, มี quota |
| Langfuse / OpenTelemetry tracing | เห็น prompt / trace ราย request | เป็นเรื่อง tracing ไม่ใช่ metrics (เหมาะเป็นขั้นต่อไป) |

## ผลที่ตามมา
- ✅ ตอบได้ด้วยข้อมูลว่า "p95 latency 90% มาจาก generate ไม่ใช่ search"
- ⚠️ ห้ามใส่ค่าที่มีได้ไม่จำกัดใน label (เช่น user_id, question) เพราะ cardinality จะสูงจน Prometheus ล่ม
- 🔁 ขั้นต่อไป: เพิ่ม OpenTelemetry tracing + Langfuse เพื่อดู prompt/response ราย request
