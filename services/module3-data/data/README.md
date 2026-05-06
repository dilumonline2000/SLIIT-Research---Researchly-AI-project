# Module 3 — Training Data

This folder is the **input** to scripts in `../training/`. Nothing here is
loaded at runtime; the live service reads from `../models/` instead.

## Structure

```
data/
├── README.md                              ← you are here
└── processed/                             Output of training/prepare_*.py
    ├── topic_training.json                1,382 SLIIT papers w/ multi-labels (~2.4 MB)
    ├── topic_labels.json                  80-label vocabulary + frequencies
    └── plagiarism_trend_corpus.json       (topic, year) similarity stats (~74 KB)
```

## Provenance

The raw source is `ml/data/raw/sliit_papers/papers_raw_sliit.json`
(4,219 papers from the SLIIT Research Data Archive).

- **`topic_training.json`** — every paper that has at least one label from
  the kept vocabulary. Built by `prepare_topic_data.py`:
  1. Extract the `subject` field, split on `,;·|`
  2. Lowercase, strip punctuation
  3. Drop labels that appear in < 5 papers
  4. Keep top 80 most-frequent labels
  5. Retain papers that have ≥ 1 surviving label

- **`topic_labels.json`** — the resulting label vocabulary along with the
  total paper count per label. The most common labels: `sri lanka` (240),
  `machine learning` (189), `deep learning` (74), `image processing` (70),
  `artificial intelligence` (58), `covid-19` (54), `nlp` (47).

- **`plagiarism_trend_corpus.json`** — for every (topic, year) bucket with
  ≥3 papers, compute pairwise SBERT cosine similarity over a sample of up
  to 60 papers. Aggregate to `avg / max / p95 / n_high_pairs`. Built by
  `prepare_plagiarism_corpus.py`. Heavy step (~90 s on CPU).

## Regenerating

```bash
python ../training/prepare_topic_data.py
python ../training/prepare_plagiarism_corpus.py
```

Both scripts are deterministic — same input → same output.

## Sample queries (for viva demos)

**Categorization** — paste one of these and inspect the top categories:
- A deep-learning + medical-imaging abstract
- A blockchain + supply-chain abstract
- An IoT + cybersecurity abstract

**Plagiarism trend search**:
- *"machine learning"* — should hit the largest topic bucket
- *"covid-19"* — recent topic with high-similarity papers expected
- *"image processing"* — overlapping with machine learning

**Pair comparison**:
- Paste two abstracts about the *same SLIIT topic* — expect HIGH risk
- Paste two abstracts about *unrelated topics* — expect MINIMAL risk
- Paste a paper + a paraphrased version of itself — expect MEDIUM/HIGH
