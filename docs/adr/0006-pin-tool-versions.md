# ADR-0006: pin เวอร์ชันของทุกเครื่องมือ และติดตั้งแบบ versioned directory + symlink

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 0 (หลักการนี้ใช้กับทุก phase)

## บริบท
ถ้าใช้ `latest` วันนี้กับเดือนหน้าจะได้ของไม่เหมือนกัน แล็บที่เคยทำงานได้จะพังเองโดยที่ code ไม่ได้เปลี่ยน
ตัวอย่างจริงตอนเขียนแล็บนี้: MinIO หยุดเผยแพร่ image บน Docker Hub ทำให้ compose ที่อ้าง `minio/minio` ใช้ไม่ได้ (ดู ADR-0008)
นอกจากนี้ kubectl ต้องมีเวอร์ชันห่างจาก cluster ไม่เกิน ±1 minor

## การตัดสินใจ
- เวอร์ชันของ CLI ทั้งหมดอยู่ใน `bootstrap/ansible/group_vars/all.yml` ที่เดียว
- ติดตั้งไว้ที่ `/opt/tools/<name>-<version>` แล้ว symlink ไปที่ `/usr/local/bin/<name>`
- container image ใช้ tag ที่ระบุเวอร์ชันเสมอ (`qdrant/qdrant:v1.12.4` ไม่ใช่ `:latest`)
- Helm chart / Terraform provider / Python package กำหนดเวอร์ชันหรือช่วงเวอร์ชันชัดเจน
- `rancher/k3s` กับ `kubectl` ใช้ minor เดียวกัน (1.31)

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Pin + versioned dir (เลือก) | reproducible, rollback ได้ทันทีด้วยการเปลี่ยน symlink | ต้องอัปเดตเวอร์ชันเอง |
| apt / snap | อัปเดตอัตโนมัติ | เวอร์ชันไม่แน่นอน, apt มักมีเวอร์ชันเก่า |
| asdf / mise | จัดการหลายเวอร์ชันได้ดี | เพิ่มเครื่องมืออีกตัว |

## ผลที่ตามมา
- ✅ เครื่องสองเครื่องที่รัน playbook เดียวกันได้ผลเหมือนกัน
- ⚠️ เวอร์ชันจะเก่าลงเรื่อย ๆ ต้องอัปเกรดเอง ในงานจริงใช้ Renovate/Dependabot ช่วยเปิด PR อัปเดตอัตโนมัติ
- 🔁 แบบฝึกหัด: เปิด Dependabot ให้ GitHub Actions และ Dockerfile
