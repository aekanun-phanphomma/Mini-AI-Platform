"""Prometheus metrics (ADR-0019)

RED = Rate, Errors, Duration สำหรับ request
บวก metric เฉพาะของ AI ที่ dashboard ทั่วไปไม่มี:
- latency แยกตาม stage (embed / search / generate) จะได้รู้ว่าช้าที่ไหน
- จำนวน token ซึ่งเป็นตัวแทนของ cost
- คะแนน retrieval สูงสุด ถ้าค่าตกลงเรื่อย ๆ แปลว่าคำถามของผู้ใช้ไม่ตรงกับเอกสาร (drift)
"""

from prometheus_client import Counter, Histogram

REQUESTS = Counter(
    "rag_requests_total", "Requests by endpoint and status", ["endpoint", "status"]
)

STAGE_SECONDS = Histogram(
    "rag_stage_seconds",
    "Latency of each RAG stage",
    ["stage"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 40, 80),
)

LLM_TOKENS = Counter("rag_llm_tokens_total", "LLM tokens", ["kind"])  # kind=prompt|completion

TOP_SCORE = Histogram(
    "rag_retrieval_top_score",
    "Cosine similarity of the best retrieved chunk",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
