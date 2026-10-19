# Phase 3 — Platform: Kubernetes + GitOps + CI/CD

**เป้าหมาย:** merge code แล้วระบบ deploy เองอัตโนมัติ, cluster สร้างใหม่ได้จาก Git ทั้งหมด
**ADR:** [0015](../adr/0015-k3d-local-kubernetes.md) · [0016](../adr/0016-helm-charts.md) · [0017](../adr/0017-opentofu-bootstrap-argocd-gitops.md) · [0018](../adr/0018-github-actions-ghcr.md)
**เวลา:** 2-3 สัปดาห์

## ภาพรวม
```
 dev ──push──▶ GitHub ──Actions──▶ test → build → GHCR (image:sha)
                 ▲                                   │
                 └──── commit values-lab.yaml ◀──────┘
                 │
          Argo CD (ใน cluster) poll Git ทุก ~3 นาที
                 ▼
 k3d cluster: ns argocd │ ns ai: ollama, qdrant, rag-api │ (ns monitoring ใน phase 4)
```

## ขั้นตอน

### 0. ปิด compose ของ phase 1-2 เพื่อคืน RAM
```bash
(cd ../phase-2-llm-rag && make down); (cd ../phase-1-data-ml && make down)
```

### 1. Cluster
```bash
cd ~/code/Mini-AI-Platform/phase-3-platform
make cluster-up
make lint            # helm lint + tofu validate
make image           # build rag-api:dev → import เข้า k3d
```

### 2. GitOps bootstrap
```bash
make set-repo REPO=https://github.com/aekanun-phanphomma/Mini-AI-Platform.git
git add -A && git commit -m "phase3: set gitops repo" && git push
make bootstrap       # tofu apply → Argo CD + root app
make argocd-password
```
เปิด http://argocd.localhost:8080 (admin / password จากคำสั่งด้านบน)
จะเห็น `root` → `ai-deps`, `rag-api` (Job pull model ใช้เวลาหลายนาที)

### 3. ทดสอบ
```bash
make status
make ingest
make eval            # eval set เดียวกับ phase 2 แต่รันผ่าน Ingress
```

### 4. CI/CD
1. push repo ขึ้น GitHub แล้วไปที่ Settings → Actions → General → Workflow permissions → **Read and write**
2. แก้อะไรก็ได้ใน `apps/rag-api` (เช่น `version` ใน `main.py`) → push
3. ดู Actions: test → build → commit `deploy(rag-api): <sha>`
4. GitHub → Packages → `rag-api` → Package settings → **Change visibility → Public**
5. `git pull` (เพราะ bot commit เพิ่ม) แล้วดู Argo CD sync image ใหม่: `kubectl -n ai get deploy rag-api -o jsonpath='{..image}'`

## ✅ Checkpoint
- `make cluster-down && make cluster-up && make bootstrap` → ระบบกลับมาครบเองจาก Git (นอกจากต้อง ingest ใหม่)
- rollback: `git revert <commit deploy>` → push → Argo กลับไป image เดิม

## 💥 Break it
1. **Drift:** `kubectl -n ai scale deploy rag-api --replicas=0` → Argo (selfHeal) ต้องแก้กลับเอง
2. **Prune:** ย้าย `gitops/apps/rag-api.yaml` ออกจากโฟลเดอร์ → push → rag-api หายจาก cluster
3. **ImagePullBackOff:** ตั้ง package กลับเป็น private แล้ว restart pod → อ่าน `kubectl describe pod`
4. **OOM:** ลด `ollama.resources.limits.memory` เหลือ `1Gi` → ดู `OOMKilled` ใน `kubectl get pod -w`
5. **Bad template:** ใส่ YAML ผิดใน chart → PR → CI `infra-lint` ต้อง fail ก่อน merge

## 🧠 ต้องตอบได้
- ทำไม CI ไม่มี kubeconfig แต่ยัง deploy ได้?
- Deployment vs StatefulSet: ทำไม Qdrant ใช้ StatefulSet แต่ Ollama ใช้ Deployment + PVC?
- ถ้า tfstate หาย จะเกิดอะไรขึ้น?

## 🔧 Troubleshooting
| อาการ | วิธีแก้ |
|---|---|
| Argo: `repository not found` | repo ต้อง public และ URL ใน `gitops/apps/*.yaml` ถูกต้อง |
| rag-api `ErrImageNeverPull` / `ImagePullBackOff` ก่อนตั้ง CI | `make image` ใหม่ (import ต้องทำใหม่ทุกครั้งที่สร้าง cluster) |
| เปิด `*.localhost:8080` ไม่ได้ | ลอง `curl -H 'Host: rag.localhost' localhost:8080/healthz` และตรวจ `kubectl -n kube-system get pods` ว่า Traefik ทำงาน |
| ollama-pull Job ค้าง | `kubectl -n ai logs job/ollama-pull-models -f` (ดาวน์โหลดช้า / disk เต็ม) |
