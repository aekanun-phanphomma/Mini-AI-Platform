# ใช้ '>' แทน TAB เป็นตัวนำหน้าคำสั่ง (GNU make >= 3.82)
# เพราะ TAB มักหายตอน copy/paste และทำให้ error "missing separator"
.RECIPEPREFIX = >
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help up down logs dvc-init pipeline push pull exp dag clean

help:  ## แสดงคำสั่งทั้งหมด
> @grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

.env:
> cp .env.example .env

up: .env  ## start S3 + Postgres + MLflow
> docker compose up -d --build
> @echo "รอ MLflow พร้อม (~30s): docker compose ps"
> @echo "MLflow UI : http://localhost:5000"
> @echo "S3 master : http://localhost:9333"

down:  ## stop (ข้อมูลยังอยู่ใน volume)
> docker compose down

logs:
> docker compose logs -f --tail=100

# DVC ต้องอยู่ใน git repo; --subdir เพราะ repo นี้เป็น monorepo
# credential ใส่ด้วย --local → เขียนลง .dvc/config.local ซึ่ง git ignore อยู่แล้ว
dvc-init: .env  ## ตั้งค่า DVC + remote S3 (ทำครั้งเดียว)
> test -d .dvc || dvc init --subdir
> dvc remote add -d -f s3 s3://dvc
> dvc remote modify s3 endpointurl http://localhost:8333
> source .env && dvc remote modify --local s3 access_key_id "$$S3_ACCESS_KEY" \
>   && dvc remote modify --local s3 secret_access_key "$$S3_SECRET_KEY"
> @echo "commit .dvc/config แล้ว (ไม่มี secret อยู่ในนั้น)"

pipeline:  ## รัน pipeline ทั้งหมด (เฉพาะ stage ที่ต้องรัน)
> uv sync
> dvc repro
> dvc metrics show

push:  ## อัปโหลด data/model ขึ้น S3 remote
> dvc push

pull:  ## ดึง data/model ตาม dvc.lock ของ commit ปัจจุบัน
> dvc pull

exp:  ## ตัวอย่าง experiment: เปลี่ยน C โดยไม่ต้องแก้ไฟล์
> dvc exp run -S train.C=1.0
> dvc exp run -S train.C=10.0
> dvc exp show --only-changed

dag:  ## แสดง pipeline DAG
> dvc dag

clean:  ## ลบ container + volume ทั้งหมด (ข้อมูลหาย!)
> docker compose down -v
