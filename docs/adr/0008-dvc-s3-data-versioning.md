# ADR-0008: ใช้ DVC + S3-compatible storage (SeaweedFS) สำหรับ version ข้อมูลและ pipeline

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 1

## บริบท
โมเดลประกอบด้วย code + data + config ถ้าไม่รู้ว่าโมเดลเทรนจากข้อมูลชุดไหน ก็ reproduce หรือ debug ไม่ได้
Git ไม่เหมาะกับไฟล์ใหญ่ ส่วน object storage (S3) เป็นที่เก็บข้อมูลมาตรฐานของงาน data/ML บน cloud
แผนเดิมใช้ MinIO แต่ตรวจแล้วพบว่า image `minio/minio` บน Docker Hub ไม่มีให้ดึงแล้ว

## การตัดสินใจ
- **DVC** ทำ 2 หน้าที่
  1. version ข้อมูล: Git เก็บแค่ hash (`dvc.lock`) ไฟล์จริงเก็บใน S3
  2. pipeline: `dvc.yaml` ระบุ stage พร้อม deps/params/outs แล้ว `dvc repro` รันเฉพาะส่วนที่เปลี่ยน
- **SeaweedFS** ให้ S3 API บนเครื่อง (Apache-2.0, image `chrislusf/seaweedfs`) แทน MinIO
- สร้าง bucket ด้วย one-shot container `amazon/aws-cli` ผ่าน S3 API มาตรฐาน จึงไม่ผูกกับ storage ตัวใดตัวหนึ่ง
- credential ของ DVC เก็บใน `.dvc/config.local` (git ignore) ไม่ใช่ `.dvc/config`

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| DVC (เลือก) | ใช้คู่กับ Git ได้ตรง ๆ, มี pipeline + experiment ในตัว, ไม่ต้องมี server | ต้องจำคำสั่งเพิ่ม, ไม่เหมาะกับข้อมูลระดับ TB ที่เปลี่ยนตลอด |
| Git LFS | ง่าย | ไม่มี pipeline, GitHub คิดเงินเมื่อเกิน quota |
| lakeFS / Delta Lake / Iceberg | เหมาะกับ data lake ขนาดใหญ่ | เกินความจำเป็นสำหรับแล็บ |
| MinIO | นิยมที่สุด | หยุดเผยแพร่ image/binary ของ community edition |
| SeaweedFS (เลือก) | เบา, รองรับ S3 API, license เปิด | UI น้อย, ตั้งค่า identity ผ่าน JSON |

## ผลที่ตามมา
- ✅ `git checkout <commit> && dvc pull` ได้ข้อมูลและโมเดลของ commit นั้นกลับมาทุกไฟล์
- ✅ endpoint ใช้ S3 API ล้วน ถ้าย้ายไป AWS S3 / Cloudflare R2 แค่เปลี่ยน `endpointurl`
- ⚠️ SeaweedFS ในแล็บรันเป็น single node ไม่มี replication ข้อมูลหายได้ถ้าลบ volume
- 🔁 บทเรียน: dependency ภายนอกหายไปได้เสมอ ควรใช้ API มาตรฐาน (S3) ไม่ผูกกับผลิตภัณฑ์ใดผลิตภัณฑ์หนึ่ง
