# image ทางการของ MLflow ไม่มี driver Postgres และ boto3 จึง build เองโดย pin เวอร์ชัน
# (ADR-0009) เวอร์ชันต้องตรงกับฝั่ง client ใน ../pyproject.toml
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      mlflow==2.17.2 \
      psycopg2-binary==2.9.10 \
      boto3==1.35.63

RUN useradd --uid 10001 --create-home mlflow
USER 10001
EXPOSE 5000
