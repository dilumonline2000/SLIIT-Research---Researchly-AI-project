# Module 1 — Training Data

This folder is the **input** to scripts in `../training/`. Nothing here is
loaded at runtime; the live service reads from `../models/` instead.

## Structure

```
data/
├── README.md                   ← you are here
├── raw/                        Linked from project-root ml/data/raw/sliit_papers/
├── processed/                  Output of training/prepare_*.py
│   ├── gap_corpus.json         553 gap sentences from 494 SLIIT papers
│   └── proposal_corpus.json    3,858 proposal exemplars
└── samples/                    Sample queries for viva demos / smoke tests
```

## Provenance

The raw source is `ml/data/raw/sliit_papers/papers_raw_sliit.json`
(4,219 papers from the SLIIT Research Data Archive). Each record has:
`id, title, authors, abstract, year, subject, url`.

`prepare_gap_corpus.py` runs 7 regex patterns over each abstract to extract
sentences that signal a research gap — `however ... has not`, `future work`,
`research gap`, etc. Each match becomes a `(gap_text, source_paper)` row.

`prepare_proposal_corpus.py` keeps every paper with a usable abstract
(≥120 chars + a title) and extracts a candidate problem statement,
objective sentence, and methodology sentence.

## Regenerating

```bash
python ../training/prepare_gap_corpus.py
python ../training/prepare_proposal_corpus.py
```

Both scripts are deterministic — same input → same output.

## Sample queries for demos

Use these in the UI to show off the gap analyzer at viva:

- *"machine learning in healthcare"*
- *"blockchain supply chain transparency"*
- *"deep learning for crop disease detection"*
- *"IoT security in smart cities"*
- *"natural language processing for Sinhala"*
- *"renewable energy forecasting Sri Lanka"*

Each returns 5–8 gaps each grounded in a different SLIIT paper.
