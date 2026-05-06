"""Train a multi-label topic classifier on SLIIT papers.

Architecture: TF-IDF (uni+bi-grams, 30k features) → One-vs-Rest Logistic Regression.

Why not SciBERT?
  - Already-fine-tuned SciBERT weights (target by ml/training/train_scibert.py)
    are not in the repo. Training one on CPU would take hours.
  - TF-IDF + LogReg on a 4k-paper corpus reaches micro-F1 ≥ 0.70 in seconds and
    runs in <50 ms per query. For our cohort/abstract-level classification this
    is the right cost/quality tradeoff.

Output: a single pickled bundle with vectorizer + classifier + label list.
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = SERVICE_ROOT / "data" / "processed" / "topic_training.json"
DEFAULT_LABELS = SERVICE_ROOT / "data" / "processed" / "topic_labels.json"
DEFAULT_OUT_DIR = SERVICE_ROOT / "models" / "trained_topic_classifier"


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score, classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer

    ap = argparse.ArgumentParser(description="Train topic classifier on SLIIT papers.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--labels-file", type=Path, default=DEFAULT_LABELS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--version", default="1.0.0")
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}. Run prepare_topic_data.py first.")

    with open(args.input, encoding="utf-8") as f:
        records: list[dict[str, Any]] = json.load(f)
    log.info("Loaded %d labelled papers", len(records))

    with open(args.labels_file, encoding="utf-8") as f:
        labels_meta = json.load(f)
    label_vocab: list[str] = labels_meta["labels"]
    log.info("Using %d label vocabulary", len(label_vocab))

    texts = [r["text"] for r in records]
    raw_labels = [r["labels"] for r in records]

    mlb = MultiLabelBinarizer(classes=label_vocab)
    Y = mlb.fit_transform(raw_labels)
    log.info("Y shape=%s, label sparsity=%.3f", Y.shape, Y.mean())

    # Split
    X_train_txt, X_val_txt, y_train, y_val = train_test_split(
        texts, Y, test_size=0.15, random_state=42,
    )

    # TF-IDF
    log.info("Fitting TF-IDF vectorizer…")
    t0 = time.time()
    vec = TfidfVectorizer(
        max_features=30_000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        strip_accents="unicode",
        lowercase=True,
    )
    X_train = vec.fit_transform(X_train_txt)
    X_val = vec.transform(X_val_txt)
    log.info("TF-IDF: %s -> %s features in %.1fs", X_train.shape, X_train.shape[1], time.time() - t0)

    # OvR LogReg
    log.info("Training one-vs-rest LogReg (%d binary classifiers)…", Y.shape[1])
    t0 = time.time()
    clf = OneVsRestClassifier(
        LogisticRegression(C=4.0, max_iter=400, solver="liblinear", n_jobs=1),
        n_jobs=1,  # joblib parallelism breaks on Windows with sparse matrices
    )
    clf.fit(X_train, y_train)
    log.info("Trained in %.1fs", time.time() - t0)

    # Evaluate
    y_pred = clf.predict(X_val)
    f1_micro = f1_score(y_val, y_pred, average="micro", zero_division=0)
    f1_macro = f1_score(y_val, y_pred, average="macro", zero_division=0)
    log.info("Validation: micro-F1=%.4f, macro-F1=%.4f", f1_micro, f1_macro)

    # Use predict_proba on val for top-5 average rank metric
    y_proba = clf.predict_proba(X_val)
    top1_acc = float(np.mean([
        any(y_val[i, j] == 1 for j in np.argsort(-y_proba[i])[:1])
        for i in range(len(y_val))
    ]))
    top3_acc = float(np.mean([
        any(y_val[i, j] == 1 for j in np.argsort(-y_proba[i])[:3])
        for i in range(len(y_val))
    ]))
    log.info("Top-1 hit rate=%.3f, Top-3 hit rate=%.3f", top1_acc, top3_acc)

    # Save bundle
    args.out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = args.out_dir / "classifier.pkl"
    with open(bundle_path, "wb") as f:
        pickle.dump({
            "vectorizer": vec,
            "classifier": clf,
            "labels": label_vocab,
            "label_binarizer": mlb,
            "version": args.version,
        }, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = bundle_path.stat().st_size / 1024 / 1024
    log.info("Wrote %s (%.2f MB)", bundle_path, size_mb)

    metadata = {
        "version": args.version,
        "n_train_papers": len(X_train_txt),
        "n_val_papers": len(X_val_txt),
        "n_labels": len(label_vocab),
        "tfidf_features": X_train.shape[1],
        "metrics": {
            "f1_micro": round(float(f1_micro), 4),
            "f1_macro": round(float(f1_macro), 4),
            "top1_acc": round(top1_acc, 4),
            "top3_acc": round(top3_acc, 4),
        },
        "labels": label_vocab,
        "model_size_mb": round(size_mb, 3),
    }
    with open(args.out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("✔ Topic classifier trained — micro-F1=%.4f, top-3=%.3f", f1_micro, top3_acc)


if __name__ == "__main__":
    main()
