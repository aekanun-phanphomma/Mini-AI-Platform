#!/usr/bin/env python3
"""ตรวจ data drift ด้วย PSI (Population Stability Index) — ADR-0020

เขียนเองโดยไม่ใช้ library เพื่อให้เห็นว่า drift detection คือการเปรียบเทียบ distribution
ของข้อมูลช่วงที่เทรน (reference) กับข้อมูลที่เข้ามาตอนนี้ (current)

  PSI = Σ (cur% - ref%) * ln(cur% / ref%)
  < 0.10 : ไม่เปลี่ยน   0.10-0.25 : เปลี่ยนปานกลาง   > 0.25 : เปลี่ยนมาก ควร retrain

exit code: 0 = ไม่ drift, 2 = drift (Prefect flow ใช้ค่านี้ตัดสินใจ), อื่น ๆ = error
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PHASE1 = ROOT / "phase-1-data-ml" / "data" / "processed"
EPS = 1e-6


def features(df: pd.DataFrame) -> pd.DataFrame:
    """feature ที่ดูได้โดยไม่ต้องมี label: ใน production ยังไม่มี label ของข้อมูลใหม่ทันที"""
    text = df["text"].astype(str)
    return pd.DataFrame(
        {
            "char_len": text.str.len(),
            "word_count": text.str.split().str.len(),
            "digit_ratio": text.str.count(r"\d") / text.str.len().clip(lower=1),
            "upper_ratio": text.str.count(r"[A-Z]") / text.str.len().clip(lower=1),
        }
    )


def psi_numeric(ref: pd.Series, cur: pd.Series, bins: int = 10) -> float:
    # ใช้ quantile ของ reference เป็นขอบ bin: แต่ละ bin ของ reference จะมีข้อมูลราว 10% เท่ากัน
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    ref_pct = np.histogram(ref, edges)[0] / len(ref) + EPS
    cur_pct = np.histogram(cur, edges)[0] / len(cur) + EPS
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def psi_categorical(ref: pd.Series, cur: pd.Series) -> float:
    cats = sorted(set(ref) | set(cur))
    ref_pct = ref.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy() + EPS
    cur_pct = cur.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy() + EPS
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def simulate_shift(df: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """จำลองโลกเปลี่ยน: ข่าวสั้นลง (เช่นมาจาก social media) และมีแต่ข่าวกีฬา"""
    out = df.copy()
    out["text"] = out["text"].str.slice(0, 60)
    sports = out[out["label"] == 1]
    return pd.concat([out, sports.sample(len(out), replace=True, random_state=seed)])


def level(psi: float) -> str:
    return "none" if psi < 0.10 else "moderate" if psi < 0.25 else "significant"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", type=Path, default=PHASE1 / "train.parquet")
    ap.add_argument("--current", type=Path, default=PHASE1 / "test.parquet")
    ap.add_argument("--simulate-shift", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.25)
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("drift_report.json"))
    args = ap.parse_args()

    ref = pd.read_parquet(args.reference)
    cur = pd.read_parquet(args.current)
    if args.simulate_shift:
        cur = simulate_shift(cur)

    fr, fc = features(ref), features(cur)
    scores = {col: psi_numeric(fr[col], fc[col]) for col in fr.columns}
    # label distribution: ใน production ใช้ "predicted label" แทนเพราะยังไม่มี label จริง
    scores["label_dist"] = psi_categorical(ref["label"], cur["label"])

    report = {
        "reference_rows": len(ref),
        "current_rows": len(cur),
        "threshold": args.threshold,
        "features": {k: {"psi": round(v, 4), "level": level(v)} for k, v in scores.items()},
    }
    report["drift_detected"] = any(v > args.threshold for v in scores.values())
    args.out.write_text(json.dumps(report, indent=2))

    for k, v in report["features"].items():
        print(f"{k:12s} PSI={v['psi']:.4f}  {v['level']}")
    print(f"drift_detected={report['drift_detected']}  -> {args.out}")
    return 2 if report["drift_detected"] else 0


if __name__ == "__main__":
    sys.exit(main())
