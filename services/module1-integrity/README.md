# Module 1 — Research Integrity & Compliance

Locally-trained ML services for citation parsing, plagiarism detection,
research-gap analysis, proposal generation and mind-map building.

All models are trained on SLIIT RDA papers (4,219 abstracts) and run **fully
offline** — no API keys required for the core integrity workflows.

---

## Folder layout (read this before adding files)

```
services/module1-integrity/
├── README.md                          ← you are here
│
├── app/                               ← FastAPI runtime
│   ├── main.py                        Entry point + router registration
│   ├── routers/                       HTTP endpoints
│   │   ├── citation.py                /citations/parse, /format
│   │   ├── gap_analysis.py            /gaps/analyze, /gaps/status
│   │   ├── proposal.py                /proposals/generate, /proposals/status
│   │   ├── plagiarism.py              /plagiarism/check
│   │   └── mindmap.py                 /mindmaps/generate
│   ├── services/                      ML inference (loaded lazily, cached)
│   │   ├── gap_analyzer.py            SBERT retrieval over gap corpus
│   │   └── proposal_retriever.py      SBERT retrieval over proposal corpus
│   └── models/                        Pydantic schemas + lightweight wrappers
│       ├── citation_ner.py            spaCy NER inference wrapper
│       └── proposal_generator.py      (legacy stub, replaced by services/)
│
├── data/                              ← TRAINING DATA (input to training/)
│   ├── README.md                      How each file is built
│   ├── raw/                           (linked from ml/data/raw/sliit_papers/)
│   ├── processed/                     Output of prepare_*.py scripts
│   │   ├── gap_corpus.json            553 gap sentences from 494 SLIIT papers
│   │   └── proposal_corpus.json       3,858 proposal exemplars
│   └── samples/                       Sample queries for viva demos
│
├── training/                          ← REPRODUCIBLE TRAINING SCRIPTS
│   ├── README.md                      How to retrain everything
│   ├── prepare_gap_corpus.py          Step 1: extract gap sentences
│   ├── prepare_proposal_corpus.py     Step 1: build proposal exemplars
│   ├── train_gap_analyzer.py          Step 2: SBERT-encode gap corpus
│   └── train_proposal_retriever.py    Step 2: SBERT-encode proposal corpus
│
├── models/                            ← TRAINED MODEL ARTIFACTS (loaded at runtime)
│   ├── README.md                      What each model does + metrics
│   ├── citation_ner/                  spaCy NER (F1=99.05%, pre-trained)
│   ├── sbert_plagiarism/              SBERT fine-tuned (Acc=100%, pre-trained)
│   ├── trained_gap_analyzer/          Output of train_gap_analyzer.py
│   │   ├── gap_index.pkl              ~1.1 MB embeddings + metadata
│   │   └── metadata.json              Stats: n_gaps, n_papers, model version
│   └── trained_proposal_retriever/    Output of train_proposal_retriever.py
│       ├── proposal_index.pkl         ~13 MB embeddings + metadata
│       └── metadata.json              Stats: n_exemplars, model version
│
├── requirements.txt                   pip dependencies
├── Dockerfile                         Production container
└── railway.toml                       Cloud deployment config
```

> **Mental model:** `data/` is the input, `training/` is the recipe, `models/`
> is the output. `app/` consumes `models/` at runtime — never the other way around.

---

## Models at a glance

| Model | Architecture | Training data | Metric | Status |
|---|---|---|---|---|
| Citation NER | spaCy transformer | 3,866 citations from 539 SLIIT papers | F1 = **99.05%** | ✅ trained |
| SBERT Plagiarism | Sentence-BERT (triplet loss) | 500 SLIIT abstract pairs | Acc = **100%** | ✅ trained |
| Gap Analyzer | SBERT retrieval index | 553 gap sentences from 494 SLIIT papers | Cosine retrieval | ✅ trained |
| Proposal Retriever | SBERT retrieval index | 3,858 SLIIT proposal exemplars | Cosine retrieval | ✅ trained |

Gap & Proposal models reuse the fine-tuned `sbert_plagiarism` encoder, so the
SLIIT-specific signal carries through.

---

## End-to-end flow: research-gap analysis (the headline feature)

User enters a topic in the UI — e.g. *"machine learning in healthcare"*.

1. **Frontend** calls `POST /api/v1/gaps/analyze` with `{topic, top_k, min_similarity}`.
2. **Gateway** proxies to module 1's `/gaps/analyze`.
3. **Router** calls `app.services.gap_analyzer.analyze(topic, ...)`:
   1. Encode the topic with the SLIIT-fine-tuned SBERT.
   2. Cosine-rank against the 553-vector gap index.
   3. Filter by `min_similarity`, weight by gap-type (`research_gap` &gt; `limitation`).
   4. Greedy-cluster near-duplicates (threshold 0.78).
   5. Return top-K with `gap_score`, `recency_score`, `novelty_score`, and the
      **source SLIIT paper** (title, authors, year, RDA URL).
4. **Frontend** renders each gap as a card with the supporting paper attached.

If the index is missing the router silently falls back to Gemini, then to a
deterministic stub — so the endpoint never breaks.

---

## How to retrain

From the project root:

```bash
# 1. Build training corpora (regex extraction over SLIIT papers)
python services/module1-integrity/training/prepare_gap_corpus.py
python services/module1-integrity/training/prepare_proposal_corpus.py

# 2. Encode with SBERT (re-uses models/sbert_plagiarism if present)
python services/module1-integrity/training/train_gap_analyzer.py
python services/module1-integrity/training/train_proposal_retriever.py
```

Total wall-clock on CPU: ~2 min for gaps, ~95 s for proposals.

---

## Running the service

```bash
cd services/module1-integrity
pip install -r requirements.txt
uvicorn app.main:app --port 8001 --reload
```

Health endpoints:
- `GET  /health`
- `GET  /gaps/status` — local-model load state
- `GET  /proposals/status` — local-model load state

---

## Viva talking points

- **Why retrieval, not generation?** Retrieval is *grounded* — every gap cites
  a real SLIIT paper, so claims are verifiable. Generation hallucinates.
- **Why SBERT instead of TF-IDF?** SBERT captures semantic similarity (e.g.
  "kidney disease prediction" matches "renal failure forecasting"); TF-IDF
  matches surface tokens.
- **Why fine-tune the encoder?** The plagiarism-trained SBERT learned *SLIIT
  paper similarity*, which transfers directly to gap retrieval.
- **What's `gap_score`?** Cosine similarity × gap-type weight (research_gap=1.10,
  limitation=0.95). Bounded to [0, 1].
- **What's `novelty_score`?** Recency × similarity — high when the gap is
  recent *and* topical.
