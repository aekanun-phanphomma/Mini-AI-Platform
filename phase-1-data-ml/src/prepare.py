"""Stage 2 — prepare: ทำความสะอาดข้อมูลแล้วแบ่ง train/test

ทุกกฎ cleaning ต้อง log จำนวนแถวที่หายไป ถ้าข้อมูลหายไปเยอะผิดปกติ
มักแปลว่า source เปลี่ยน format (data quality issue) ไม่ได้แปลว่า "ข้อมูลสะอาดขึ้น"
"""

import re
from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

RAW = Path("data/raw/news.parquet")
OUT_DIR = Path("data/processed")


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)       # HTML tags
    text = re.sub(r"\\+", " ", text)           # backslash escapes ใน AG News
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    params = yaml.safe_load(Path("params.yaml").read_text())["prepare"]
    df = pd.read_parquet(RAW)
    n0 = len(df)

    df["text"] = df["text"].astype(str).map(clean_text)

    df = df[df["text"].str.len() >= params["min_chars"]]
    print(f"drop short   : {n0 - len(df):,}")

    n1 = len(df)
    df = df.drop_duplicates(subset="text")
    print(f"drop dupes   : {n1 - len(df):,}")

    # stratify: ให้สัดส่วน class ใน train/test เท่ากัน ไม่งั้นค่า metric เชื่อถือไม่ได้
    train, test = train_test_split(
        df,
        test_size=params["test_size"],
        random_state=params["seed"],
        stratify=df["label"],
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train.to_parquet(OUT_DIR / "train.parquet", index=False)
    test.to_parquet(OUT_DIR / "test.parquet", index=False)
    print(f"train={len(train):,} test={len(test):,}")


if __name__ == "__main__":
    main()
