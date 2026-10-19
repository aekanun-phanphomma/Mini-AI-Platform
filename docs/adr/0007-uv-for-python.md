# ADR-0007: ใช้ uv จัดการ Python environment และ CLI tools

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 0-4

## บริบท
แล็บมี Python หลายส่วน (phase-1 pipeline, rag-api, phase-4 flow) ซึ่งมี dependency ต่างกัน
Ubuntu 24.04 ห้าม `pip install` ลง system Python (PEP 668 "externally managed")
และ CLI อย่าง DVC มี dependency จำนวนมาก ถ้าติดตั้งรวมกับ project อื่นจะชนกันได้

## การตัดสินใจ
- ติดตั้ง `uv` ระดับ user แล้วใช้ `uv tool install` สำหรับ CLI (dvc, ruff, pre-commit) ซึ่งจะได้ venv แยกของแต่ละตัว
- แต่ละ project มี `pyproject.toml` ของตัวเอง ใช้ `uv sync` / `uv run` (venv แยกต่อ project)
- ใน Docker image ใช้ `uv pip install --system` เพราะ container แยก environment ให้อยู่แล้ว

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| uv (เลือก) | เร็วกว่า pip 10-100 เท่า, จัดการ Python version + venv + lock ได้ในตัวเดียว | ยังใหม่, บางคำสั่งเปลี่ยนตามเวอร์ชัน |
| pip + venv | มาตรฐาน | ช้า, ไม่มี lockfile ในตัว |
| Poetry | lockfile ดี | ช้า, ใช้ใน Docker ยุ่ง |
| conda | เหมาะกับ lib ที่มี C/CUDA | หนัก, license ของ channel default |

## ผลที่ตามมา
- ✅ `uv run python src/train.py` สร้าง venv ให้อัตโนมัติ ไม่ต้อง activate
- ✅ ควร commit `uv.lock` ที่ `uv sync` สร้างขึ้น เพื่อให้ dependency ตรงกันทุกเครื่อง
- ⚠️ งาน deep learning ที่ต้องใช้ CUDA อาจต้องใช้ conda/pixi หรือ base image ของ NVIDIA
