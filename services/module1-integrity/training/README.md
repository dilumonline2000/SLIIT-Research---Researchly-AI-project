# Module 1 — Training Pipeline

Scripts here produce the artifacts in `../models/`. Each step is idempotent
and runnable independently. **Run from the project root**, not from this dir.

## Pipeline

```
ml/data/raw/sliit_papers/papers_raw_sliit.json      (4,219 SLIIT papers)
                            │
                            ├──► prepare_gap_corpus.py
                            │    └──► data/processed/gap_corpus.json    (553 gaps)
                            │              │
                            │              └──► train_gap_analyzer.py
                            │                   └──► models/trained_gap_analyzer/
                            │                        ├── gap_index.pkl
                            │                        └── metadata.json
                            │
                            └──► prepare_proposal_corpus.py
                                 └──► data/processed/proposal_corpus.json (3,858)
                                           │
                                           └──► train_proposal_retriever.py
                                                └──► models/trained_proposal_retriever/
                                                     ├── proposal_index.pkl
                                                     └── metadata.json
```

## How to run

```bash
# From project root
python services/module1-integrity/training/prepare_gap_corpus.py
python services/module1-integrity/training/prepare_proposal_corpus.py
python services/module1-integrity/training/train_gap_analyzer.py
python services/module1-integrity/training/train_proposal_retriever.py
```

CPU runtime: ~2 min total. No GPU required.

## What the scripts do

### `prepare_gap_corpus.py`
Sentence-splits every paper's abstract and applies 7 regex patterns:

| Pattern | Tag | Weight |
|---|---|---|
| `however ... not / lack / limited` | `limitation` | 0.95 |
| `future work / further research` | `future_work` | 1.02 |
| `remains unclear / open question` | `unexplored` | 1.06 |
| `few studies / limited research` | `scarcity` | 1.00 |
| `research gap` | `research_gap` | 1.10 |
| `more research is needed` | `more_needed` | 1.04 |
| `has not been investigated` | `not_investigated` | 1.08 |

Tags carry into the runtime `gap_score` so a `research_gap` outranks a
`limitation` of equal cosine similarity.

### `prepare_proposal_corpus.py`
Retains every paper whose abstract is ≥120 chars and extracts:
- `problem_statement` — first sentence matching `this study investigates...` or `the aim of this...`
- `objectives_text` — first sentence matching `objective / aim / in order to`
- `methodology_text` — first sentence matching `using / employ / conduct ... method`

### `train_gap_analyzer.py`
Loads SLIIT-fine-tuned SBERT (`models/sbert_plagiarism/`) and encodes every gap
sentence to a 384-dim vector. Pickles `{embeddings, records, version}`.

### `train_proposal_retriever.py`
Same encoder, applied to `title + subject + abstract[:500]` per exemplar.

## Adding a new gap pattern

Edit `GAP_PATTERNS` in `prepare_gap_corpus.py`, re-run the two-step pipeline,
and the live service picks up the new index on next request (lazy load — kill
the uvicorn worker or hit `/gaps/status` to force reload).
