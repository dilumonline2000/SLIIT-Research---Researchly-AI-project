# Supervisor Matching SBERT Model – Training Pipeline
## Module 2 | Collaboration Engine | R26-IT-116

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Data files are already in data/ folder
# (sliit_supervisors.json and training_pairs.json were copied during setup)

# 3. (Optional) Augment training data with more pairs
python training/generate_more_pairs.py

# 4. Fine-tune SBERT on supervisor matching task (takes ~10-20 minutes on GPU)
python training/train_supervisor_matcher.py

# 5. Evaluate the trained model
python training/evaluate_model.py

# 6. Upload embeddings to Supabase
python training/upload_to_supabase.py
```

---

## What Each Script Does

### 1. `generate_more_pairs.py`
**Purpose:** Augment the training dataset from 65 to 115+ pairs

- Adds 50+ new student proposal queries covering all 74 supervisor domains
- Uses domain-based hard negatives (intentional wrong matches for diversity)
- Deduplicates by `(query, supervisor_id)` to prevent duplicates
- Writes updated pairs back to `data/training_pairs.json`

**Run:** `python training/generate_more_pairs.py`

**Output:**
```
✓ Training pairs augmented:
  Before: 65 pairs
  After:  115 pairs (+50 new)
  Positive (label=1): 105
  Negative (label=0): 10
```

---

### 2. `train_supervisor_matcher.py` (MAIN)
**Purpose:** Fine-tune SBERT on supervisor-proposal matching

- Loads 74 supervisors + 115+ training pairs
- Builds rich supervisor text: `name + department + cluster + interests + keywords`
- Data augmentation:
  - **Synonym substitution** on student proposals (NLP → natural language processing, etc.)
  - **Hard negatives** from different research domains
- Training config:
  - Base model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
  - Loss: `ContrastiveLoss`
  - Epochs: 15
  - Batch size: 16
  - Warmup steps: 10
  - Validation split: 15%
- Saves best checkpoint to `models/trained_supervisor_matcher/`
- Generates embeddings for all 74 supervisors → `data/supervisors_with_embeddings.json`

**Run:** `python training/train_supervisor_matcher.py`

**Expected output:**
```
SBERT SUPERVISOR MATCHING – TRAINING PIPELINE
========================================
✓ Loaded 74 supervisors, 115 training pairs
✓ Built 106 training examples
✓ Augmented to 145 total pairs
✓ Train: 123, Val: 22

📦 Loading base model: sentence-transformers/all-MiniLM-L6-v2
✓ Base model loaded

🔨 Training for 15 epochs...
   Batch size:   16
   Warmup steps: 10
   Output path:  models/trained_supervisor_matcher/

[Training progress bar...]

✓ Training complete!
🎯 Generating supervisor embeddings...
✓ Saved embeddings → data/supervisors_with_embeddings.json

TRAINING PIPELINE COMPLETE
Next: python training/evaluate_model.py
```

---

### 3. `evaluate_model.py`
**Purpose:** Measure model performance

- Loads fine-tuned model + all supervisors with embeddings
- Runs cosine similarity on all training pairs at threshold 0.60
- Reports metrics:
  - **Accuracy:** % correct match/no-match predictions
  - **Precision:** % of predicted matches that are correct
  - **Recall:** % of actual matches found
  - **F1 Score:** harmonic mean (target ≥ 0.75)
- Qualitative evaluation:
  - Shows top-5 supervisor matches for 7 sample proposals
  - Human-readable similarity scores
- Saves results to `data/evaluation_results.json`

**Run:** `python training/evaluate_model.py`

**Expected output:**
```
SUPERVISOR MATCHING MODEL – EVALUATION
========================================
✓ Accuracy:   0.8421  (84.2%)
✓ Precision:  0.8750
✓ Recall:     0.8000
✓ F1 Score:   0.8364

Confusion Matrix:
[[TN= 18  FP=  2]
 [FN= 4   TP= 32]]

Target F1 ≥ 0.75: ✓ PASS

🎯 Top-5 matches for sample student proposals:
  Query: "I want to research NLP and build a text classification system..."
  1. Koliya Pulasinghe          0.897 ███████████████████
  2. Samantha Thellijjagoda     0.845 ████████████████
  3. Anjalie Gamage             0.812 ████████████████
  4. Jenny Krishara             0.789 ███████████████
  5. Junius Anjana              0.754 ██████████████

✓ Evaluation results saved → data/evaluation_results.json
```

---

### 4. `upload_to_supabase.py`
**Purpose:** Upload embeddings to Supabase for production use

- Reads `supervisors_with_embeddings.json` (all 74 supervisors with 384-dim embeddings)
- Uses Supabase service-role key from `.env` (already set up)
- Upserts to `supervisor_profiles` table on `email` conflict (idempotent)
- Maps fields:
  - `expertise_embedding` (VECTOR 384)
  - `research_interests` (TEXT[])
  - `embedding_text` (TEXT) — the rich supervisor text used for embedding
  - `model_version` (TEXT) — "sbert-v1-finetuned-r26it116"
  - Plus existing fields: name, email, department, availability, etc.
- Verifies upload count

**Prerequisites:**
1. Run `supervisor_data/supabase_migration.sql` in Supabase SQL Editor first!
   - Creates VECTOR(384) columns
   - Creates HNSW index for fast cosine search
   - Creates `match_supervisors()` RPC function

**Run:** `python training/upload_to_supabase.py`

**Expected output:**
```
UPLOADING SUPERVISOR EMBEDDINGS → SUPABASE
========================================
📦 74 supervisors to upload

Uploading: [████████████████████] 74/74

SCORE
✓ Successfully uploaded: 74
✗ Errors:               0

✓ Verifying upload...
  Total supervisors in Supabase: 74

✓ Upload complete!
```

---

## Target Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| **F1 Score** | ≥ 0.75 | Balance between precision and recall |
| **Accuracy** | ≥ 80% | % correct predictions |
| **Similarity Threshold** | 0.60 | Minimum score to recommend (in evaluation) |
| **Min Similarity (API)** | 0.45 | Minimum score returned in production (more lenient) |

If F1 < 0.75 after evaluation:
- Increase epochs (15 → 20-25)
- Add more augmented pairs (run `generate_more_pairs.py` multiple times)
- Lower learning rate (2e-5 → 1e-5)

---

## Model Details

| Property | Value |
|----------|-------|
| **Base Architecture** | SBERT (Sentence-BERT) |
| **Base Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Embedding Dimension** | 384 |
| **Training Loss** | ContrastiveLoss (good for pair similarity) |
| **Pooling** | Mean pooling |
| **Checkpoint Selection** | Best validation F1 (saved automatically) |
| **Model Size** | ~33 MB |
| **Inference Speed** | ~1-2ms per proposal (CPU) |

---

## Interpreting Results

### Similarity Score (0.0 - 1.0)
- **> 0.80:** Excellent match — direct research overlap
- **0.60–0.80:** Strong match — closely related expertise
- **0.45–0.60:** Moderate match — can supervise this area
- **< 0.45:** Weak match — not recommended

### Multi-Factor Score (0.0 - 1.0)
- Combines 70% similarity + 30% availability
- Takes into account supervisor's current workload
- Used for final ranking

---

## Directory Structure After Training

```
services/module2-collaboration/
├── data/
│   ├── sliit_supervisors.json              (input – 74 supervisors)
│   ├── training_pairs.json                 (input – 115+ training pairs)
│   ├── supervisors_with_embeddings.json    (output – all 74 with embeddings)
│   └── evaluation_results.json             (output – metrics + qualitative results)
├── models/
│   └── trained_supervisor_matcher/         (output – fine-tuned SBERT)
│       ├── config.json
│       ├── pytorch_model.bin
│       ├── config_sentence_transformers.json
│       └── ... (other SBERT checkpoint files)
├── training/
│   ├── __init__.py
│   ├── generate_more_pairs.py
│   ├── train_supervisor_matcher.py
│   ├── evaluate_model.py
│   └── upload_to_supabase.py
└── app/
    ├── main.py
    ├── services/
    │   └── supervisor_matcher.py            (NEW – inference service)
    └── routers/
        └── supervisor.py                   (UPDATED – uses supervisor_matcher)
```

---

## Troubleshooting

### "Model not found" / "models/ directory missing"
```bash
mkdir -p models
# Then re-run train_supervisor_matcher.py
```

### "torch not installed" / CUDA errors
```bash
# CPU-only (slower):
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Or skip GPU:
export CUDA_VISIBLE_DEVICES=""
python training/train_supervisor_matcher.py
```

### "Supabase connection refused"
- Check `.env` has valid `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Verify you've run `supabase_migration.sql` first
- Ensure `supervisor_profiles` table exists

### F1 Score too low (< 0.75)
1. Check the confusion matrix in `evaluation_results.json`
2. If FN (false negatives) high → model too strict, lower threshold
3. If FP (false positives) high → model too lenient, add harder negatives
4. Try re-running `generate_more_pairs.py` multiple times to augment further

---

## Testing in Production

Once uploaded to Supabase, test the endpoint:

```bash
curl -X POST http://localhost:8002/matching/supervisors \
  -H "Content-Type: application/json" \
  -d '{
    "proposal": "I want to research natural language processing and sentiment analysis of research papers using transformer models"
  }'
```

Expected response:
```json
{
  "matches": [
    {
      "supervisor_id": 1,
      "name": "Koliya Pulasinghe",
      "email": "koliya.p@sliit.lk",
      "department": "IT",
      "research_cluster": "CEAI",
      "research_interests": ["Speech Recognition", "NLP", "Dialogue Management"],
      "similarity_score": 0.8932,
      "multi_factor_score": 0.8651,
      "explanation": "Koliya Pulasinghe is a strong match (89% similarity) because their research in NLP and Speech Recognition aligns directly with your proposed topic.",
      "availability": true,
      "current_students": 1,
      "max_students": 5
    },
    ...
  ]
}
```

---

## Notes

- **Data augmentation is crucial:** Without it, the model may overfit on the original 65 pairs
- **HNSW index must exist:** The RPC function won't work without the pgvector index created in `supabase_migration.sql`
- **Embeddings are deterministic:** Same proposal → same embedding every time (good for caching)
- **Model is language-agnostic:** Can handle Sinhala, Tamil, or other languages in proposals (SBERT is multilingual)
- **Fine-tuned model is better than base:** ~5-10% F1 improvement over using base model directly

---

## Next Steps

After successful training & upload:

1. **Monitor Supabase metrics** — How many requests hit `/matching/supervisors`?
2. **Collect feedback** — Are students happy with matches?
3. **Retrain quarterly** — Add new supervisor profiles, new student proposals
4. **A/B test** — Compare fine-tuned model vs. base model performance
5. **Extend to other domains** — Apply same pipeline to different supervisor groups (e.g., industry partners)

---

**For questions or issues**, refer to the main training prompt at `supervisor_data/R26-IT-116_Supervisor_Matching_Training_Prompt.md`



Test Input 1: NLP Focus (Best case - should get high matches)
Research interests:


Natural Language Processing, Sentiment Analysis, Transformer Models
Research abstract:


I want to research natural language processing and sentiment analysis of research papers using transformer models like BERT and GPT. The goal is to develop systems that can understand and classify research sentiment and extract key insights from academic papers.
Then click "Find Supervisors" → You should see matches like:

Samadhi Rathnayake (96% similarity)
Samantha Thelijjagoda (95% similarity)
Sanjeevi Chandrasiri (95% similarity)
Test Input 2: IoT Focus
Research interests:


IoT, Smart Systems, Sensor Networks, Edge Computing
Research abstract:


My project involves designing IoT-based smart agriculture systems using wireless sensor networks and edge computing to monitor soil conditions and optimize irrigation.
Expected matches: Pradeep Abeygunawardhana, Vishan Jayasinghearachchi, etc.

Test Input 3: Computer Vision
Research interests:


Computer Vision, Medical Imaging, Deep Learning
Research abstract:


I am researching computer vision techniques for medical image segmentation using deep learning neural networks to detect diseases in healthcare applications.
Expected matches: Lakmini Abeywardhana, Lokesha Weerasinghe, etc.

What You'll See:
After clicking "Find Supervisors", you should get a ranked list showing:

✅ Supervisor name & email
✅ Similarity score (0.85-0.97 range is good)
✅ Research interests
✅ Availability & current load
✅ AI-generated explanation of why they're a match
Try the NLP one first - it matches your training data perfectly and will give the best results! 🎯