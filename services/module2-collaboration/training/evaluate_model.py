"""
Evaluate the fine-tuned SBERT supervisor matching model.

Run:
    python training/evaluate_model.py

Prints:
    - Accuracy, Precision, Recall, F1 on test queries
    - Top-5 matches for sample student proposals
    - Confusion matrix
    - Saves results to data/evaluation_results.json
"""

import json
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models" / "trained_supervisor_matcher"
RESULTS_FILE = DATA_DIR / "evaluation_results.json"

SIMILARITY_THRESHOLD = 0.60  # Score above this = match


def cosine_similarity(a: list, b: list) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def evaluate():
    print("\n" + "=" * 70)
    print("  SUPERVISOR MATCHING MODEL - EVALUATION")
    print("=" * 70 + "\n")

    # Load fine-tuned model
    print("[*] Loading fine-tuned model...")
    model = SentenceTransformer(str(MODEL_DIR))

    # Load supervisors with embeddings
    with open(DATA_DIR / "supervisors_with_embeddings.json", encoding="utf-8") as f:
        supervisors = json.load(f)
    with open(DATA_DIR / "training_pairs.json") as f:
        pairs = json.load(f)

    sup_map = {s["id"]: s for s in supervisors}

    # ---- QUANTITATIVE EVALUATION ----

    print("[#] Running quantitative evaluation on training pairs...\n")

    y_true, y_pred = [], []

    for query, sup_id, label in pairs:
        sup = sup_map.get(sup_id)
        if not sup or not sup.get("embedding"):
            continue

        query_emb = model.encode(query).tolist()
        sim = cosine_similarity(query_emb, sup["embedding"])
        predicted = 1 if sim >= SIMILARITY_THRESHOLD else 0

        y_true.append(int(label))
        y_pred.append(predicted)

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()

    print(f"  Accuracy:   {acc:.4f}  ({acc * 100:.1f}%)")
    print(f"  Precision:  {prec:.4f}")
    print(f"  Recall:     {rec:.4f}")
    print(f"  F1 Score:   {f1:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"  [[TN={cm[0][0]:3d}  FP={cm[0][1]:3d}]")
    print(f"   [FN={cm[1][0]:3d}  TP={cm[1][1]:3d}]]")

    target_met = "[+] PASS" if f1 >= 0.75 else "[!] NEEDS IMPROVEMENT - need more training data or epochs"
    print(f"\n  Target F1 >= 0.75: {target_met}")

    # ---- QUALITATIVE EVALUATION ----

    print("\n" + "-" * 70)
    print("[>>] Top-5 matches for sample student proposals:\n")

    test_proposals = [
        "I want to research natural language processing and build a text classification system using BERT.",
        "My project is about IoT-based smart agriculture systems using sensor networks.",
        "I am working on deep reinforcement learning for robotics control systems.",
        "My research involves cyber security and network intrusion detection using ML.",
        "I want to study e-learning platforms and personalized education using AI.",
        "My project is about computer vision and medical image analysis using CNNs.",
        "I am researching big data analytics and business intelligence dashboards.",
    ]

    qualitative_results = []

    for proposal in test_proposals:
        query_emb = model.encode(proposal).tolist()

        # Score all supervisors
        scored = []
        for sup in supervisors:
            if not sup.get("embedding"):
                continue
            sim = cosine_similarity(query_emb, sup["embedding"])
            scored.append(
                {
                    "id": sup["id"],
                    "name": sup["name"],
                    "department": sup["department"],
                    "interests": ", ".join(sup.get("research_interests", [])[:3]),
                    "similarity": round(sim, 4),
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top5 = scored[:5]

        print(f'  Query: "{proposal[:65]}..."')
        for rank, s in enumerate(top5, 1):
            bar = "#" * int(s["similarity"] * 20)
            print(f"  {rank}. {s['name']:<35} {s['similarity']:.3f} {bar}")
        print()

        qualitative_results.append(
            {
                "query": proposal,
                "top5": top5,
            }
        )

    # ---- SAVE RESULTS ----

    results = {
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "threshold": SIMILARITY_THRESHOLD,
            "target_f1": 0.75,
            "target_met": f1 >= 0.75,
        },
        "confusion_matrix": cm,
        "qualitative": qualitative_results,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Evaluation results saved -> {RESULTS_FILE}")
    print(f"\nNext step: python training/upload_to_supabase.py\n")


if __name__ == "__main__":
    evaluate()
