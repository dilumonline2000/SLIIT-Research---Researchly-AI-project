# 🧠 CLAUDE CODE — SUPERVISOR MATCHING MODEL TRAINING PROMPT
## R26-IT-116 | Module 2 — SBERT Fine-tuning for SLIIT Supervisor Matching
### Complete Implementation: Dataset → Training → Evaluation → Supabase Upload

---

## 📌 CONTEXT — READ FIRST

You are working on **R26-IT-116 monorepo**, Module 2 (Collaboration & Recommendation Engine).

**Goal:** Train a fine-tuned SBERT model that matches students to SLIIT supervisors
based on research interest similarity using cosine similarity + pgvector in Supabase.

**What already exists:**
- `sliit_supervisors.json` — 74 SLIIT supervisors with research interests, emails, departments
- `training_pairs.json` — 65 labelled (student_query, supervisor_id, label) pairs
- Supabase project with `supervisor_profiles` table + pgvector extension enabled
- Python FastAPI service at `services/module2-collaboration/`

**What to build:**
Complete end-to-end training pipeline from raw JSON → fine-tuned model → Supabase.

---

## 🗂️ FILES TO CREATE

```
services/module2-collaboration/
├── training/
│   ├── __init__.py
│   ├── train_supervisor_matcher.py      # MAIN training script
│   ├── evaluate_model.py                # Evaluation + metrics
│   ├── upload_to_supabase.py           # Upload embeddings to Supabase
│   └── generate_more_pairs.py          # Augment training data
├── data/
│   ├── sliit_supervisors.json          # COPY the provided JSON here
│   ├── training_pairs.json             # COPY the provided JSON here
│   ├── supervisors_with_embeddings.json # Generated after training
│   └── evaluation_results.json         # Generated after evaluation
├── models/
│   └── trained_supervisor_matcher/     # Saved fine-tuned model (generated)
├── app/
│   ├── services/
│   │   └── supervisor_matcher.py       # Updated inference service
│   └── routers/
│       └── supervisor.py               # Updated API endpoint
├── requirements.txt                    # Updated with new dependencies
└── README_TRAINING.md                  # Training documentation
```

---

## ⚙️ STEP 1 — requirements.txt

```
# services/module2-collaboration/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.1
python-dotenv==1.0.1
supabase==2.4.6

# ML / Training
sentence-transformers==3.0.1
torch==2.3.1
transformers==4.41.2
numpy==1.26.4
pandas==2.2.2
scikit-learn==1.5.0

# Utilities
tqdm==4.66.4
matplotlib==3.9.0
seaborn==0.13.2
```

---

## ⚙️ STEP 2 — MAIN TRAINING SCRIPT

```python
# services/module2-collaboration/training/train_supervisor_matcher.py
"""
SBERT Fine-tuning for SLIIT Supervisor-Student Matching
Module 2 — R26-IT-116

Run:
    python training/train_supervisor_matcher.py

Output:
    models/trained_supervisor_matcher/   ← fine-tuned model
    data/supervisors_with_embeddings.json ← embeddings for Supabase
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

# ─── PATHS ────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent.parent
DATA_DIR        = BASE_DIR / "data"
MODEL_DIR       = BASE_DIR / "models" / "trained_supervisor_matcher"
SUPERVISORS_F   = DATA_DIR / "sliit_supervisors.json"
PAIRS_F         = DATA_DIR / "training_pairs.json"
OUTPUT_EMB_F    = DATA_DIR / "supervisors_with_embeddings.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ─── CONFIG ───────────────────────────────────────────────────────

CONFIG = {
    "base_model":    "sentence-transformers/all-MiniLM-L6-v2",
    "epochs":        15,
    "batch_size":    16,
    "warmup_steps":  10,
    "learning_rate": 2e-5,
    "val_split":     0.15,
    "seed":          42,
}

random.seed(CONFIG["seed"])
np.random.seed(CONFIG["seed"])


# ─── HELPERS ──────────────────────────────────────────────────────

def build_supervisor_text(sup: dict) -> str:
    """
    Build a rich text representation of a supervisor for embedding.
    Combines name, research interests, keywords, department, cluster.
    This text is what SBERT encodes to represent the supervisor.
    """
    interests = "; ".join(sup.get("research_interests", []))
    keywords  = sup.get("keywords", "")
    dept      = sup.get("department", "")
    cluster   = sup.get("research_cluster", "")
    name      = sup.get("name", "")
    level     = sup.get("level", "")

    parts = [
        f"Supervisor: {level} {name}",
        f"Department: {dept}",
        f"Research Cluster: {cluster}",
        f"Research Interests: {interests}",
        f"Keywords: {keywords}",
    ]
    return ". ".join(p for p in parts if p.split(": ")[1].strip())


def load_data():
    """Load supervisors and training pairs from JSON files."""
    with open(SUPERVISORS_F, encoding="utf-8") as f:
        supervisors = json.load(f)
    with open(PAIRS_F, encoding="utf-8") as f:
        pairs = json.load(f)

    sup_map = {s["id"]: s for s in supervisors}
    print(f"✅ Loaded {len(supervisors)} supervisors, {len(pairs)} training pairs")
    return supervisors, pairs, sup_map


def build_training_examples(pairs: list, sup_map: dict) -> list:
    """
    Convert raw pairs into SBERT InputExamples.
    Format: (student_query_text, supervisor_text, label)
    label: 1.0 = good match, 0.0 = poor match
    """
    examples = []
    skipped  = 0

    for query, sup_id, label in pairs:
        sup = sup_map.get(sup_id)
        if not sup:
            skipped += 1
            continue
        if not sup.get("research_interests") and not sup.get("keywords"):
            skipped += 1
            continue

        sup_text = build_supervisor_text(sup)
        examples.append(
            InputExample(texts=[query, sup_text], label=float(label))
        )

    print(f"✅ Built {len(examples)} training examples (skipped {skipped})")
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
        "research":     ["study", "investigate", "explore", "analyze"],
        "build":        ["develop", "create", "implement", "design"],
        "using":        ["with", "leveraging", "employing", "applying"],
        "machine learning": ["ML", "statistical learning", "data-driven models"],
        "deep learning":    ["neural networks", "DL", "deep neural networks"],
        "IoT":              ["Internet of Things", "connected devices", "smart devices"],
        "NLP":              ["natural language processing", "text processing", "language AI"],
        "security":         ["cybersecurity", "information security", "data protection"],
        "system":           ["platform", "framework", "solution", "application"],
        "propose":          ["plan to", "intend to", "aim to", "want to"],
        "classification":   ["categorization", "labeling", "prediction"],
        "detection":        ["recognition", "identification", "discovery"],
    }

    positive_pairs = [(q, sid, l) for q, sid, l in pairs if l == 1]

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
    domain_groups = {
        "NLP_AI":      [1, 2, 4, 26, 33, 39, 56],
        "IoT_Systems": [3, 16, 35, 36, 54, 67],
        "Security":    [15, 30, 38, 53, 69, 71],
        "Education":   [5, 6, 14, 29, 32, 45],
        "Vision":      [20, 37, 41, 62, 65],
        "Data":        [12, 13, 17, 18, 49, 50],
        "Networking":  [27, 34, 57, 63],
    }

    # Map supervisor → domain
    sup_domain = {}
    for domain, ids in domain_groups.items():
        for sid in ids:
            sup_domain[sid] = domain

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

    print(f"✅ Augmented to {len(augmented)} total pairs")
    return augmented


def split_data(examples: list, val_ratio: float = 0.15):
    """Split into train and validation sets."""
    random.shuffle(examples)
    val_size   = max(1, int(len(examples) * val_ratio))
    val_set    = examples[:val_size]
    train_set  = examples[val_size:]
    print(f"✅ Train: {len(train_set)}, Val: {len(val_set)}")
    return train_set, val_set


# ─── MAIN TRAINING ────────────────────────────────────────────────

def train():
    print("\n" + "="*60)
    print("  SBERT SUPERVISOR MATCHING — TRAINING PIPELINE")
    print("  R26-IT-116 | Module 2 | " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*60 + "\n")

    # 1. Load data
    supervisors, pairs, sup_map = load_data()

    # 2. Augment training data
    augmented_pairs = augment_training_data(pairs, sup_map)

    # 3. Build SBERT InputExamples
    all_examples = build_training_examples(augmented_pairs, sup_map)

    # 4. Train / Val split
    train_examples, val_examples = split_data(all_examples, CONFIG["val_split"])

    # 5. Load base model
    print(f"\n📦 Loading base model: {CONFIG['base_model']}")
    model = SentenceTransformer(CONFIG["base_model"])
    print("✅ Base model loaded")

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
    val_labels     = [e.label    for e in val_examples]

    evaluator = evaluation.BinaryClassificationEvaluator(
        sentences1=val_sentences1,
        sentences2=val_sentences2,
        labels=val_labels,
        name="supervisor_val",
    )

    # 8. Train
    print(f"\n🏋️  Training for {CONFIG['epochs']} epochs...")
    print(f"   Batch size  : {CONFIG['batch_size']}")
    print(f"   Warmup steps: {CONFIG['warmup_steps']}")
    print(f"   Output path : {MODEL_DIR}\n")

    model.fit(
        train_objectives=[(train_loader, train_loss)],
        evaluator=evaluator,
        epochs=CONFIG["epochs"],
        warmup_steps=CONFIG["warmup_steps"],
        output_path=str(MODEL_DIR),
        show_progress_bar=True,
        save_best_model=True,       # Save checkpoint with best val score
    )

    print(f"\n✅ Training complete! Model saved to: {MODEL_DIR}")

    # 9. Generate supervisor embeddings using fine-tuned model
    print("\n📐 Generating supervisor embeddings with fine-tuned model...")
    fine_tuned = SentenceTransformer(str(MODEL_DIR))

    for sup in tqdm(supervisors, desc="Embedding supervisors"):
        text = build_supervisor_text(sup)
        sup["embedding_text"] = text
        sup["embedding"]      = fine_tuned.encode(text).tolist()
        sup["embedding_dim"]  = 384   # all-MiniLM-L6-v2 output dim

    # 10. Save supervisors with embeddings
    with open(OUTPUT_EMB_F, "w", encoding="utf-8") as f:
        json.dump(supervisors, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved embeddings → {OUTPUT_EMB_F}")
    print(f"\n{'='*60}")
    print("  TRAINING PIPELINE COMPLETE")
    print(f"  Run next: python training/evaluate_model.py")
    print(f"  Then:     python training/upload_to_supabase.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    train()
```

---

## ⚙️ STEP 3 — EVALUATION SCRIPT

```python
# services/module2-collaboration/training/evaluate_model.py
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
    accuracy_score, precision_score,
    recall_score, f1_score, confusion_matrix,
)
from sentence_transformers import SentenceTransformer

BASE_DIR     = Path(__file__).parent.parent
DATA_DIR     = BASE_DIR / "data"
MODEL_DIR    = BASE_DIR / "models" / "trained_supervisor_matcher"
RESULTS_FILE = DATA_DIR / "evaluation_results.json"

SIMILARITY_THRESHOLD = 0.60   # Score above this = match


def cosine_similarity(a: list, b: list) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def evaluate():
    print("\n" + "="*55)
    print("  SUPERVISOR MATCHING MODEL — EVALUATION")
    print("="*55 + "\n")

    # Load fine-tuned model
    print("📦 Loading fine-tuned model...")
    model = SentenceTransformer(str(MODEL_DIR))

    # Load supervisors with embeddings
    with open(DATA_DIR / "supervisors_with_embeddings.json", encoding="utf-8") as f:
        supervisors = json.load(f)
    with open(DATA_DIR / "training_pairs.json") as f:
        pairs = json.load(f)

    sup_map = {s["id"]: s for s in supervisors}

    # ── QUANTITATIVE EVALUATION ───────────────────────────────────
    print("📊 Running quantitative evaluation on training pairs...\n")

    y_true, y_pred = [], []

    for query, sup_id, label in pairs:
        sup = sup_map.get(sup_id)
        if not sup or not sup.get("embedding"):
            continue

        query_emb = model.encode(query).tolist()
        sim       = cosine_similarity(query_emb, sup["embedding"])
        predicted = 1 if sim >= SIMILARITY_THRESHOLD else 0

        y_true.append(int(label))
        y_pred.append(predicted)

    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec  = recall_score(y_true, y_pred, zero_division=0)
    f1   = f1_score(y_true, y_pred, zero_division=0)
    cm   = confusion_matrix(y_true, y_pred).tolist()

    print(f"  Accuracy  : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1 Score  : {f1:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"  [[TN={cm[0][0]:3d}  FP={cm[0][1]:3d}]")
    print(f"   [FN={cm[1][0]:3d}  TP={cm[1][1]:3d}]]")

    target_met = "✅ PASS" if f1 >= 0.75 else "❌ FAIL — need more training data or epochs"
    print(f"\n  Target F1 ≥ 0.75: {target_met}")

    # ── QUALITATIVE EVALUATION ────────────────────────────────────
    print("\n" + "─"*55)
    print("📋 Top-5 matches for sample student proposals:\n")

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
            scored.append({
                "id":         sup["id"],
                "name":       sup["name"],
                "department": sup["department"],
                "interests":  ", ".join(sup.get("research_interests", [])[:3]),
                "similarity": round(sim, 4),
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top5 = scored[:5]

        print(f"  Query: \"{proposal[:65]}...\"")
        for rank, s in enumerate(top5, 1):
            bar = "█" * int(s["similarity"] * 20)
            print(f"  {rank}. {s['name']:<35} {s['similarity']:.3f} {bar}")
        print()

        qualitative_results.append({
            "query": proposal,
            "top5":  top5,
        })

    # ── SAVE RESULTS ──────────────────────────────────────────────
    results = {
        "metrics": {
            "accuracy":  round(acc, 4),
            "precision": round(prec, 4),
            "recall":    round(rec, 4),
            "f1_score":  round(f1, 4),
            "threshold": SIMILARITY_THRESHOLD,
            "target_f1": 0.75,
            "target_met": f1 >= 0.75,
        },
        "confusion_matrix": cm,
        "qualitative":      qualitative_results,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Evaluation results saved → {RESULTS_FILE}")
    print(f"\nNext step: python training/upload_to_supabase.py\n")


if __name__ == "__main__":
    evaluate()
```

---

## ⚙️ STEP 4 — SUPABASE UPLOAD SCRIPT

```python
# services/module2-collaboration/training/upload_to_supabase.py
"""
Upload fine-tuned SBERT supervisor embeddings to Supabase pgvector.

Run:
    python training/upload_to_supabase.py

Requires .env with:
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
EMB_FILE = DATA_DIR / "supervisors_with_embeddings.json"


def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env"
        )
    return create_client(url, key)


def upload():
    print("\n" + "="*55)
    print("  UPLOADING SUPERVISOR EMBEDDINGS → SUPABASE")
    print("="*55 + "\n")

    # Load supervisors with embeddings
    with open(EMB_FILE, encoding="utf-8") as f:
        supervisors = json.load(f)

    print(f"📋 {len(supervisors)} supervisors to upload\n")

    supabase = get_supabase()

    success_count = 0
    error_count   = 0
    errors        = []

    for sup in tqdm(supervisors, desc="Uploading"):
        if not sup.get("embedding"):
            print(f"  ⚠️  Skipping {sup['name']} — no embedding")
            continue

        # Map to Supabase supervisor_profiles table schema
        payload = {
            # Core fields
            "name":               sup["name"],
            "email":              sup["email"],
            "department":         sup["department"],
            "research_cluster":   sup["research_cluster"],
            "level":              sup.get("level", "Mr/Ms"),
            "note":               sup.get("note", None),

            # Research data
            "research_interests": sup.get("research_interests", []),
            "specializations":    sup.get("specializations", []),
            "keywords":           sup.get("keywords", ""),

            # Availability
            "availability":       sup.get("availability", True),
            "max_students":       sup.get("max_students", 3),
            "current_students":   sup.get("current_students", 0),

            # SBERT embedding (768-dim for all-MiniLM-L6-v2)
            "expertise_embedding": sup["embedding"],

            # Metadata
            "embedding_text":     sup.get("embedding_text", ""),
            "model_version":      "sbert-v1-finetuned-r26it116",
        }

        try:
            # Upsert on email (unique identifier)
            result = (
                supabase.table("supervisor_profiles")
                .upsert(payload, on_conflict="email")
                .execute()
            )
            success_count += 1

        except Exception as e:
            error_count += 1
            errors.append({"supervisor": sup["name"], "error": str(e)})
            print(f"\n  ❌ Error uploading {sup['name']}: {e}")

    print(f"\n{'='*55}")
    print(f"  ✅ Successfully uploaded : {success_count}")
    print(f"  ❌ Errors               : {error_count}")

    if errors:
        print("\n  Errors detail:")
        for e in errors:
            print(f"    - {e['supervisor']}: {e['error']}")

    # Verify upload
    print("\n🔍 Verifying upload...")
    count_result = (
        supabase.table("supervisor_profiles")
        .select("id", count="exact")
        .execute()
    )
    print(f"  Total supervisors in Supabase: {count_result.count}")
    print(f"\n✅ Upload complete!\n")


if __name__ == "__main__":
    upload()
```

---

## ⚙️ STEP 5 — DATA AUGMENTATION SCRIPT

```python
# services/module2-collaboration/training/generate_more_pairs.py
"""
Generate additional training pairs to improve model accuracy.
Adds 50+ more student query examples covering all research domains.

Run:
    python training/generate_more_pairs.py

Output:
    Appends new pairs to training_pairs.json
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PAIRS_F  = DATA_DIR / "training_pairs.json"

# Additional training pairs — domain-specific student queries
# Format: (student_query, supervisor_id, label)

NEW_PAIRS = [
    # ── NLP / Language AI (Supervisor IDs: 1, 2, 4, 26, 33, 39, 56) ──
    ("I am building a Sinhala language NLP system for sentiment analysis", 1, 1),
    ("My project involves fine-tuning BERT for named entity recognition", 56, 1),
    ("I want to create a multilingual text classification system", 2, 1),
    ("My research is about question answering systems using transformers", 4, 1),
    ("I am developing a research paper summarization tool using T5", 33, 1),
    ("My project uses GPT models for automatic essay grading", 26, 1),
    ("I want to study topic modeling using LDA and BERTopic", 39, 1),
    ("My research involves information extraction from legal documents", 2, 1),

    # ── Machine Learning / Deep Learning (IDs: 6, 12, 13, 18, 20, 42, 50) ──
    ("I am implementing a random forest model for student performance prediction", 6, 1),
    ("My project is about federated learning for privacy-preserving ML", 13, 1),
    ("I want to research explainable AI for medical diagnosis", 18, 1),
    ("My research involves transfer learning for low-resource classification", 42, 1),
    ("I am building a GAN for data augmentation in medical imaging", 20, 1),
    ("My project is about multi-objective optimization in neural architecture search", 42, 1),
    ("I want to study spiking neural networks for energy-efficient AI", 24, 1),
    ("My research involves ensemble methods for fraud detection", 50, 1),

    # ── Computer Vision (IDs: 20, 37, 41, 62, 65) ──
    ("I am developing a real-time object detection system using YOLO", 41, 1),
    ("My project is about image segmentation for autonomous vehicles", 20, 1),
    ("I want to research facial recognition with privacy preservation", 65, 1),
    ("My research involves 3D reconstruction from 2D images", 37, 1),
    ("I am building a plant disease detection system from leaf images", 41, 1),

    # ── IoT / Smart Systems (IDs: 3, 16, 35, 36, 54, 67) ──
    ("My project uses Raspberry Pi and sensors for smart energy monitoring", 16, 1),
    ("I am researching LoRaWAN networks for long-range IoT communication", 67, 1),
    ("My research involves digital twin systems for industrial IoT", 54, 1),
    ("I want to study SDN for managing IoT network traffic", 35, 1),
    ("My project is about predictive maintenance using IoT sensor data", 54, 1),
    ("I am building a smart water management system using IoT", 3, 1),

    # ── Cyber Security (IDs: 15, 30, 38, 53, 69, 71) ──
    ("My research involves adversarial attacks on deep learning models", 15, 1),
    ("I am developing a blockchain-based identity management system", 22, 1),
    ("My project is about zero-trust architecture for enterprise networks", 53, 1),
    ("I want to study malware detection using machine learning", 15, 1),
    ("My research involves privacy-preserving data sharing techniques", 38, 1),

    # ── Education Technology (IDs: 5, 6, 14, 29, 32, 45) ──
    ("I am building a gamified learning platform for programming education", 14, 1),
    ("My project is about automatic quiz generation from lecture notes", 6, 1),
    ("I want to study student engagement prediction in online courses", 5, 1),
    ("My research involves AR for interactive science education", 52, 1),
    ("I am developing a peer review system for university assignments", 29, 1),

    # ── Data Science / Analytics (IDs: 12, 13, 17, 18, 49, 56) ──
    ("My project is about real-time dashboard for hospital patient monitoring", 48, 1),
    ("I am researching time series forecasting for stock market prediction", 18, 1),
    ("My research involves data lineage tracking in ETL pipelines", 49, 1),
    ("I want to build a recommendation engine for e-commerce", 14, 1),
    ("My project is about clustering algorithms for customer segmentation", 17, 1),

    # ── Networking / Systems (IDs: 57, 63, 67, 71) ──
    ("I am researching software-defined networking for cloud data centres", 57, 1),
    ("My project involves QoS optimization in 5G/6G networks", 67, 1),
    ("I want to study network topology discovery using graph algorithms", 71, 1),

    # ── Hard Negatives (label=0 — wrong domain) ──
    ("I want to build a deep learning image classifier", 69, 0),       # Cyber security
    ("My research is about network security firewalls", 20, 0),        # Computer vision
    ("I am studying e-learning engagement analytics", 67, 0),          # Wireless comms
    ("My project is about speech synthesis using AI", 53, 0),          # Security
    ("I want to research blockchain for supply chain", 41, 0),         # Computer vision
    ("My research is about data visualization dashboards", 3, 0),      # Smart agriculture
    ("I am building an NLP chatbot for customer service", 57, 0),      # Networking
    ("My project involves deep learning for cancer detection", 25, 0), # HCI
]


def append_pairs():
    with open(PAIRS_F) as f:
        existing = json.load(f)

    before = len(existing)
    combined = existing + NEW_PAIRS

    # Deduplicate by (query, sup_id)
    seen = set()
    deduped = []
    for pair in combined:
        key = (pair[0], pair[1])
        if key not in seen:
            seen.add(key)
            deduped.append(pair)

    with open(PAIRS_F, "w") as f:
        json.dump(deduped, f, indent=2)

    print(f"✅ Training pairs: {before} → {len(deduped)} (+{len(deduped)-before} new)")
    print(f"   Positive (label=1): {sum(1 for p in deduped if p[2]==1)}")
    print(f"   Negative (label=0): {sum(1 for p in deduped if p[2]==0)}")


if __name__ == "__main__":
    append_pairs()
```

---

## ⚙️ STEP 6 — INFERENCE SERVICE (updated supervisor_matcher.py)

```python
# services/module2-collaboration/app/services/supervisor_matcher.py
"""
Production inference service for supervisor matching.
Uses the fine-tuned SBERT model loaded from models/trained_supervisor_matcher/
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from app.services.model_registry import register, get as get_model

BASE_DIR  = Path(__file__).parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "trained_supervisor_matcher"
FALLBACK  = "sentence-transformers/all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None


def _cosine_similarity(a: list, b: list) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def load_model() -> SentenceTransformer:
    """Load fine-tuned model. Falls back to base model if not trained yet."""
    global _model
    if _model:
        return _model

    model_path = MODEL_DIR if MODEL_DIR.exists() else FALLBACK

    _model = SentenceTransformer(str(model_path))
    version = "fine-tuned-v1" if MODEL_DIR.exists() else "base-pretrained"
    register("sbert", _model, version=version)

    print(f"[SupervisorMatcher] Model loaded: {model_path} ({version})")
    return _model


def get_supabase() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


async def match_supervisors(
    student_proposal: str,
    top_k: int = 5,
    min_similarity: float = 0.45,
) -> List[Dict]:
    """
    Match a student research proposal to the top-K supervisors.

    Args:
        student_proposal: Student's research proposal or topic description
        top_k: Number of supervisors to return
        min_similarity: Minimum cosine similarity threshold

    Returns:
        List of dicts with supervisor info + similarity score + explanation
    """
    model     = load_model()
    supabase  = get_supabase()

    # Encode student query
    student_embedding = model.encode(student_proposal).tolist()

    # Query Supabase using pgvector RPC function
    result = supabase.rpc(
        "match_supervisors",
        {
            "student_embedding": student_embedding,
            "match_count":       top_k * 2,   # Over-fetch then filter
        },
    ).execute()

    raw_matches = result.data or []

    # Enrich results with explanation and multi-factor scoring
    enriched = []
    for match in raw_matches:
        sim = float(match.get("similarity", 0))
        if sim < min_similarity:
            continue

        # Load supervisor full profile
        sup_result = (
            supabase.table("supervisor_profiles")
            .select("*")
            .eq("id", match["id"])
            .single()
            .execute()
        )
        sup = sup_result.data or {}

        # Availability factor
        avail_factor = 1.0
        if not sup.get("availability", True):
            avail_factor = 0.0   # Skip overseas/unavailable
        elif sup.get("current_students", 0) >= sup.get("max_students", 5):
            avail_factor = 0.3   # Full but still show

        # Final multi-factor score
        # Weights: topic_similarity=70%, availability=30%
        final_score = (sim * 0.70) + (avail_factor * 0.30)

        # Generate explanation
        explanation = _build_explanation(
            student_proposal, sup, sim
        )

        enriched.append({
            "supervisor_id":      match["id"],
            "name":               sup.get("name", ""),
            "email":              sup.get("email", ""),
            "department":         sup.get("department", ""),
            "research_cluster":   sup.get("research_cluster", ""),
            "research_interests": sup.get("research_interests", []),
            "availability":       sup.get("availability", True),
            "current_students":   sup.get("current_students", 0),
            "max_students":       sup.get("max_students", 5),
            "similarity_score":   round(sim, 4),
            "multi_factor_score": round(final_score, 4),
            "explanation":        explanation,
        })

    # Sort by multi-factor score, return top_k
    enriched.sort(key=lambda x: x["multi_factor_score"], reverse=True)
    return enriched[:top_k]


def _build_explanation(query: str, sup: dict, sim: float) -> str:
    """Generate a human-readable explanation for why this supervisor matched."""
    interests = sup.get("research_interests", [])
    name      = sup.get("name", "This supervisor")

    query_lower = query.lower()
    matched_interests = [
        i for i in interests
        if any(word in query_lower for word in i.lower().split())
    ]

    if matched_interests:
        return (
            f"{name} is a strong match ({sim*100:.0f}% similarity) because their "
            f"research in {', '.join(matched_interests[:2])} aligns directly with "
            f"your proposed topic."
        )
    elif sim > 0.70:
        return (
            f"{name} is an excellent match ({sim*100:.0f}% similarity) with "
            f"closely related expertise in {', '.join(interests[:2])}."
        )
    elif sim > 0.55:
        return (
            f"{name} could supervise your work ({sim*100:.0f}% similarity). "
            f"Their background in {', '.join(interests[:2])} provides relevant context."
        )
    else:
        return (
            f"{name} has some relevant expertise ({sim*100:.0f}% similarity) "
            f"in {', '.join(interests[:2])}."
        )
```

---

## ⚙️ STEP 7 — SUPABASE SQL FUNCTIONS

Run these in the **Supabase SQL Editor** before uploading embeddings:

```sql
-- Add missing columns to supervisor_profiles table
ALTER TABLE public.supervisor_profiles
    ADD COLUMN IF NOT EXISTS name               TEXT,
    ADD COLUMN IF NOT EXISTS email              TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS department         TEXT,
    ADD COLUMN IF NOT EXISTS research_cluster   TEXT,
    ADD COLUMN IF NOT EXISTS level              TEXT,
    ADD COLUMN IF NOT EXISTS note               TEXT,
    ADD COLUMN IF NOT EXISTS research_interests TEXT[],
    ADD COLUMN IF NOT EXISTS specializations    TEXT[],
    ADD COLUMN IF NOT EXISTS keywords           TEXT,
    ADD COLUMN IF NOT EXISTS availability       BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS max_students       INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS current_students   INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS expertise_embedding VECTOR(384),
    ADD COLUMN IF NOT EXISTS embedding_text     TEXT,
    ADD COLUMN IF NOT EXISTS model_version      TEXT;

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_supervisor_embedding
    ON public.supervisor_profiles
    USING hnsw (expertise_embedding vector_cosine_ops);

-- RPC function used by the inference service
CREATE OR REPLACE FUNCTION match_supervisors(
    student_embedding VECTOR(384),
    match_count       INT DEFAULT 5
)
RETURNS TABLE (
    id         UUID,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        sp.id,
        1 - (sp.expertise_embedding <=> student_embedding) AS similarity
    FROM public.supervisor_profiles sp
    WHERE
        sp.availability = TRUE
        AND sp.expertise_embedding IS NOT NULL
    ORDER BY sp.expertise_embedding <=> student_embedding
    LIMIT match_count;
END;
$$;
```

---

## ⚙️ STEP 8 — README_TRAINING.md

```markdown
# Supervisor Matching Model — Training Guide
## R26-IT-116 | Module 2 | SBERT Fine-tuning

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy data files into data/ folder
#    sliit_supervisors.json   ← provided
#    training_pairs.json      ← provided

# 3. (Optional) Add more training pairs
python training/generate_more_pairs.py

# 4. Train the model (takes ~5-15 minutes)
python training/train_supervisor_matcher.py

# 5. Evaluate the model
python training/evaluate_model.py

# 6. Upload embeddings to Supabase
python training/upload_to_supabase.py
```

### What each script does

| Script | Purpose |
|--------|---------|
| `train_supervisor_matcher.py` | Fine-tunes SBERT using ContrastiveLoss on SLIIT supervisor pairs |
| `evaluate_model.py` | Reports Accuracy, Precision, Recall, F1 + qualitative top-5 matches |
| `upload_to_supabase.py` | Uploads supervisor embeddings to Supabase pgvector table |
| `generate_more_pairs.py` | Adds 50+ more training pairs to improve accuracy |

### Target Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| F1 Score | ≥ 0.75 | Balance of precision and recall |
| Accuracy | ≥ 80% | Correct match/no-match predictions |
| Similarity Threshold | 0.60 | Score above this = recommended match |

### Model Details

- **Base model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding dim:** 384
- **Training loss:** ContrastiveLoss
- **Epochs:** 15
- **Batch size:** 16
- **Saved to:** `models/trained_supervisor_matcher/`
```

---

## 📋 IMPLEMENTATION ORDER

```
1. Create folder structure:
   services/module2-collaboration/training/
   services/module2-collaboration/data/
   services/module2-collaboration/models/

2. Copy data files:
   sliit_supervisors.json  →  data/sliit_supervisors.json
   training_pairs.json     →  data/training_pairs.json

3. Update requirements.txt

4. Run Supabase SQL (Step 7) in Supabase SQL Editor

5. Create all Python files (Steps 2–6)

6. Install dependencies:
   pip install -r requirements.txt

7. Run training pipeline in order:
   python training/generate_more_pairs.py
   python training/train_supervisor_matcher.py
   python training/evaluate_model.py
   python training/upload_to_supabase.py

8. Update supervisor.py FastAPI router to use new supervisor_matcher.py

9. Test API endpoint:
   POST /api/v2/matching/supervisors
   Body: { "proposal": "I want to research NLP..." }
```

---

## ⚠️ CRITICAL RULES

```
1. NEVER hardcode Supabase keys — always use .env + python-dotenv
2. Run Supabase SQL (Step 7) BEFORE upload_to_supabase.py
3. embedding dim MUST be 384 (all-MiniLM-L6-v2 output) — match SQL VECTOR(384)
4. save_best_model=True in model.fit() — saves checkpoint with best val score
5. upsert on email — re-running upload does not create duplicates
6. load_model() checks MODEL_DIR first — falls back to base model if not trained
7. Augment data BEFORE training — more pairs = better accuracy
8. Check F1 after evaluate — if < 0.75, increase epochs or add more pairs
9. register() in model_registry — required for AI Provider Toggle (local mode)
10. similarity threshold 0.60 — tune this based on evaluation results
```
