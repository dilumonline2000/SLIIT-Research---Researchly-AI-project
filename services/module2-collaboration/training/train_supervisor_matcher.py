"""
SBERT Fine-tuning for SLIIT Supervisor-Student Matching
Module 2 – R26-IT-116

Fine-tunes a sentence-transformers model on labelled supervisor-student proposal pairs.
Trains on ContrastiveLoss with data augmentation (synonym substitution + hard negatives).

Run:
    python training/train_supervisor_matcher.py

Output:
    models/trained_supervisor_matcher/       – fine-tuned model checkpoint
    data/supervisors_with_embeddings.json    – all 74 supervisors with 384-dim embeddings
"""

import json
import os
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    evaluation,
)
from torch.utils.data import DataLoader

# ---- PATHS ----

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models" / "trained_supervisor_matcher"
SUPERVISORS_F = DATA_DIR / "sliit_supervisors.json"
PAIRS_F = DATA_DIR / "training_pairs.json"
OUTPUT_EMB_F = DATA_DIR / "supervisors_with_embeddings.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ---- CONFIG ----

CONFIG = {
    "base_model": "sentence-transformers/all-MiniLM-L6-v2",
    "epochs": 15,
    "batch_size": 16,
    "warmup_steps": 10,
    "learning_rate": 2e-5,
    "val_split": 0.15,
    "seed": 42,
}

random.seed(CONFIG["seed"])
np.random.seed(CONFIG["seed"])


# ---- HELPERS ----

def build_supervisor_text(sup: dict) -> str:
    """
    Build a rich text representation of a supervisor for embedding.
    Combines name, research interests, keywords, department, cluster.
    """
    interests = "; ".join(sup.get("research_interests", []))
    keywords = sup.get("keywords", "")
    dept = sup.get("department", "")
    cluster = sup.get("research_cluster", "")
    name = sup.get("name", "")
    level = sup.get("level", "")

    parts = [
        f"Supervisor: {level} {name}" if level and name else f"Supervisor: {name}",
        f"Department: {dept}" if dept else None,
        f"Research Cluster: {cluster}" if cluster else None,
        f"Research Interests: {interests}" if interests else None,
        f"Keywords: {keywords}" if keywords else None,
    ]
    # Filter out None values and join
    return ". ".join(p for p in parts if p)


def load_data():
    """Load supervisors and training pairs from JSON files."""
    with open(SUPERVISORS_F, encoding="utf-8") as f:
        supervisors = json.load(f)
    with open(PAIRS_F, encoding="utf-8") as f:
        pairs = json.load(f)

    sup_map = {s["id"]: s for s in supervisors}
    print(f"[+] Loaded {len(supervisors)} supervisors, {len(pairs)} training pairs")
    return supervisors, pairs, sup_map


def build_training_examples(pairs: list, sup_map: dict) -> list:
    """
    Convert raw pairs into SBERT InputExamples.
    Format: (student_query_text, supervisor_text, label)
    label: 1.0 = good match, 0.0 = poor match
    """
    examples = []
    skipped = 0

    for query, sup_id, label in pairs:
        sup = sup_map.get(sup_id)
        if not sup:
            skipped += 1
            continue
        if not sup.get("research_interests") and not sup.get("keywords"):
            skipped += 1
            continue

        sup_text = build_supervisor_text(sup)
        examples.append(InputExample(texts=[query, sup_text], label=float(label)))

    print(f"[+] Built {len(examples)} training examples (skipped {skipped})")
    return examples


def augment_training_data(pairs: list, sup_map: dict) -> list:
    """
    Augment training data by:
    1. Paraphrasing student queries (simple word substitution)
    2. Creating hard negatives (supervisors from different research areas)
    """
    augmented = list(pairs)

    # Word-level augmentations for student queries
    synonyms = {
        "research": ["study", "investigate", "explore", "analyze"],
        "build": ["develop", "create", "implement", "design"],
        "using": ["with", "leveraging", "employing", "applying"],
        "machine learning": ["ML", "statistical learning", "data-driven models"],
        "deep learning": ["neural networks", "DL", "deep neural networks"],
        "IoT": ["Internet of Things", "connected devices", "smart devices"],
        "NLP": ["natural language processing", "text processing", "language AI"],
        "security": ["cybersecurity", "information security", "data protection"],
        "system": ["platform", "framework", "solution", "application"],
        "propose": ["plan to", "intend to", "aim to", "want to"],
        "classification": ["categorization", "labeling", "prediction"],
        "detection": ["recognition", "identification", "discovery"],
        "AR/VR": ["augmented reality", "virtual reality", "immersive"],
        "5G": ["fifth generation", "wireless networks"],
        "blockchain": ["distributed ledger", "cryptocurrency"],
    }

    positive_pairs = [(q, sid, l) for q, sid, l in pairs if l == 1]

    # Augment by synonym substitution
    for query, sup_id, label in positive_pairs:
        aug_query = query
        for original, replacements in synonyms.items():
            if original.lower() in aug_query.lower():
                replacement = random.choice(replacements)
                aug_query = aug_query.replace(original, replacement, 1)
                break  # One substitution per query

        if aug_query != query:
            augmented.append((aug_query, sup_id, 1))

    # Hard negatives: same query, wrong supervisor from different domain
    # Manually curated domain groups from the full 74-supervisor list
    domain_groups = {
        "NLP_AI": [1, 2, 4, 26, 33, 39, 56, 65],
        "IoT_Systems": [3, 16, 35, 36, 54, 67],
        "Security": [15, 30, 38, 53, 69, 71, 22],
        "Education": [5, 6, 14, 29, 32, 45, 51],
        "Vision": [20, 37, 41, 62, 65, 21],
        "Data": [12, 13, 17, 18, 49, 50, 48, 59],
        "Networking": [27, 34, 57, 63, 36, 57, 71],
        "Software": [9, 25, 50, 59, 61, 40],
        "Speech": [21, 39],
        "Specialized": [11, 19, 23, 24, 28, 31, 43, 44, 46, 47, 52, 58, 60, 68, 72, 74],
    }

    # Map supervisor → domain
    sup_domain = {}
    for domain, ids in domain_groups.items():
        for sid in ids:
            sup_domain[sid] = domain

    # Create hard negatives for first 20 positive pairs
    for query, sup_id, label in positive_pairs[:20]:
        src_domain = sup_domain.get(sup_id)
        if not src_domain:
            continue
        # Pick a supervisor from a DIFFERENT domain as hard negative
        for domain, ids in domain_groups.items():
            if domain != src_domain and ids:
                neg_id = random.choice(ids)
                augmented.append((query, neg_id, 0))
                break

    print(f"[+] Augmented to {len(augmented)} total pairs")
    return augmented


def split_data(examples: list, val_ratio: float = 0.15):
    """Split into train and validation sets."""
    random.shuffle(examples)
    val_size = max(1, int(len(examples) * val_ratio))
    val_set = examples[:val_size]
    train_set = examples[val_size:]
    print(f"[+] Train: {len(train_set)}, Val: {len(val_set)}")
    return train_set, val_set


# ---- MAIN TRAINING ----

def train():
    print("\n" + "=" * 70)
    print("  SBERT SUPERVISOR MATCHING – TRAINING PIPELINE")
    print("  R26-IT-116 | Module 2 | " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 70 + "\n")

    # 1. Load data
    supervisors, pairs, sup_map = load_data()

    # 2. Augment training data
    augmented_pairs = augment_training_data(pairs, sup_map)

    # 3. Build SBERT InputExamples
    all_examples = build_training_examples(augmented_pairs, sup_map)

    # 4. Train / Val split
    train_examples, val_examples = split_data(all_examples, CONFIG["val_split"])

    # 5. Load base model
    print(f"\n[*] Loading base model: {CONFIG['base_model']}")
    model = SentenceTransformer(CONFIG["base_model"])
    print("[+] Base model loaded")

    # 6. DataLoader + Loss
    train_loader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=CONFIG["batch_size"],
    )
    train_loss = losses.ContrastiveLoss(model=model)

    # 7. Evaluator on validation set
    val_sentences1 = [e.texts[0] for e in val_examples]
    val_sentences2 = [e.texts[1] for e in val_examples]
    val_labels = [e.label for e in val_examples]

    evaluator = evaluation.BinaryClassificationEvaluator(
        sentences1=val_sentences1,
        sentences2=val_sentences2,
        labels=val_labels,
        name="supervisor_val",
    )

    # 8. Train
    print(f"\n[=] Training for {CONFIG['epochs']} epochs...")
    print(f"   Batch size:   {CONFIG['batch_size']}")
    print(f"   Warmup steps: {CONFIG['warmup_steps']}")
    print(f"   Output path:  {MODEL_DIR}\n")

    model.fit(
        train_objectives=[(train_loader, train_loss)],
        evaluator=evaluator,
        epochs=CONFIG["epochs"],
        warmup_steps=CONFIG["warmup_steps"],
        output_path=str(MODEL_DIR),
        show_progress_bar=True,
        save_best_model=True,
    )

    print(f"\n[+] Training complete! Model saved to: {MODEL_DIR}")

    # 9. Generate supervisor embeddings using fine-tuned model
    print("\n[>>] Generating supervisor embeddings with fine-tuned model...")
    fine_tuned = SentenceTransformer(str(MODEL_DIR))

    for sup in tqdm(supervisors, desc="Embedding supervisors"):
        text = build_supervisor_text(sup)
        sup["embedding_text"] = text
        sup["embedding"] = fine_tuned.encode(text).tolist()
        sup["embedding_dim"] = 384  # all-MiniLM-L6-v2 output dim

    # 10. Save supervisors with embeddings
    with open(OUTPUT_EMB_F, "w", encoding="utf-8") as f:
        json.dump(supervisors, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved embeddings -> {OUTPUT_EMB_F}")
    print(f"\n{'=' * 70}")
    print("  TRAINING PIPELINE COMPLETE")
    print(f"  Next: python training/evaluate_model.py")
    print(f"  Then: python training/upload_to_supabase.py")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    train()
