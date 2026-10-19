# ADR-0003: ใช้ WSL2 (Ubuntu 24.04) และเก็บ repo ใน Linux filesystem

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 0

## บริบท
เครื่องมือ infra/MLOps เกือบทั้งหมด (Docker, k3d, Ansible, DVC, shell script) ออกแบบมาสำหรับ Linux
server และ container ในงานจริงก็เป็น Linux แต่เครื่องที่มีคือ Windows 11
repo ปัจจุบันอยู่ใน OneDrive (`C:\Users\...\OneDrive\...`)

## การตัดสินใจ
1. ใช้ WSL2 + Ubuntu 24.04 LTS ติดตั้งด้วย `bootstrap/windows/setup-wsl.ps1`
2. จำกัด resource ของ VM ผ่าน `.wslconfig` (memory 12GB, CPU 6) ซึ่ง script เขียนให้
3. clone repo ไว้ที่ `~/code/Mini-AI-Platform` ใน Linux **ไม่ใช้** `/mnt/c/...` และไม่ไว้ใน OneDrive
4. เปิด systemd ใน WSL (`/etc/wsl.conf`) เพื่อให้ docker daemon จัดการได้เหมือน server ปกติ

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| WSL2 + Linux FS (เลือก) | เร็วเกือบเท่า Linux จริง, ใช้คำสั่งเดียวกับ server | ต้องเรียนการแยก filesystem สองฝั่ง |
| WSL2 + repo บน /mnt/c | แก้ไฟล์จาก Windows ได้ตรง ๆ | I/O ช้ากว่า 5-20 เท่า, permission/line ending เพี้ยน, inotify ไม่ทำงาน |
| VirtualBox / Hyper-V VM | แยกขาดจาก host | หนักกว่า, ตั้งค่า network ยุ่งกว่า |
| Native Windows | ไม่ต้องตั้งค่าอะไร | เครื่องมือหลายตัวไม่รองรับหรือมี bug เฉพาะ Windows |

## ผลที่ตามมา
- ✅ ทุกคำสั่งในแล็บเหมือนกับที่ใช้บน Linux server / CI runner
- ✅ เปิดไฟล์จาก Windows ได้ที่ `\\wsl$\Ubuntu-24.04\home\<user>\code` หรือใช้ VS Code + WSL extension
- ⚠️ OneDrive sync ไฟล์ใน WSL ไม่ได้ ต้องใช้ Git push ขึ้น GitHub เป็นที่ backup (ซึ่งเป็นแนวทางที่ถูกอยู่แล้ว)
- ⚠️ `.wslconfig` จำกัด RAM ไว้ ถ้ารัน Phase 3+4 พร้อมกันแล้ว OOM ให้ปิด compose ของ phase 1/2
