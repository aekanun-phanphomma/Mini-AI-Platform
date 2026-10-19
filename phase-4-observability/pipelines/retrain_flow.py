#!/usr/bin/env python3
"""ปิดวงจร MLOps: ตรวจ drift → ถ้า drift ให้ retrain ด้วย DVC pipeline → push artifact (ADR-0021)

รันครั้งเดียว:       uv run python pipelines/retrain_flow.py [--simulate-shift] [--force]
รันตาม schedule:    uv run python pipelines/retrain_flow.py --serve   (ตี 2 ทุกวัน)
UI:                 uv run prefect server start  → http://localhost:4200

หมายเหตุ: ในแล็บ "retrain" คือรัน pipeline ซ้ำกับข้อมูลชุดเดิม ซึ่งยังไม่ช่วยให้โมเดลดีขึ้น
ในงานจริงขั้นตอน ingest จะดึงข้อมูลชุดใหม่ที่มี label แล้ว ส่วนนี้มีไว้ให้เห็นว่าระบบต่อกันอย่างไร
"""

import subprocess
import sys
from pathlib import Path

from prefect import flow, get_run_logger, task

HERE = Path(__file__).resolve().parent
PHASE1 = HERE.parents[1] / "phase-1-data-ml"
DRIFT = HERE.parent / "drift" / "drift.py"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    logger = get_run_logger()
    logger.info("$ %s", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.stdout:
        logger.info(proc.stdout)
    if proc.stderr:
        logger.warning(proc.stderr)
    return proc


@task
def check_drift(simulate_shift: bool) -> bool:
    cmd = [sys.executable, str(DRIFT)] + (["--simulate-shift"] if simulate_shift else [])
    proc = run(cmd)
    if proc.returncode not in (0, 2):
        raise RuntimeError(f"drift check failed (exit {proc.returncode})")
    return proc.returncode == 2


# retries: ขั้นที่ต้องใช้ network (ดาวน์โหลด dataset / push S3) ล้มชั่วคราวได้บ่อย
@task(retries=2, retry_delay_seconds=30)
def retrain() -> None:
    # --single-item: บังคับรันเฉพาะ stage train ไม่ต้องดาวน์โหลดข้อมูลใหม่
    proc = run(["dvc", "repro", "--force", "--single-item", "train"], cwd=PHASE1)
    if proc.returncode != 0:
        raise RuntimeError("dvc repro failed")


@task(retries=2, retry_delay_seconds=30)
def publish() -> None:
    if run(["dvc", "push"], cwd=PHASE1).returncode != 0:
        raise RuntimeError("dvc push failed")


@flow(name="retrain-on-drift", log_prints=True)
def retrain_on_drift(simulate_shift: bool = False, force: bool = False) -> str:
    logger = get_run_logger()
    drifted = check_drift(simulate_shift)
    if not (drifted or force):
        logger.info("no significant drift — skip retrain")
        return "skipped"
    logger.info("drift detected (or forced) — retraining")
    retrain()
    publish()
    # train.py ตัดสินเองว่าโมเดลใหม่จะได้เป็น champion หรือไม่ (ดูได้ใน MLflow)
    return "retrained"


if __name__ == "__main__":
    if "--serve" in sys.argv:
        retrain_on_drift.serve(name="nightly", cron="0 2 * * *")
    else:
        retrain_on_drift(
            simulate_shift="--simulate-shift" in sys.argv,
            force="--force" in sys.argv,
        )
