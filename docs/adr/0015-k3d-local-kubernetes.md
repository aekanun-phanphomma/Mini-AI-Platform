# ADR-0015: ใช้ k3d รัน Kubernetes บนเครื่อง

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 3

## บริบท
ต้องการ Kubernetes จริง (มี Ingress, PVC, metrics-server, หลาย node) ที่สร้างและลบได้ภายในไม่กี่วินาที
และกิน RAM น้อยพอจะรันคู่กับ Ollama ได้

## การตัดสินใจ
- ใช้ **k3d** (k3s ใน Docker) กำหนดด้วย `phase-3-platform/k3d/cluster.yaml`
- 1 server + 1 agent, k3s `v1.31.2` ให้ตรงกับ kubectl
- ใช้ส่วนที่ k3s มีให้แล้ว: Traefik (ingress), local-path (storage class), metrics-server (สำหรับ HPA)
- ingress ใช้ host `*.localhost` ผ่าน `localhost:8080` (browser resolve `*.localhost` เป็น 127.0.0.1 เอง)
- ก่อนมี CI ใช้ `k3d image import` โหลด image เข้า cluster

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| k3d (เลือก) | เร็ว, เบา, มี ingress + LB ในตัว, multi-node | k3s ต่างจาก upstream เล็กน้อย |
| kind | upstream Kubernetes, CI ใช้กันมาก | ต้องติดตั้ง ingress/metrics-server เอง |
| minikube | doc เยอะ | หนักกว่า, single node เป็นหลัก |
| managed k8s (GKE/EKS) | ของจริง | เสียเงิน |

## ผลที่ตามมา
- ✅ `make cluster-down && make cluster-up` ได้ cluster ใหม่ใน ~30 วินาที จึงกล้าลองทำให้พัง
- ⚠️ local-path PV ผูกกับ node ถ้า pod ย้าย node จะ mount volume เดิมไม่ได้ (ใน cloud ใช้ network storage แทน)
- 🔁 แบบฝึกหัด: `kubectl drain` agent node แล้วดูว่า Qdrant (StatefulSet + local PV) เกิดอะไรขึ้น
