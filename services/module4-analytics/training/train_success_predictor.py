"""
Train Success Predictor — XGBoost binary classifier on SLIIT papers.

Uses quality features as input, predicts whether a paper would be considered
"successful" (high quality + publishable). Ground truth derived from:
- Combined quality score >= 0.55 → successful
- Has methodology keywords + citations + adequate length → successful

This gives a probabilistic prediction of project success likelihood.
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
import xgboost as xgb

_SERVICE_ROOT = Path(__file__).parent.parent
_DATA_DIR = _SERVICE_ROOT / "data"
_MODELS_DIR = _SERVICE_ROOT / "models"
_MODELS_DIR.mkdir(exist_ok=True)

OUT_MODEL_DIR = _MODELS_DIR / "trained_success_predictor"
OUT_MODEL_DIR.mkdir(exist_ok=True)


FEATURE_COLUMNS = [
    "word_count",
    "title_word_count",
    "sentence_count",
    "avg_word_length",
    "avg_sentence_length",
    "methodology_keywords_count",
    "author_count",
    "citation_signals",
    "year",
    "abstract_length",
    "title_length",
]


def load_data() -> pd.DataFrame:
    path = _DATA_DIR / "quality_training.json"
    if not path.exists():
        print(f"[!] Training data not found at {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    records = []
    for r in rows:
        record = dict(r["features"])
        record["overall_score"] = r["scores"]["overall"]
        records.append(record)
    df = pd.DataFrame(records)

    # Derive success label: top quality + sufficient signals
    # Threshold tuned for ~30% positive class (realistic publication rate)
    df["success"] = (
        (df["overall_score"] >= 0.62)
        & (df["abstract_length"] >= 500)
        & (df["methodology_keywords_count"] >= 2)
    ).astype(int)

    return df


def main():
    print("=" * 70)
    print("  TRAINING SUCCESS PREDICTOR (XGBoost Binary Classifier)")
    print("=" * 70 + "\n")

    df = load_data()
    print(f"[+] Loaded {len(df)} papers")

    pos_count = df["success"].sum()
    neg_count = len(df) - pos_count
    print(f"[+] Positive (success): {pos_count} ({pos_count/len(df)*100:.1f}%)")
    print(f"[+] Negative           : {neg_count} ({neg_count/len(df)*100:.1f}%)")

    X = df[FEATURE_COLUMNS].values
    y = df["success"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    print(f"\n[+] Train: {len(X_train)}  Test: {len(X_test)}\n")

    # Class imbalance handling
    scale_pos = neg_count / max(1, pos_count)
    print(f"[+] scale_pos_weight: {scale_pos:.2f}")

    print("[+] Training XGBoost classifier...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_pos,
        random_state=42,
        eval_metric="auc",
        verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print(f"\n[+] Test Accuracy: {accuracy:.4f}")
    print(f"[+] Test ROC-AUC : {auc:.4f}\n")

    print("[+] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Not Successful", "Successful"]))

    print("[+] Top features:")
    importance = model.feature_importances_
    for col, imp in sorted(zip(FEATURE_COLUMNS, importance), key=lambda x: -x[1])[:5]:
        print(f"   {col:30s} {imp:.4f}")

    # Save model
    out_pkl = OUT_MODEL_DIR / "success_model.pkl"
    with open(out_pkl, "wb") as f:
        pickle.dump({
            "model": model,
            "feature_columns": FEATURE_COLUMNS,
            "metrics": {"accuracy": accuracy, "roc_auc": auc},
            "version": "sliit-v1-success",
        }, f)
    print(f"\n[+] Saved model -> {out_pkl}")

    meta_path = OUT_MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "XGBoost Binary Classifier",
            "version": "sliit-v1-success",
            "feature_columns": FEATURE_COLUMNS,
            "metrics": {"accuracy": accuracy, "roc_auc": auc},
            "training_size": len(X_train),
            "test_size": len(X_test),
            "label_definition": "overall_score >= 0.62 AND abstract_length >= 500 AND methodology_keywords >= 2",
        }, f, indent=2)
    print(f"[+] Saved metadata -> {meta_path}")

    print("\n" + "=" * 70)
    print("  SUCCESS PREDICTOR TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
