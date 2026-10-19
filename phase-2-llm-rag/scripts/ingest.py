#!/usr/bin/env python3
"""ส่งไฟล์ .md ใน sample-docs/ เข้า /ingest

ใช้แค่ standard library จึงไม่ต้องติดตั้งอะไรเพิ่ม และใช้ script เดียวกันได้กับทุก environment:
  compose : python3 scripts/ingest.py --url http://localhost:8000
  k3d     : python3 scripts/ingest.py --url http://localhost:8080 --host rag.localhost
  edge    : python3 scripts/ingest.py --url https://rag-edge.<you>.workers.dev --token $TOKEN
"""

import argparse
import json
import urllib.request
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "sample-docs"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--host", help="Host header (สำหรับ ingress)")
    ap.add_argument("--token", help="Bearer token (สำหรับ edge worker)")
    ap.add_argument("--docs", type=Path, default=DOCS)
    args = ap.parse_args()

    documents = [
        {"source": p.name, "text": p.read_text(encoding="utf-8")}
        for p in sorted(args.docs.glob("*.md"))
    ]
    headers = {"Content-Type": "application/json"}
    if args.host:
        headers["Host"] = args.host
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    req = urllib.request.Request(
        f"{args.url.rstrip('/')}/ingest",
        data=json.dumps({"documents": documents}).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print(json.loads(r.read()))


if __name__ == "__main__":
    main()
