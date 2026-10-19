#!/usr/bin/env python3
"""วัดคุณภาพ RAG ด้วยชุดคำถามที่รู้คำตอบอยู่แล้ว (ADR-0014)

วัด 3 อย่าง:
  retrieval_hit : เอกสารที่ควรเจอ อยู่ใน sources ที่ค้นได้ไหม (ถ้าค้นผิด LLM ก็ตอบถูกไม่ได้)
  answer_hit    : คำตอบมีคีย์เวิร์ดที่ต้องมีครบไหม (วัดแบบหยาบแต่ทำซ้ำได้และไม่เสียเงิน)
  latency       : p50 / p95

exit code 1 ถ้าต่ำกว่าเกณฑ์ จึงใช้เป็น quality gate ก่อน deploy ได้
"""

import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ask(url: str, host: str | None, question: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if host:
        headers["Host"] = host
    req = urllib.request.Request(
        f"{url.rstrip('/')}/ask",
        data=json.dumps({"question": question}).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--host")
    ap.add_argument("--questions", type=Path, default=HERE / "questions.jsonl")
    ap.add_argument("--min-retrieval", type=float, default=0.8)
    ap.add_argument("--min-answer", type=float, default=0.6)
    args = ap.parse_args()

    cases = [json.loads(line) for line in args.questions.read_text("utf-8").splitlines() if line]
    rows, latencies = [], []

    for c in cases:
        t0 = time.perf_counter()
        res = ask(args.url, args.host, c["question"])
        latencies.append(time.perf_counter() - t0)

        sources = [s["source"] for s in res.get("sources", [])]
        answer = res["answer"].lower()
        retrieval_hit = c["expected_source"] is None or c["expected_source"] in sources
        answer_hit = all(k.lower() in answer for k in c["must_contain"])
        rows.append({**c, "answer": res["answer"], "sources": sources,
                     "retrieval_hit": retrieval_hit, "answer_hit": answer_hit})
        mark = lambda ok: "✅" if ok else "❌"  # noqa: E731
        print(f"{mark(retrieval_hit)}{mark(answer_hit)} {c['question']}")

    retrieval = sum(r["retrieval_hit"] for r in rows) / len(rows)
    answer = sum(r["answer_hit"] for r in rows) / len(rows)
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
    summary = {"n": len(rows), "retrieval_hit_rate": round(retrieval, 3),
               "answer_hit_rate": round(answer, 3), "latency_p50_s": round(p50, 2),
               "latency_p95_s": round(p95, 2)}

    (HERE / "results.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), "utf-8"
    )
    print(json.dumps(summary, indent=2))

    if retrieval < args.min_retrieval or answer < args.min_answer:
        raise SystemExit("FAILED quality gate")


if __name__ == "__main__":
    main()
