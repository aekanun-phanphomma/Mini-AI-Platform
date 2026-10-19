"""Unit tests ที่ไม่ต้องใช้ Ollama/Qdrant จริง จึงรันใน CI ได้
(คุณภาพของคำตอบวัดด้วย eval set ใน phase-2-llm-rag/eval ซึ่งเป็นคนละเรื่องกับ unit test)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag import chunk_text, point_id


def test_chunk_empty():
    assert chunk_text("   ", 100, 10) == []


def test_chunk_short_text_is_single_chunk():
    assert chunk_text("สวัสดี", 100, 10) == ["สวัสดี"]


def test_chunk_covers_everything_with_overlap():
    text = "ก" * 1000
    chunks = chunk_text(text, 300, 50)
    assert all(len(c) <= 300 for c in chunks)
    # ถ้ามี overlap ความยาวรวมต้องมากกว่าหรือเท่ากับต้นฉบับ (ไม่มีส่วนไหนหาย)
    assert sum(len(c) for c in chunks) >= len(text)
    assert chunks[-1].endswith("ก")


def test_chunk_prefers_newline_boundary():
    text = "a" * 200 + "\n" + "b" * 200
    chunks = chunk_text(text, 300, 20)
    assert chunks[0] == "a" * 200


def test_chunk_rejects_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("abc", 10, 10)


def test_point_id_is_deterministic():
    assert point_id("a.md", 0) == point_id("a.md", 0)
    assert point_id("a.md", 0) != point_id("a.md", 1)


def test_healthz_and_metrics():
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert "rag_requests_total" in client.get("/metrics").text


def test_ask_validation():
    with TestClient(app) as client:
        assert client.post("/ask", json={"question": ""}).status_code == 422
