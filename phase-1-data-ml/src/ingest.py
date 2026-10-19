"""Stage 1 — ingest: ดึงข้อมูลดิบมาเก็บเป็น parquet

stage นี้ทำแค่ "ดึงมาให้ตรงต้นฉบับ" ไม่แปลงข้อมูลเลย เพื่อให้แยกได้ว่า
ปัญหาเกิดจาก source หรือจากขั้นตอน cleaning
"""

from pathlib import Path

import yaml
from datasets import load_dataset

OUT = Path("data/raw/news.parquet")


def main() -> None:
    params = yaml.safe_load(Path("params.yaml").read_text())["ingest"]

    ds = load_dataset(params["dataset"], split="train")
    label_names = ds.features["label"].names

    df = ds.to_pandas()
    df = df.sample(n=min(params["sample_size"], len(df)), random_state=params["seed"])
    df["label_name"] = df["label"].map(dict(enumerate(label_names)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"wrote {len(df):,} rows -> {OUT}")
    print(df["label_name"].value_counts().to_string())


if __name__ == "__main__":
    main()
