# Module 3 — Training Pipeline

Scripts here produce the artifacts in `../models/`. Each step is idempotent
and runnable independently. **Run from the project root**, not from this dir.

## Pipeline

```
ml/data/raw/sliit_papers/papers_raw_sliit.json    (4,219 SLIIT papers)
                            │
                            ├──► prepare_topic_data.py
                            │    ├──► data/processed/topic_training.json
                            │    └──► data/processed/topic_labels.json
                            │              │
                            │              └──► train_topic_classifier.py
                            │                   └──► models/trained_topic_classifier/
                            │                        ├── classifier.pkl
                            │                        └── metadata.json
                            │
                            └──► prepare_plagiarism_corpus.py
                                 └──► data/processed/plagiarism_trend_corpus.json
                                           │
                                           └──► train_plagiarism_analyzer.py
                                                └──► models/trained_plagiarism_analyzer/
                                                     ├── trend_index.pkl
                                                     └── metadata.json
```

## How to run

```bash
# From project root
python services/module3-data/training/prepare_topic_data.py
python services/module3-data/training/prepare_plagiarism_corpus.py
python services/module3-data/training/train_topic_classifier.py
python services/module3-data/training/train_plagiarism_analyzer.py
```

CPU runtime: ~3 min total. No GPU required. The plagiarism corpus
(`prepare_plagiarism_corpus.py`) dominates wall-clock because it encodes
~3,800 abstracts with SBERT.

## What each script does

### `prepare_topic_data.py`
Builds the multi-label corpus. Filters labels that appear in < 5 papers and
keeps the top 80 most frequent. Output preserves `text = title + ". " + abstract`.

### `prepare_plagiarism_corpus.py`
For each (topic, year) bucket with ≥3 papers:
- Encode every abstract with SLIIT-fine-tuned SBERT
- Compute all pairwise cosine similarities (capped at 60 papers per bucket)
- Aggregate: avg, max, 95th-percentile
- Capture top-K most-similar pairs (with paper IDs + URLs)
- Compute year-over-year trend direction within the topic

### `train_topic_classifier.py`
- TF-IDF: 30k features, 1+2-grams, sublinear_tf
- One-vs-Rest LogReg (`liblinear` solver, C=4.0, 400 iters)
- 85/15 train/val split, stratified
- Reports: micro-F1, macro-F1, top-1 hit rate, top-3 hit rate
- Saves `classifier.pkl` (TF-IDF + LogReg + label vocab) ~19 MB

### `train_plagiarism_analyzer.py`
- Encodes each unique topic name with SBERT (one embedding per topic)
- Aggregates `n_papers_total / avg_overall / max_avg / latest_direction` per topic
- Saves `trend_index.pkl` ~70 KB

## Adding a new label
1. Drop `MIN_LABEL_FREQ` in `prepare_topic_data.py` (currently 5)
2. Re-run the topic pipeline
3. Restart uvicorn (or hit `/data/categorize/status` to force-reload)

## Adding a new SLIIT paper
1. Append it to `ml/data/raw/sliit_papers/papers_raw_sliit.json`
2. Re-run all 4 scripts
3. Restart the service

The whole pipeline is incremental-safe in concept but currently re-trains
from scratch — fast enough that we don't need delta updates yet.
