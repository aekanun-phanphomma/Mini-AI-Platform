# ADR-0002: ใช้ monorepo เดียวสำหรับทุก phase

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** -

## บริบท
แล็บมีหลายส่วน ได้แก่ bootstrap, data pipeline, app, Helm chart, infra และ GitOps manifest
หลายส่วนอ้างถึงกัน เช่น CI ต้องแก้ไฟล์ใน chart, eval script ใช้ร่วมกันใน phase 2/3/5, drift script อ่านข้อมูลจาก phase 1

## การตัดสินใจ
ใช้ Git repo เดียว แบ่งโฟลเดอร์ตาม phase และแยก `apps/` (code ที่ deploy) กับ `gitops/` (สิ่งที่ควรรันอยู่ใน cluster) ออกมาไว้ที่ระดับบนสุด
CI ใช้ `paths:` filter เพื่อให้ workflow รันเฉพาะเมื่อส่วนที่เกี่ยวข้องเปลี่ยน

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Monorepo (เลือก) | เปลี่ยน app + chart ใน PR เดียว, เห็นภาพรวม, ตั้งค่าง่าย | CI ต้องใช้ path filter, repo ใหญ่ขึ้นเรื่อย ๆ |
| แยก repo app / config (polyrepo) | สิทธิ์แยกชัด, เป็นแนวทางที่ Argo CD แนะนำในองค์กรใหญ่ | ต้องจัดการหลาย repo และสิทธิ์ข้าม repo ใน CI |

## ผลที่ตามมา
- ✅ clone ครั้งเดียวได้ทั้งแล็บ
- ⚠️ CI commit กลับเข้า repo เดียวกับที่ dev ทำงาน จึงต้อง `git pull` บ่อย (ดู ADR-0018)
- 🔁 ถ้ามีหลายทีม ให้ย้าย `gitops/` ไปเป็น repo แยก (config repo pattern)
