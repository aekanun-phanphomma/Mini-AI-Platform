"""HTTP layer ของ RAG service

ไม่เก็บ state ใน process (ADR-0013): เอกสารอยู่ใน Qdrant โมเดลอยู่ใน Ollama
จึงเพิ่มจำนวน replica ได้เลย (HPA, Phase 4)
"""

import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from .metrics import REQUESTS, STAGE_SECONDS
from .rag import RagService
from .settings import settings


class Document(BaseModel):
    source: str = Field(..., examples=["leave-policy.md"])
    text: str


class IngestRequest(BaseModel):
    documents: list[Document]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(None, ge=1, le=20)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RagService(settings)
    yield
    await app.state.rag.close()


app = FastAPI(title="rag-api", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    """liveness: process ยังทำงานอยู่ ห้ามเช็ก dependency ที่นี่
    ไม่งั้นถ้า Ollama ล่ม K8s จะ restart rag-api ไปด้วยโดยไม่ช่วยอะไร"""
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(response: Response):
    """readiness: dependency พร้อมไหม"""
    checks = await app.state.rag.ready()
    if any(v != "ok" for v in checks.values()):
        response.status_code = 503
    return checks


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ingest")
async def ingest(req: IngestRequest):
    try:
        n = await app.state.rag.ingest([d.model_dump() for d in req.documents])
    except httpx.HTTPError as e:
        REQUESTS.labels("ingest", "error").inc()
        raise HTTPException(502, f"upstream error: {e}") from e
    REQUESTS.labels("ingest", "ok").inc()
    return {"documents": len(req.documents), "chunks": n}


@app.post("/ask")
async def ask(req: AskRequest):
    start = time.perf_counter()
    try:
        result = await app.state.rag.ask(req.question, req.top_k)
    except httpx.HTTPError as e:
        REQUESTS.labels("ask", "error").inc()
        raise HTTPException(502, f"upstream error: {e}") from e
    elapsed = time.perf_counter() - start
    STAGE_SECONDS.labels("total").observe(elapsed)
    REQUESTS.labels("ask", "ok").inc()
    result["latency_s"] = round(elapsed, 3)
    return result
