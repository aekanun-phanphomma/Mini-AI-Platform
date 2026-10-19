# ADR-0005: ตั้งค่าเครื่องทำงานด้วย Ansible

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 0

## บริบท
ต้องติดตั้งเครื่องมือราว 15 ตัว ถ้าทำมือตาม README จะเจอปัญหา "เครื่องฉันใช้ได้แต่เครื่องเธอไม่ได้"
และถ้า WSL พังก็ต้องจำว่าเคยทำอะไรไปบ้าง
อีกเหตุผลคือ Ansible เป็นเครื่องมือ configuration management ที่ยังใช้กันมากกับ VM และ bare-metal (เช่นเครื่อง GPU)

## การตัดสินใจ
- Windows side: PowerShell script (`setup-wsl.ps1`) ทำเฉพาะสิ่งที่ต้องทำฝั่ง Windows (ติดตั้ง WSL, `.wslconfig`)
- Linux side: Ansible playbook `bootstrap/ansible/site.yml` แบ่งเป็น role: `base`, `docker`, `cli_tools`, `python_tools`
- รันแบบ `ansible_connection=local` บนเครื่องตัวเอง
- ทุก task ต้อง idempotent: รันซ้ำแล้วไม่มีอะไรเปลี่ยน (`changed=0`)
- ใช้เฉพาะ module ใน `ansible.builtin` จึงไม่ต้องติดตั้ง collection เพิ่ม

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| Ansible (เลือก) | declarative, idempotent, ใช้กับ VM บน cloud ได้ด้วย, เป็นทักษะที่ตลาดงานต้องการ | ช้ากว่า shell script, ต้องเรียน YAML/Jinja |
| Bash script | ง่าย, ไม่มี dependency | ทำให้ idempotent ยาก, จัดการ error ยาก |
| Nix / Devbox | reproducible ที่สุด | learning curve สูงมาก |
| Dev Container | แยก environment ต่อ project | ใช้ Docker-in-Docker และ k3d ใน container ซับซ้อน |

## ผลที่ตามมา
- ✅ `./bootstrap/bootstrap.sh` ครั้งเดียวได้เครื่องพร้อมใช้ ถ้าเครื่องพังก็สร้างใหม่ได้
- ✅ `--check` ดูได้ก่อนว่าจะเปลี่ยนอะไร (dry-run) และ `--tags` รันเฉพาะบางส่วนได้
- ✅ เพิ่ม host ใน `inventory.ini` ก็ตั้งค่า VM บน cloud ด้วย playbook เดียวกันได้
- ⚠️ ต้องใส่รหัส sudo ทุกครั้ง (`-K`)
- 🔁 แบบฝึกหัด: เขียน role `gpu` ที่ติดตั้ง NVIDIA driver + container toolkit (ใช้ `when:` ให้ข้ามบนเครื่องที่ไม่มี GPU)
