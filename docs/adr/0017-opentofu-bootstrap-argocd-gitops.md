# ADR-0017: OpenTofu ใช้ bootstrap cluster แล้วให้ Argo CD จัดการทุกอย่างแบบ GitOps (app-of-apps)

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 3

## บริบท
ถ้า deploy ด้วย `kubectl apply` / `helm install` จากเครื่อง dev จะไม่มีใครรู้ว่าใน cluster มีอะไรอยู่
ถ้ามีคนแก้มือ (drift) ก็ไม่มีใครเห็น และสร้าง cluster ใหม่ให้เหมือนเดิมไม่ได้
คำถามที่ต้องตอบคือ เครื่องมือไหนดูแลส่วนไหน

## การตัดสินใจ
แบ่งหน้าที่เป็นสองชั้น:

| ชั้น | เครื่องมือ | จัดการอะไร | เปลี่ยนบ่อยไหม |
|---|---|---|---|
| Bootstrap | **OpenTofu** (`phase-3-platform/infra`) | Argo CD + root Application | นาน ๆ ครั้ง |
| Workloads | **Argo CD** อ่านจาก `gitops/apps/` | ai-deps, rag-api, monitoring | บ่อย |

- root app ใช้ chart `argocd-apps` แทน `kubernetes_manifest` เพราะ `kubernetes_manifest` ต้องมี CRD อยู่แล้วตอน plan
- เปิด `automated: {prune: true, selfHeal: true}`: Git คือ source of truth ถ้าแก้ cluster ด้วยมือ Argo จะแก้กลับ
- ใช้ OpenTofu (fork open source ของ Terraform, license MPL) syntax เดียวกับ Terraform
- state เก็บ local (แล็บ) และ pin provider `helm ~> 2.16`
- repo ต้องเป็น **public** บน GitHub เพราะ Argo CD ใน cluster ต้อง clone ได้

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Tofu bootstrap + Argo CD (เลือก) | แบ่งหน้าที่ชัด, มี UI เห็น drift, pull-based (CI ไม่ต้องมี kubeconfig) | 2 เครื่องมือ |
| Terraform จัดการทุกอย่าง | เครื่องมือเดียว | ไม่มี reconcile loop, เห็น drift เฉพาะตอนรัน plan |
| Flux CD | เบา, เป็น CLI-first | ไม่มี UI ในตัว ภาพไม่ชัดสำหรับการเรียน |
| Helm จาก CI (push-based) | ง่าย | CI ต้องถือ credential ของ cluster (ความเสี่ยงด้าน security) |

## ผลที่ตามมา
- ✅ deploy = merge PR, rollback = `git revert`
- ✅ เพิ่ม monitoring ใน phase 4 แค่เพิ่มไฟล์เดียวใน `gitops/apps/`
- ⚠️ ต้อง push ก่อนถึงจะเห็นผล (feedback ช้ากว่า `kubectl apply`) ระหว่าง debug ใช้ `helm template` / `make render`
- ⚠️ local tfstate หายแล้ว tofu จะลืมว่าเคยสร้างอะไร งานจริงต้องใช้ remote backend + locking
