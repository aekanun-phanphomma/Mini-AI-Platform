// rag-edge: RAG แบบเดียวกับ apps/rag-api แต่ใช้ managed services ของ Cloudflare
//   Ollama  → Workers AI   (เรียก model ผ่าน binding ไม่ต้องดูแล server)
//   Qdrant  → Vectorize    (vector DB แบบ managed)
//   K8s/HPA → Workers      (scale อัตโนมัติ จ่ายตามจำนวน request)

// ประกาศ type ของ binding เองแบบสั้น ๆ เพื่อให้เห็นว่า code ใช้ API อะไรบ้าง
interface VectorMatch {
  id: string;
  score: number;
  metadata?: Record<string, unknown>;
}
interface Env {
  AI: { run(model: string, input: unknown): Promise<unknown> };
  VECTORIZE: {
    upsert(v: { id: string; values: number[]; metadata: Record<string, string> }[]): Promise<unknown>;
    query(
      vector: number[],
      opts: { topK: number; returnMetadata: "all" | "indexed" | "none" },
    ): Promise<{ matches: VectorMatch[] }>;
  };
  EMBED_MODEL: string;
  CHAT_MODEL: string;
  TOP_K: string;
  INGEST_TOKEN: string;
}

const SYSTEM_PROMPT =
  "คุณเป็นผู้ช่วยตอบคำถามจากเอกสารภายในองค์กร ตอบโดยใช้ข้อมูลใน CONTEXT เท่านั้น " +
  "ถ้าใน CONTEXT ไม่มีคำตอบ ให้ตอบว่า 'ไม่ทราบ' ห้ามแต่งข้อมูลเพิ่ม ตอบเป็นภาษาไทยให้กระชับ " +
  "และระบุแหล่งที่มาในวงเล็บเหลี่ยม";

// ตรรกะเดียวกับ chunk_text ใน apps/rag-api/app/rag.py
function chunkText(text: string, size = 800, overlap = 150): string[] {
  const t = text.trim();
  const chunks: string[] = [];
  let start = 0;
  while (start < t.length) {
    let end = Math.min(start + size, t.length);
    if (end < t.length) {
      const cut = t.lastIndexOf("\n", end - 1);
      if (cut >= start + size / 2) end = cut;
    }
    const piece = t.slice(start, end).trim();
    if (piece) chunks.push(piece);
    if (end >= t.length) break;
    start = Math.max(end - overlap, start + 1);
  }
  return chunks;
}

async function embed(env: Env, texts: string[]): Promise<number[][]> {
  const res = (await env.AI.run(env.EMBED_MODEL, { text: texts })) as { data: number[][] };
  return res.data;
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

async function ingest(req: Request, env: Env): Promise<Response> {
  if (req.headers.get("authorization") !== `Bearer ${env.INGEST_TOKEN}`) {
    return json({ error: "unauthorized" }, 401);
  }
  const { documents } = (await req.json()) as { documents: { source: string; text: string }[] };
  let total = 0;
  for (const doc of documents) {
    const chunks = chunkText(doc.text);
    for (let i = 0; i < chunks.length; i += 16) {
      const batch = chunks.slice(i, i + 16);
      const vectors = await embed(env, batch);
      // id แบบ deterministic: ingest ซ้ำจะทับของเดิม
      await env.VECTORIZE.upsert(
        batch.map((text, j) => ({
          id: `${doc.source}#${i + j}`,
          values: vectors[j],
          metadata: { source: doc.source, text },
        })),
      );
    }
    total += chunks.length;
  }
  return json({ documents: documents.length, chunks: total });
}

async function ask(req: Request, env: Env): Promise<Response> {
  const started = Date.now();
  const { question } = (await req.json()) as { question?: string };
  if (!question) return json({ error: "question is required" }, 422);

  const [vector] = await embed(env, [question]);
  const { matches } = await env.VECTORIZE.query(vector, {
    topK: Number(env.TOP_K),
    returnMetadata: "all",
  });

  const context = matches
    .map((m) => `[${m.metadata?.source}]\n${m.metadata?.text}`)
    .join("\n\n");
  const out = (await env.AI.run(env.CHAT_MODEL, {
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: `CONTEXT:\n${context}\n\nคำถาม: ${question}` },
    ],
    temperature: 0.1,
  })) as { response?: string; usage?: unknown };

  return json({
    answer: out.response ?? "",
    sources: matches.map((m) => ({ source: m.metadata?.source, score: m.score })),
    usage: out.usage ?? null,
    latency_s: (Date.now() - started) / 1000,
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(req.url);
    try {
      if (req.method === "GET" && pathname === "/healthz") return json({ status: "ok" });
      if (req.method === "POST" && pathname === "/ingest") return await ingest(req, env);
      if (req.method === "POST" && pathname === "/ask") return await ask(req, env);
      return json({ error: "not found" }, 404);
    } catch (err) {
      console.error(err);
      return json({ error: String(err) }, 502);
    }
  },
};
