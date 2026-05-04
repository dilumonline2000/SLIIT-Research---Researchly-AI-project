"""
Train Topic Classifier — SBERT embeddings + Logistic Regression head.

Uses lightweight all-MiniLM-L6-v2 for embedding (no fine-tuning needed),
classifies into: computing, business, social_sciences, engineering, health, sciences.
"""

import json
import logging
import pickle
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# Suppress noisy logs
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer

# Paths
_SERVICE_ROOT = Path(__file__).parent.parent
_DATA_DIR = _SERVICE_ROOT / "data"
_MODELS_DIR = _SERVICE_ROOT / "models"
_MODELS_DIR.mkdir(exist_ok=True)

OUT_MODEL_DIR = _MODELS_DIR / "trained_topic_classifier"
OUT_MODEL_DIR.mkdir(exist_ok=True)

SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_data():
    path = _DATA_DIR / "topic_training.json"
    if not path.exists():
        print(f"[!] Training data not found at {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    texts = [r["text"] for r in rows]
    labels = [r["label"] for r in rows]
    return texts, labels


def main():
    print("=" * 70)
    print("  TRAINING TOPIC CLASSIFIER (SBERT + LogisticRegression)")
    print("=" * 70 + "\n")

    texts, labels = load_data()
    print(f"[+] Loaded {len(texts)} training rows")

    label_counts = Counter(labels)
    print(f"[+] Class distribution:")
    for lbl, cnt in label_counts.most_common():
        print(f"    {lbl:20s}: {cnt:5d}")

    # Encode texts with SBERT
    print(f"\n[+] Loading SBERT model: {SBERT_MODEL}")
    encoder = SentenceTransformer(SBERT_MODEL)
    print(f"[+] Encoding {len(texts)} texts...")
    embeddings = encoder.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    print(f"[+] Embeddings shape: {embeddings.shape}")

    # Train classifier head
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, labels, test_size=0.15, random_state=42, stratify=labels
    )
    print(f"[+] Train: {len(X_train)}  Test: {len(X_test)}\n")

    print("[+] Training LogisticRegression head...")
    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")

    print(f"\n[+] Test accuracy : {accuracy:.4f}")
    print(f"[+] F1 (macro)    : {f1_macro:.4f}")
    print(f"[+] F1 (weighted) : {f1_weighted:.4f}\n")

    print("[+] Per-class report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save classifier head + label info
    out_pkl = OUT_MODEL_DIR / "classifier.pkl"
    with open(out_pkl, "wb") as f:
        pickle.dump({
            "classifier": clf,
            "labels": list(clf.classes_),
            "encoder_name": SBERT_MODEL,
            "version": "sliit-v1-topic",
        }, f)
    print(f"[+] Saved classifier head -> {out_pkl}")

    # Save metadata
    meta_path = OUT_MODEL_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_type": "SBERT + LogisticRegression",
            "version": "sliit-v1-topic",
            "encoder": SBERT_MODEL,
            "labels": list(clf.classes_),
            "metrics": {
                "accuracy": accuracy,
                "f1_macro": f1_macro,
                "f1_weighted": f1_weighted,
            },
            "training_size": len(X_train),
            "test_size": len(X_test),
        }, f, indent=2)
    print(f"[+] Saved metadata -> {meta_path}")

    print("\n" + "=" * 70)
    print("  TOPIC CLASSIFIER TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
