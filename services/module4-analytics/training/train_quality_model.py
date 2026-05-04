"""
Train Quality Score Predictor — XGBoost regression on SLIIT papers.

Predicts: overall_score, originality, citation_impact, methodology, clarity
Features: word_count, sentence stats, methodology_keywords, citation_signals,
          author_count, year, abstract/title length, topic embedding
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Paths
_SERVICE_ROOT = Path(__file__).parent.parent
_DATA_DIR = _SERVICE_ROOT / "data"
_MODELS_DIR = _SERVICE_ROOT / "models"
_MODELS_DIR.mkdir(exist_ok=True)

OUT_MODEL_DIR = _MODELS_DIR / "trained_quality_predictor"
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

TARGET_COLUMNS = [
    "originality",
    "citation_impact",
    "methodology",
    "clarity",
    "overall",
]


def load_data() -> pd.DataFrame:
    path = _DATA_DIR / "quality_training.json"
    if not path.exists():
        print(f"[!] Training data not found at {path}")
        print("    Run: python training/prepare_training_data.py")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    records = []
    for r in rows:
        record = dict(r["features"])
        for k, v in r["scores"].items():
            record[f"target_{k}"] = v
        records.append(record)
    df = pd.DataFrame(records)
    print(f"[+] Loaded {len(df)} training rows")
    return df


def train_one_target(X_train, X_test, y_train, y_test, target_name: str) -> tuple:
    """Train XGBoost for one target dimension."""
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective="reg:squarederror",
        verbosity=0,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"   [{target_name:18s}] MAE={mae:.4f}  RMSE={np.sqrt(mse):.4f}  R²={r2:.4f}")
    return model, {"mae": mae, "rmse": float(np.sqrt(mse)), "r2": r2}


def main():
    print("=" * 70)
    print("  TRAINING QUALITY SCORE PREDICTOR (XGBoost)")
    print("=" * 70 + "\n")

    df = load_data()

    X = df[FEATURE_COLUMNS].values
    y_dict = {tgt: df[f"target_{tgt}"].values for tgt in TARGET_COLUMNS}

    # Split once for consistent train/test
    X_train, X_test, *_ = train_test_split(X, y_dict["overall"], test_size=0.15, random_state=42)
    train_idx, test_idx = train_test_split(range(len(X)), test_size=0.15, random_state=42)
    X_train, X_test = X[train_idx], X[test_idx]

    print(f"\n[+] Train: {len(X_train)}  Test: {len(X_test)}\n")
    print("[+] Training one model per dimension...\n")

    models = {}
    metrics = {}
    for target in TARGET_COLUMNS:
        y_train = y_dict[target][train_idx]
        y_test = y_dict[target][test_idx]
        model, m = train_one_target(X_train, X_test, y_train, y_test, target)
        models[target] = model
        metrics[target] = m

    # Save all models in one pickle file
    out_pkl = OUT_MODEL_DIR / "quality_models.pkl"
    with open(out_pkl, "wb") as f:
        pickle.dump({
            "models": models,
            "feature_columns": FEATURE_COLUMNS,
            "target_columns": TARGET_COLUMNS,
            "metrics": metrics,
            "version": "sliit-v1-quality",
        }, f)
    print(f"\n[+] Saved models -> {out_pkl}")

    # Save metadata
    meta_path = OUT_MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "XGBoost Multi-Target Regressor",
            "version": "sliit-v1-quality",
            "training_size": len(X_train),
            "test_size": len(X_test),
            "feature_columns": FEATURE_COLUMNS,
            "target_columns": TARGET_COLUMNS,
            "metrics": metrics,
            "weights": {
                "originality": 0.30,
                "citation_impact": 0.25,
                "methodology": 0.25,
                "clarity": 0.20,
            },
        }, f, indent=2)
    print(f"[+] Saved metadata -> {meta_path}")

    # Show feature importance for overall
    print("\n[+] Feature importance (overall score):")
    importance = models["overall"].feature_importances_
    for col, imp in sorted(zip(FEATURE_COLUMNS, importance), key=lambda x: -x[1]):
        bar = "#" * int(imp * 50)
        print(f"   {col:30s} {imp:.4f}  {bar}")

    print("\n" + "=" * 70)
    print("  QUALITY MODEL TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
