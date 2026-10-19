# ADR-0016: เขียน Helm chart เองสำหรับ rag-api และ dependency (Ollama, Qdrant)

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 3

## บริบท
manifest ของ k8s ต้องเปลี่ยนตาม environment (image tag, เปิด/ปิด HPA, monitoring)
community chart ของ Ollama/Qdrant มีให้ใช้ แต่ values มักเปลี่ยนรูปแบบระหว่างเวอร์ชัน และซ่อน primitive ของ k8s ที่อยากเรียน

## การตัดสินใจ
- `charts/rag-api`: Deployment, Service, Ingress, HPA, ServiceMonitor, PrometheusRule, dashboard ConfigMap
  แต่ละ feature เปิด/ปิดด้วย flag ใน values
- `charts/ai-deps`: Ollama (Deployment + PVC + Job pull model) และ Qdrant (StatefulSet + headless Service)
- ค่าเฉพาะ environment อยู่ใน `values-lab.yaml` ส่วน `values.yaml` เป็นค่า default
- หลักเรื่อง resource:
  - ตั้ง **memory limit เสมอ** (เกินแล้วโดน OOMKill แค่ pod เดียว ไม่ลามทั้ง node)
  - **ไม่ตั้ง CPU limit ให้ Ollama** (CPU limit ทำให้โดน CFS throttling และ latency ของ LLM แย่ลง)
- Ollama ใช้ `strategy: Recreate` เพราะ PVC เป็น ReadWriteOnce

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Helm chart เขียนเอง (เลือก) | เข้าใจทุกบรรทัด, ควบคุมได้เต็มที่ | ต้องดูแลเอง |
| Community chart (otwld/ollama, qdrant-helm) | feature ครบ, มีคนดูแล | values ซับซ้อนและเปลี่ยนบ่อย |
| Kustomize | ไม่ต้องใช้ template language | เปิด/ปิด feature ทั้งก้อนทำได้ยากกว่า |
| Raw YAML | ง่ายที่สุด | ต้อง copy ไฟล์ซ้ำต่อ environment |

## ผลที่ตามมา
- ✅ `make render` ดู YAML ที่จะ apply จริงได้ ส่วน CI ใช้ `helm lint` + `helm template` ทุก flag
- ⚠️ chart ของ Qdrant ที่เขียนเองไม่มี cluster mode / backup ใน production ควรใช้ official chart หรือ operator
- 🔁 แบบฝึกหัด: เพิ่ม PodDisruptionBudget และ NetworkPolicy ที่ให้เฉพาะ rag-api เรียก Ollama/Qdrant ได้
