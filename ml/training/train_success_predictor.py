"""Model 8: Success Prediction — RF + XGBoost ensemble.

Architecture: Random Forest + XGBoost with soft voting
Features: 10 research progress indicators
Target: F1 >= 0.75, ROC-AUC >= 0.80

Usage:
    python ml/training/train_success_predictor.py
    python ml/training/train_success_predictor.py --cv-folds 5
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    f1_score, roc_auc_score, classification_report, accuracy_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FEATURES = [
    "milestone_completion_rate",
    "login_frequency",
    "submission_frequency",
    "quality_score_trajectory",
    "supervisor_interaction_frequency",
    "topic_trend_alignment",
    "peer_collaboration_score",
    "citation_count",
    "feedback_sentiment_avg",
    "days_since_last_submission",
]


def load_data(data_dir: str) -> tuple[pd.DataFrame, np.ndarray]:
    """Load research progress features and success labels."""
    data_file = Path(data_dir) / "student_progress.csv"
    if data_file.exists():
        df = pd.read_csv(data_file)
        X = df[FEATURES]
        y = df["success"].values
        return X, y

    json_file = Path(data_dir) / "student_progress.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame(records)
        X = df[FEATURES]
        y = df["success"].values
        return X, y

    logger.warning("No progress data found, generating synthetic data")
    return _synthetic_data()


def _synthetic_data() -> tuple[pd.DataFrame, np.ndarray]:
    """Generate synthetic student progress data."""
    np.random.seed(42)
    n_samples = 500

    # Successful students (60%)
    n_success = int(n_samples * 0.6)
    n_fail = n_samples - n_success

    def gen_features(n, success=True):
        if success:
            return {
                "milestone_completion_rate": np.random.uniform(0.6, 1.0, n),
                "login_frequency": np.random.uniform(3, 7, n),
                "submission_frequency": np.random.uniform(2, 5, n),
                "quality_score_trajectory": np.random.uniform(0.3, 1.0, n),
                "supervisor_interaction_frequency": np.random.uniform(1, 4, n),
                "topic_trend_alignment": np.random.uniform(0.4, 1.0, n),
                "peer_collaboration_score": np.random.uniform(0.3, 1.0, n),
                "citation_count": np.random.randint(5, 30, n).astype(float),
                "feedback_sentiment_avg": np.random.uniform(0.3, 1.0, n),
                "days_since_last_submission": np.random.uniform(1, 14, n),
            }
        else:
            return {
                "milestone_completion_rate": np.random.uniform(0.1, 0.5, n),
                "login_frequency": np.random.uniform(0.5, 3, n),
                "submission_frequency": np.random.uniform(0.2, 2, n),
                "quality_score_trajectory": np.random.uniform(-0.5, 0.4, n),
                "supervisor_interaction_frequency": np.random.uniform(0.1, 1.5, n),
                "topic_trend_alignment": np.random.uniform(0.0, 0.5, n),
                "peer_collaboration_score": np.random.uniform(0.0, 0.4, n),
                "citation_count": np.random.randint(0, 8, n).astype(float),
                "feedback_sentiment_avg": np.random.uniform(-0.5, 0.3, n),
                "days_since_last_submission": np.random.uniform(14, 60, n),
            }

    success_feats = gen_features(n_success, True)
    fail_feats = gen_features(n_fail, False)

    data = {k: np.concatenate([success_feats[k], fail_feats[k]]) for k in FEATURES}
    X = pd.DataFrame(data)
    y = np.array([1] * n_success + [0] * n_fail)

    # Shuffle
    idx = np.random.permutation(len(y))
    return X.iloc[idx].reset_index(drop=True), y[idx]


def train_success_predictor(
    output_dir: str = "services/module4-analytics/models/prediction",
    data_dir: str = "ml/data/processed/performance",
    cv_folds: int = 5,
    use_smote: bool = True,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    X, y = load_data(data_dir)
    logger.info("Loaded %d samples (%d positive, %d negative)", len(y), sum(y), len(y) - sum(y))

    # Split
    train_end = int(len(X) * 0.70)
    val_end = int(len(X) * 0.85)

    X_train, y_train = X.iloc[:train_end], y[:train_end]
    X_val, y_val = X.iloc[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X.iloc[val_end:], y[val_end:]

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # SMOTE for class imbalance
    if use_smote and HAS_SMOTE:
        smote = SMOTE(random_state=42)
        X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
        logger.info("After SMOTE: %d samples", len(y_train))
    elif use_smote:
        logger.warning("imbalanced-learn not installed — skipping SMOTE")

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=8,
        min_samples_split=5, min_samples_leaf=2,
        max_features="sqrt", class_weight="balanced",
        random_state=42, n_jobs=-1,
    )

    # XGBoost
    if HAS_XGB:
        xgb_clf = xgb.XGBClassifier(
            n_estimators=200, max_depth=6,
            learning_rate=0.1, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0,
            eval_metric="logloss", random_state=42,
            use_label_encoder=False,
        )
        # Ensemble
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("xgb", xgb_clf)],
            voting="soft",
        )
    else:
        logger.warning("xgboost not installed — using RF only")
        ensemble = rf

    # Cross-validation
    logger.info("Running %d-fold cross-validation...", cv_folds)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(ensemble, X_train_scaled, y_train, cv=cv, scoring="f1")
    logger.info("CV F1 scores: %s (mean=%.4f)", [f"{s:.4f}" for s in cv_scores], cv_scores.mean())

    # Train on full training set
    ensemble.fit(X_train_scaled, y_train)

    # Validate
    val_preds = ensemble.predict(X_val_scaled)
    val_proba = ensemble.predict_proba(X_val_scaled)[:, 1] if hasattr(ensemble, "predict_proba") else val_preds.astype(float)
    val_f1 = f1_score(y_val, val_preds)
    val_auc = roc_auc_score(y_val, val_proba)
    logger.info("Validation — F1: %.4f, ROC-AUC: %.4f", val_f1, val_auc)

    # Test
    test_preds = ensemble.predict(X_test_scaled)
    test_proba = ensemble.predict_proba(X_test_scaled)[:, 1] if hasattr(ensemble, "predict_proba") else test_preds.astype(float)
    test_f1 = f1_score(y_test, test_preds)
    test_auc = roc_auc_score(y_test, test_proba)
    test_acc = accuracy_score(y_test, test_preds)

    logger.info("Test — F1: %.4f, ROC-AUC: %.4f, Accuracy: %.4f", test_f1, test_auc, test_acc)
    logger.info("Test classification report:\n%s", classification_report(y_test, test_preds, target_names=["fail", "success"]))

    # Save
    joblib.dump(ensemble, output_path / "ensemble_model.pkl")
    joblib.dump(scaler, output_path / "scaler.pkl")

    metadata = {
        "model": "success-predictor",
        "type": "rf-xgboost-ensemble" if HAS_XGB else "random-forest",
        "features": FEATURES,
        "cv_f1_mean": float(cv_scores.mean()),
        "cv_f1_std": float(cv_scores.std()),
        "val_f1": float(val_f1),
        "val_roc_auc": float(val_auc),
        "test_f1": float(test_f1),
        "test_roc_auc": float(test_auc),
        "test_accuracy": float(test_acc),
        "train_size": len(y_train),
        "val_size": len(y_val),
        "test_size": len(y_test),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    with open(output_path / "feature_names.json", "w") as f:
        json.dump(FEATURES, f, indent=2)

    logger.info("Success predictor training complete. Test F1=%.4f, AUC=%.4f", test_f1, test_auc)


def main():
    parser = argparse.ArgumentParser(description="Train success prediction ensemble")
    parser.add_argument("--output", default="services/module4-analytics/models/prediction")
    parser.add_argument("--data", default="ml/data/processed/performance")
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--no-smote", action="store_true")
    args = parser.parse_args()
    train_success_predictor(
        output_dir=args.output, data_dir=args.data,
        cv_folds=args.cv_folds, use_smote=not args.no_smote,
    )


if __name__ == "__main__":
    main()
