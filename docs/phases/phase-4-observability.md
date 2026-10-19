# Phase 4 — Observability & MLOps Loop

**เป้าหมาย:** เห็นสุขภาพของระบบ AI เป็นตัวเลข, ตรวจ drift แล้ว retrain อัตโนมัติ, หาคอขวดด้วย load test
**ADR:** [0019](../adr/0019-prometheus-grafana-ai-metrics.md) · [0020](../adr/0020-psi-drift-detection.md) · [0021](../adr/0021-prefect-orchestration.md) · [0022](../adr/0022-hpa-load-testing.md)
**เวลา:** 1-2 สัปดาห์

## ขั้นตอน

### 1. เปิด monitoring ผ่าน GitOps (ไม่ใช้ `helm install`)
```bash
cd ~/code/Mini-AI-Platform/phase-4-observability
make enable          # copy monitoring.yaml → gitops/apps/, เปิด flag ใน values-lab.yaml
git add -A && git commit -m "phase4: enable observability" && git push
```
รอ Argo sync (ประมาณ 3-5 นาที) จากนั้นเปิด:
- Grafana http://grafana.localhost:8080 (admin/admin) → Dashboards → **RAG API**
- Prometheus http://prometheus.localhost:8080 → Status → Targets (ต้องเห็น `rag-api` เป็น UP) / Alerts

> ถ้า Argo แจ้ง rag-api error เรื่อง `ServiceMonitor` ไม่มี CRD แปลว่า monitoring ยังติดตั้งไม่เสร็จ รอแล้วกด Sync อีกครั้ง
> (ลำดับการติดตั้งข้าม Application เป็นปัญหาที่พบบ่อยใน GitOps)

### 2. Load test + HPA
```bash
make hpa             # terminal 1
make loadtest        # terminal 2
```
ดู Grafana panel "replicas vs CPU" และ "Ollama CPU" แล้วตอบคำถามท้าย `k6.js`

### 3. Drift → Retrain (ต้องเปิด compose ของ phase 1 ไว้: MLflow + S3)
```bash
(cd ../phase-1-data-ml && make up)
uv sync
make drift           # train vs test → ไม่ควร drift
make drift-shift     # ข้อมูลจำลองที่เปลี่ยน → ต้อง drift (exit 2)
make flow-shift      # Prefect: drift → dvc repro train → dvc push
make prefect-ui      # (อีก terminal) http://localhost:4200 ดูประวัติ flow run
```
ดูใน MLflow ว่ามี run ใหม่ และ alias `champion` เปลี่ยนหรือไม่ (ถ้าไม่เปลี่ยนเพราะอะไร?)

## ✅ Checkpoint
- dashboard RAG API มีข้อมูลครบทุก panel หลังจาก load test
- อธิบายได้ด้วยตัวเลขว่า latency ส่วนใหญ่มาจาก stage ไหน
- `make flow-shift` จบด้วยสถานะ `retrained` และ `make flow` (ไม่มี shift) จบด้วย `skipped`

## 💥 Break it
1. `kubectl -n ai scale deploy ollama --replicas=0` → alert `RagApiHighErrorRate` ต้องขึ้นใน Prometheus (รอ 5 นาที)
2. เพิ่ม label `question` เข้า Counter (อย่า commit) แล้วรัน load test → ดูจำนวน series ใน Prometheus (`count({__name__=~"rag_.*"})`) แล้วอธิบายปัญหา cardinality
3. ลด `--threshold` ของ drift เหลือ 0.01 → flow retrain ทุกครั้ง (false positive มีราคาอะไรบ้าง?)

## 🧠 ต้องตอบได้
- RED metrics คืออะไร และ metric อะไรบ้างที่เฉพาะกับงาน AI?
- data drift, concept drift และ model degradation ต่างกันอย่างไร?
- ทำไม HPA ของ rag-api ไม่ทำให้ระบบเร็วขึ้น? ต้องแก้ที่ไหนแทน?
