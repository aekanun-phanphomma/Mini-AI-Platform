# ADR-0024: การจัดการ secret ในแล็บ (และแนวทางสำหรับงานจริง)

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** ทุก phase

## บริบท
แล็บมี credential หลายจุด: S3, Postgres, Grafana, Argo CD, Cloudflare token
เมื่อ "ทุกอย่างเป็น code" อยู่ใน Git ความเสี่ยงที่ใหญ่ที่สุดคือ commit secret ขึ้น public repo

## การตัดสินใจ
| ที่ | วิธีในแล็บ | ใน Git มี |
|---|---|---|
| docker compose | `.env` (git ignore) สร้างจาก `.env.example` | `.env.example` ที่เป็นค่าตัวอย่าง |
| DVC remote | `.dvc/config.local` (`dvc remote modify --local`) | `.dvc/config` ที่ไม่มี key |
| SeaweedFS identity | สร้าง JSON จาก env ตอน container start | ไม่มี |
| MLflow client | ไม่ต้องมี S3 key (proxied artifacts) | ไม่มี |
| CI → GHCR | `GITHUB_TOKEN` อายุสั้น สร้างใหม่ทุก job | ไม่มี |
| Argo CD admin | secret ที่ chart สร้างให้ (`argocd-initial-admin-secret`) | ไม่มี |
| Cloudflare | `wrangler secret put`, token เก็บใน `.ingest-token` (git ignore) | ไม่มี |
| Grafana | `admin/admin` ใน values **(ยอมรับเฉพาะแล็บ)** | มี (ตั้งใจ) |

## ทางเลือกสำหรับงานจริง
| ตัวเลือก | เหมาะกับ |
|---|---|
| SOPS + age | เข้ารหัส secret แล้ว commit เข้า Git ได้ ใช้กับ GitOps |
| Sealed Secrets | เข้ารหัสด้วย key ของ cluster |
| External Secrets Operator + Vault / AWS Secrets Manager | องค์กรที่มี secret store กลาง |
| GitHub OIDC → cloud | CI ไม่ต้องเก็บ long-lived key เลย |

## ผลที่ตามมา
- ✅ ไม่มี secret จริงใน repo จึงเปิดเป็น public ได้
- ⚠️ ค่าในแล็บอ่อนแอโดยตั้งใจ ห้ามนำไปใช้ซ้ำในงานจริง
- 🔁 แบบฝึกหัด: ติดตั้ง `pre-commit` + `gitleaks` hook เพื่อกัน commit secret โดยไม่ตั้งใจ แล้วลองย้าย Grafana password ไปใช้ SOPS
