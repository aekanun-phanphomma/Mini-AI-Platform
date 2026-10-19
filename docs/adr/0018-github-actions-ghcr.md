# ADR-0018: GitHub Actions build image ไป GHCR แล้ว commit image tag กลับเข้า Git

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 3

## บริบท
ต้องมีทางนำ code ที่ merge แล้วไปเป็น pod ใน cluster โดยอัตโนมัติ และต้องรู้ได้ว่าแต่ละช่วงเวลารันเวอร์ชันไหนอยู่
CI รันบน GitHub ซึ่งเข้า cluster บนโน้ตบุ๊กไม่ได้

## การตัดสินใจ
- workflow `.github/workflows/rag-api.yml`:
  1. PR / push → `ruff` + `pytest`
  2. push `main` → build ด้วย buildx (cache `type=gha`) → push `ghcr.io/<owner>/rag-api:<git-sha>`
  3. `yq` แก้ `values-lab.yaml` ให้เป็น tag ใหม่ แล้ว commit `[skip ci]` → Argo CD เห็นแล้ว deploy
- tag = **git SHA** (immutable) ไม่ใช้ `:latest` ในการ deploy
- ใช้ `GITHUB_TOKEN` (ไม่มี secret ที่ต้องดูแลเอง), จำกัด `permissions` ให้เท่าที่ต้องใช้
- `infra-lint.yml` ตรวจ Helm / OpenTofu / Ansible ทุก PR

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| CI เขียน tag ลง Git (เลือก) | Git history = deploy history, CI ไม่ต้องมี credential ของ cluster | CI commit เข้า main ทำให้ต้อง pull บ่อย |
| Argo CD Image Updater | ไม่ต้อง commit จาก CI | เพิ่ม component, ตั้งค่าซับซ้อน |
| `kubectl set image` จาก CI | ง่าย | push-based, Git ไม่ตรงกับ cluster |
| Docker Hub | นิยม | rate limit, public เท่านั้นถ้าใช้ฟรี |

## ผลที่ตามมา
- ✅ rollback = revert commit `deploy(rag-api): ...`
- ⚠️ package บน GHCR เป็น private ตั้งแต่สร้าง ต้องตั้งเป็น public (หรือสร้าง imagePullSecret) ไม่งั้นจะเจอ `ImagePullBackOff`
- ⚠️ ถ้า branch protection บังคับ PR ทุก commit, bot จะ push ไม่ได้ ต้องใช้ GitHub App หรือ deploy key
- 🔁 แบบฝึกหัด: เพิ่ม Trivy scan image และ SBOM (`docker/build-push-action` มี `sbom: true`)
