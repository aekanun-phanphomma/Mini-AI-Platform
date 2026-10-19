"""Stage 3 — train: เทรน baseline แล้ว log เข้า MLflow และ register ถ้าผ่าน quality gate

ADR-0010: เริ่มจาก TF-IDF + Logistic Regression เพราะเทรนได้ในไม่กี่วินาทีบน CPU
และให้ตัวเลข baseline ไว้เทียบว่าโมเดลที่ซับซ้อนกว่าดีขึ้นจริงไหม
"""

import json
import pickle
import subprocess
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

DATA = Path("data/processed")
MODEL_OUT = Path("models/model.pkl")
METRICS_OUT = Path("metrics.json")
CHAMPION = "champion"


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def current_champion_accuracy(client: MlflowClient, name: str) -> float:
    """accuracy ของโมเดลที่ใช้งานอยู่ (alias 'champion') ถ้ายังไม่มีคืน -1"""
    try:
        mv = client.get_model_version_by_alias(name, CHAMPION)
    except MlflowException:
        return -1.0
    return client.get_run(mv.run_id).data.metrics.get("accuracy", -1.0)


def main() -> None:
    params = yaml.safe_load(Path("params.yaml").read_text())
    p, cfg = params["train"], params["mlflow"]

    train = pd.read_parquet(DATA / "train.parquet")
    test = pd.read_parquet(DATA / "test.parquet")

    pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(
                max_features=p["max_features"],
                ngram_range=(1, p["ngram_max"]),
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(C=p["C"], max_iter=p["max_iter"])),
        ]
    )

    mlflow.set_tracking_uri(cfg["tracking_uri"])
    mlflow.set_experiment(cfg["experiment"])

    with mlflow.start_run() as run:
        # lineage: run นี้มาจาก code commit ไหนและข้อมูลชุดไหน
        mlflow.set_tags({"git_commit": git_sha(), "stage": "dvc-train"})
        mlflow.log_params(p)
        mlflow.log_params({"n_train": len(train), "n_test": len(test)})

        pipe.fit(train["text"], train["label"])
        preds = pipe.predict(test["text"])

        metrics = {
            "accuracy": round(accuracy_score(test["label"], preds), 4),
            "f1_macro": round(f1_score(test["label"], preds, average="macro"), 4),
        }
        mlflow.log_metrics(metrics)
        mlflow.log_text(classification_report(test["label"], preds), "classification_report.txt")
        model_info = mlflow.sklearn.log_model(pipe, artifact_path="model")
        print(f"run_id={run.info.run_id} metrics={metrics}")

        # --- quality gate + champion/challenger ---
        client = MlflowClient()
        champ_acc = current_champion_accuracy(client, cfg["model_name"])
        if metrics["accuracy"] < p["register_threshold"]:
            print(f"NOT registered: accuracy < threshold {p['register_threshold']}")
        else:
            mv = mlflow.register_model(model_info.model_uri, cfg["model_name"])
            if metrics["accuracy"] > champ_acc:
                client.set_registered_model_alias(cfg["model_name"], CHAMPION, mv.version)
                print(f"v{mv.version} is the new champion ({champ_acc} -> {metrics['accuracy']})")
            else:
                print(f"v{mv.version} registered as challenger (champion={champ_acc})")

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_OUT.open("wb") as f:
        pickle.dump(pipe, f)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
