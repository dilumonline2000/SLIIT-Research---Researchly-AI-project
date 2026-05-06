# Module 3 — Data Collection & Management

Locally-trained ML services for topic categorization, paper summarization,
and plagiarism trend analysis. All models trained on SLIIT RDA papers
(4,219 abstracts) and run **fully offline** — no API keys required.

---

## Folder layout

```
services/module3-data/
├── README.md                          ← you are here
│
├── app/                               ← FastAPI runtime
│   ├── main.py                        Entry point + router registration
│   ├── routers/                       HTTP endpoints
│   │   ├── pipeline.py                /data/scrape, /data/scrape/{id}
│   │   ├── categorization.py          /data/categorize, /data/categorize/status
│   │   ├── summarizer.py              /data/summarize, /data/summarize/upload, /data/summarize/status
│   │   ├── plagiarism_trends.py       /data/plagiarism-trends + /search + /compare
│   │   └── quality.py                 /data/quality
│   ├── services/                      ML inference (lazy-loaded, cached)
│   │   ├── topic_classifier.py        TF-IDF + OvR LogReg
│   │   ├── extractive_summarizer.py   SBERT centroid + lead-bias + MMR
│   │   ├── plagiarism_analyzer.py     SBERT trend search + pair compare
│   │   └── pdf_extractor.py           pypdf-backed text extraction for uploads
│   ├── models/                        Pydantic schemas + legacy wrappers
│   └── scrapers/                      ArXiv / SemanticScholar adapters
│
├── data/                              ← TRAINING DATA (input to training/)
│   ├── README.md
│   └── processed/
│       ├── topic_training.json        1,382 SLIIT papers, multi-label
│       ├── topic_labels.json          80-label vocabulary + frequencies
│       └── plagiarism_trend_corpus.json (topic, year) similarity stats
│
├── training/                          ← REPRODUCIBLE TRAINING SCRIPTS
│   ├── README.md
│   ├── prepare_topic_data.py          Extract subjects → multi-label
│   ├── prepare_plagiarism_corpus.py   Compute pairwise sims per topic+year
│   ├── train_topic_classifier.py      Fit TF-IDF + LogReg (≈4 s)
│   └── train_plagiarism_analyzer.py   Encode topic embeddings (≈1 s)
│
├── models/                            ← TRAINED ARTIFACTS (loaded at runtime)
│   ├── README.md
│   ├── trained_topic_classifier/
│   │   ├── classifier.pkl             ≈19 MB pickled TF-IDF + OvR LogReg
│   │   └── metadata.json              Metrics: micro-F1, top-1, top-3 hit rate
│   └── trained_plagiarism_analyzer/
│       ├── trend_index.pkl            SBERT topic embeddings + per-year stats
│       └── metadata.json
│
├── requirements.txt
├── Dockerfile
└── railway.toml
```

> **Mental model:** `data/` is the input, `training/` is the recipe, `models/`
> is the output. `app/services/` consumes `models/` at runtime — never the
> other way around.

---

## Models at a glance

| Capability | Architecture | Training data | Metric | Runtime |
|---|---|---|---|---|
| Topic categorization | TF-IDF (30k features) + One-vs-Rest LogReg | 1,382 SLIIT papers, 80 labels | Top-3 hit-rate ≈ **69%** | ~50 ms / query |
| Extractive summarization | SBERT centroid + lead-bias + MMR | (algorithmic — no training needed) | 35% compression typical | ~80 ms / paper |
| Plagiarism trend search | SBERT retrieval over topic embeddings | 17 topics from 3,782 SLIIT papers | Cosine retrieval | ~30 ms / query |
| Pair comparison | SBERT cosine + 4-gram Jaccard | (deterministic) | Risk score weighted blend | ~150 ms / pair |

The plagiarism analyzer reuses the SLIIT-fine-tuned SBERT from
`services/module1-integrity/models/sbert_plagiarism/`, so the SLIIT-specific
similarity signal carries through.

---

## End-to-end flows

### 1. Topic-aware plagiarism trends (the headline feature)

User enters a topic — e.g. *"machine learning"*:

1. **Frontend** → `POST /api/v1/data/plagiarism-trends/search`
2. **Gateway** → module 3 `/data/plagiarism-trends/search`
3. **Service** `plagiarism_analyzer.search_trends`:
   1. Encode the query topic with SLIIT-tuned SBERT.
   2. Cosine-rank against the 17-topic embedding index.
   3. For each top-K topic, return the precomputed yearly stats:
      `n_papers, avg_similarity, max_similarity, p95_similarity,
       n_high_similarity_pairs, trend_direction, top_pairs`
   4. `top_pairs` includes specific SLIIT papers that scored highest in
      similarity — clickable links to the SLIIT RDA archive.
4. **Frontend** renders a year-by-year table per topic with trend arrows
   and links to the paper pairs.

### 2. Compare two uploaded papers

User pastes two paper texts:

1. **Frontend** → `POST /api/v1/data/plagiarism-trends/compare`
2. **Service** `plagiarism_analyzer.compare_papers`:
   - Document-level cosine similarity (SBERT)
   - 4-gram Jaccard / overlap-in-A / overlap-in-B
   - Sentence-level: top-K most similar sentence pairs
   - Aggregate `risk_score = 0.75 × doc_sim + 0.25 × ngram_jaccard`
   - Bucket → `minimal | low | medium | high`
3. **Frontend** shows the risk badge, four numerical metrics, and the
   flagged sentence pairs side-by-side.

### 3. Categorization

`POST /api/v1/data/categorize` with `{text, threshold, top_k}`:
- TF-IDF transform → OvR LogReg → softmax-like probabilities per label
- Returns `top_categories` (sorted) and `categories` (above threshold)
- 80-label vocabulary built from SLIIT papers' `subject` field.

### 4. Summarization

Two entry points share the same backend pipeline:

**`POST /api/v1/data/summarize`** with `{text, length}` — paste raw text.

**`POST /api/v1/data/summarize/upload`** (multipart/form-data) with
`file` (PDF) + `length` — uploads a research paper PDF, extracts text via
`pypdf`, then runs the same summarization pipeline.

Pipeline:
- SBERT-encode every sentence
- Score by `0.55·centroid_sim + 0.20·position + 0.10·length + MMR redundancy`
- Greedy-pick `{short:3, medium:6, detailed:10}` sentences
- Return verbatim selected sentences (no hallucination)

The PDF upload path adds `filename` and `pdf_text_length` to the response so
the frontend can show what was actually extracted. Uploaded files live only in
memory long enough to extract text — they're never written to disk.

---

## How to retrain

From the project root:

```bash
# 1. Build training data
python services/module3-data/training/prepare_topic_data.py
python services/module3-data/training/prepare_plagiarism_corpus.py

# 2. Train models
python services/module3-data/training/train_topic_classifier.py
python services/module3-data/training/train_plagiarism_analyzer.py
```

Total wall-clock on CPU: ~3 min (dominated by the plagiarism corpus encode).

---

## Running the service

```bash
cd services/module3-data
pip install -r requirements.txt
uvicorn app.main:app --port 8003 --reload
```

Health endpoints:
- `GET /health`
- `GET /data/categorize/status`
- `GET /data/summarize/status`
- `GET /data/plagiarism-trends/status`

---

## Viva talking points

- **Why TF-IDF + LogReg, not SciBERT?** TF-IDF + LogReg trains in 4 s, ships
  in <20 MB, infers in 50 ms. SciBERT would need GPU + hours of training and
  match similar accuracy on this corpus size. Pragmatic engineering choice.

- **Why extractive over abstractive summarization?** Every output sentence is
  verbatim from the source paper — there's zero hallucination risk, which
  makes the system suitable for academic use. BART-style abstractive models
  add value but with hallucination cost.

- **Why is `risk_score` weighted 0.75 SBERT / 0.25 n-gram?** Academic
  plagiarism is usually paraphrased, not copy-pasted. SBERT catches semantic
  similarity (paraphrasing); n-gram overlap is a copy-paste tripwire. Both
  matter, but SBERT carries more weight.

- **What's a "trend direction"?** For each (topic, year), we compare the
  average pairwise similarity to the previous year. ±0.02 threshold:
  `increasing` (≥+0.02), `decreasing` (≤-0.02), `stable` otherwise.

- **Why only 17 topics in the trend index?** We require ≥3 papers per
  (topic, year) bucket to compute meaningful pairwise statistics. The full
  103 topics with ≥3 papers shrink to 17 once we apply that constraint
  per-year. More topics will appear as new SLIIT papers are scraped.
