# ADR-0013: image เล็ก, รันเป็น non-root, layer ของ dependency แยกจาก code
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv==0.5.4

WORKDIR /app

# copy pyproject ก่อน code: ถ้าแก้แค่ code, layer นี้ใช้ cache เดิม → build เร็วขึ้นมาก
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml

COPY app ./app

# non-root: ถ้า container ถูกเจาะ ผู้โจมตีไม่ได้ root ทันที
RUN useradd --uid 10001 --no-create-home appuser
USER 10001

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
