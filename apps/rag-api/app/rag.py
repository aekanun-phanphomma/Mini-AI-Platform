"""RAG core: chunk → embed → store → retrieve → generate"""

import time
import uuid
from contextlib import contextmanager

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .metrics import LLM_TOKENS, STAGE_SECONDS, TOP_SCORE
from .settings import Settings

SYSTEM_PROMPT = (
    "คุณเป็นผู้ช่วยตอบคำถามจากเอกสารภายในองค์กร "
    "ตอบโดยใช้ข้อมูลใน CONTEXT เท่านั้น ถ้าใน CONTEXT ไม่มีคำตอบ ให้ตอบว่า 'ไม่ทราบ' "
    "ห้ามแต่งข้อมูลเพิ่ม ตอบเป็นภาษาไทยให้กระชับ และระบุแหล่งที่มาในวงเล็บเหลี่ยม เช่น [leave-policy.md]"
)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """ตัดข้อความเป็นช่วงตามจำนวนตัวอักษร ให้แต่ละช่วงซ้อนทับกันเล็กน้อย

    ตัดตามจำนวนตัวอักษรแทนการตัดตามคำ เพราะภาษาไทยไม่มีช่องว่างระหว่างคำ
    ถ้าทำได้จะตัดตรงขึ้นบรรทัดใหม่เพื่อไม่ให้ประโยคขาดกลาง
    overlap ช่วยให้ข้อมูลที่อยู่ตรงรอยต่อของ chunk ยังค้นเจอ
    """
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind("\n", start + size // 2, end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def point_id(source: str, index: int) -> str:
    """ID แบบ deterministic: ingest เอกสารเดิมซ้ำจะทับของเดิม ไม่เกิดข้อมูลซ้ำ"""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{index}"))


@contextmanager
def timed(stage: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        STAGE_SECONDS.labels(stage).observe(time.perf_counter() - start)


class RagService:
    def __init__(self, s: Settings):
        self.s = s
        self.http = httpx.AsyncClient(base_url=s.ollama_url, timeout=s.request_timeout)
        self.qdrant = AsyncQdrantClient(url=s.qdrant_url)
        self._collection_ready = False

    async def close(self) -> None:
        await self.http.aclose()
        await self.qdrant.close()

    async def ensure_collection(self) -> None:
        if self._collection_ready:
            return
        if not await self.qdrant.collection_exists(self.s.collection):
            await self.qdrant.create_collection(
                self.s.collection,
                vectors_config=VectorParams(size=self.s.embed_dim, distance=Distance.COSINE),
            )
        self._collection_ready = True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        with timed("embed"):
            r = await self.http.post(
                "/api/embed", json={"model": self.s.embed_model, "input": texts}
            )
            r.raise_for_status()
            return r.json()["embeddings"]

    async def ingest(self, documents: list[dict]) -> int:
        await self.ensure_collection()
        total = 0
        for doc in documents:
            chunks = chunk_text(doc["text"], self.s.chunk_size, self.s.chunk_overlap)
            for i in range(0, len(chunks), self.s.embed_batch):
                batch = chunks[i : i + self.s.embed_batch]
                vectors = await self.embed(batch)
                points = [
                    PointStruct(
                        id=point_id(doc["source"], i + j),
                        vector=vec,
                        payload={"source": doc["source"], "text": chunk},
                    )
                    for j, (chunk, vec) in enumerate(zip(batch, vectors, strict=True))
                ]
                await self.qdrant.upsert(self.s.collection, points=points)
            total += len(chunks)
        return total

    async def retrieve(self, question: str, top_k: int) -> list[dict]:
        await self.ensure_collection()
        [vector] = await self.embed([question])
        with timed("search"):
            res = await self.qdrant.query_points(
                self.s.collection, query=vector, limit=top_k, with_payload=True
            )
        hits = [
            {"source": p.payload["source"], "text": p.payload["text"], "score": p.score}
            for p in res.points
        ]
        if hits:
            TOP_SCORE.observe(hits[0]["score"])
        return hits

    async def generate(self, question: str, hits: list[dict]) -> dict:
        context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nคำถาม: {question}"},
        ]
        with timed("generate"):
            r = await self.http.post(
                "/api/chat",
                json={
                    "model": self.s.chat_model,
                    "messages": messages,
                    "stream": False,
                    # temperature ต่ำ = คำตอบนิ่ง เหมาะกับการตอบจากเอกสาร และทำให้ eval ซ้ำได้
                    "options": {"temperature": 0.1},
                },
            )
            r.raise_for_status()
            data = r.json()
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        LLM_TOKENS.labels("prompt").inc(usage["prompt_tokens"])
        LLM_TOKENS.labels("completion").inc(usage["completion_tokens"])
        return {"answer": data["message"]["content"], "usage": usage}

    async def ask(self, question: str, top_k: int | None = None) -> dict:
        hits = await self.retrieve(question, top_k or self.s.top_k)
        result = await self.generate(question, hits)
        result["sources"] = [{"source": h["source"], "score": round(h["score"], 4)} for h in hits]
        return result

    async def ready(self) -> dict:
        checks = {}
        try:
            (await self.http.get("/api/version")).raise_for_status()
            checks["ollama"] = "ok"
        except Exception as e:  # noqa: BLE001
            checks["ollama"] = f"error: {e}"
        try:
            await self.qdrant.get_collections()
            checks["qdrant"] = "ok"
        except Exception as e:  # noqa: BLE001
            checks["qdrant"] = f"error: {e}"
        return checks
