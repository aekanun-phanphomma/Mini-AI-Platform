# ADR-0004: ใช้ Docker Engine ใน WSL แทน Docker Desktop

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 0

## บริบท
ต้องใช้ container runtime สำหรับ docker compose (phase 1-2) และ k3d (phase 3+)
แล็บมีเงื่อนไขว่าต้องฟรีและติดตั้งด้วย code ได้

## การตัดสินใจ
ติดตั้ง Docker Engine (docker-ce) จาก apt repo ทางการของ Docker ลงใน WSL โดยตรง ผ่าน Ansible role `docker`
ตั้ง log rotation ใน `daemon.json` และเพิ่ม user เข้า group `docker`

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Docker Engine ใน WSL (เลือก) | ฟรี 100%, ติดตั้งด้วย Ansible ได้, เหมือน server จริง | ไม่มี GUI, ต้องเปิด systemd |
| Docker Desktop | GUI, ใช้จาก PowerShell ได้ | ต้องจ่ายถ้าองค์กรใหญ่ (>250 คน), ติดตั้งด้วย code ยาก, เพิ่ม VM อีกชั้น |
| Podman | rootless, ไม่ต้องมี daemon | k3d/compose บางส่วนยังมีปัญหาความเข้ากันได้ |
| Rancher Desktop | ฟรี, มี k3s ในตัว | ซ่อนรายละเอียดที่เราอยากเรียน |

## ผลที่ตามมา
- ✅ เข้าใจองค์ประกอบของ Docker: daemon, containerd, buildx, compose plugin
- ⚠️ การอยู่ใน group `docker` เทียบเท่า root (mount `/` เข้า container ได้) ยอมรับได้สำหรับเครื่อง dev แต่ห้ามทำบน server ที่ใช้ร่วมกัน
- ⚠️ ใช้คำสั่ง `docker` จาก PowerShell ไม่ได้ ต้องเข้า WSL ก่อน
