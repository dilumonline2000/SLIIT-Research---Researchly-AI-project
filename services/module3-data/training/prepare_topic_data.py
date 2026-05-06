"""Build the topic-classifier training corpus from SLIIT papers.

Reads `ml/data/raw/sliit_papers/papers_raw_sliit.json` and produces
`data/processed/topic_training.json` — one record per paper with:
  - text   : title + " . " + abstract
  - labels : list[str]  (multi-label)
  - paper_id, year, url

Labels come from the paper's `subject` field, which is a comma- or
semicolon-separated string of keywords. We:
  1. Split on `[,;]` and `[\\u00b7|]`
  2. Lower-case + strip
  3. Drop labels that appear < MIN_LABEL_FREQ times across the corpus
     (avoids one-off categories)
  4. Cap to TOP_K most common labels per category bucket

The result is a clean multi-label corpus suitable for a TF-IDF + LogReg
one-vs-rest classifier.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SERVICE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

DEFAULT_INPUT = PROJECT_ROOT / "ml" / "data" / "raw" / "sliit_papers" / "papers_raw_sliit.json"
DEFAULT_OUTPUT = SERVICE_ROOT / "data" / "processed" / "topic_training.json"
DEFAULT_LABELS_OUTPUT = SERVICE_ROOT / "data" / "processed" / "topic_labels.json"

MIN_LABEL_FREQ = 5      # drop labels seen in < 5 papers
MAX_LABELS_TOTAL = 80   # cap vocabulary
MIN_TEXT_LEN = 80


_split_re = re.compile(r"[;,·|]+")
_clean_re = re.compile(r"[^a-z0-9 \-]+")


def _normalize_label(s: str) -> str:
    s = s.strip().lower()
    s = _clean_re.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extract_labels(paper: dict[str, Any]) -> list[str]:
    raw = paper.get("subject")
    if raw is None:
        return []
    if isinstance(raw, list):
        items = []
        for x in raw:
            items.extend(_split_re.split(str(x)))
    else:
        items = _split_re.split(str(raw))
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        n = _normalize_label(item)
        if 3 <= len(n) <= 60 and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def build(papers: list[dict[str, Any]]):
    # Pass 1: count label frequency
    label_counts: Counter[str] = Counter()
    raw_records = []
    for p in papers:
        title = (p.get("title") or "").strip()
        abstract = (p.get("abstract") or "").strip()
        if len(title) + len(abstract) < MIN_TEXT_LEN:
            continue
        labels = _extract_labels(p)
        if not labels:
            continue
        for lab in labels:
            label_counts[lab] += 1
        raw_records.append((p, title, abstract, labels))

    # Build the kept-label vocab
    common = [lab for lab, c in label_counts.most_common(MAX_LABELS_TOTAL) if c >= MIN_LABEL_FREQ]
    vocab = set(common)
    print(f"[prepare_topic_data] {len(label_counts)} unique raw labels -> {len(vocab)} kept (>= {MIN_LABEL_FREQ} papers)")

    # Pass 2: filter records to only those that have at least one kept label
    out_records = []
    for p, title, abstract, labels in raw_records:
        kept = [lab for lab in labels if lab in vocab]
        if not kept:
            continue
        out_records.append({
            "paper_id": str(p.get("id") or p.get("handle") or ""),
            "text": f"{title}. {abstract}",
            "labels": kept,
            "year": p.get("year"),
            "url": p.get("url") or p.get("source_url") or "",
        })

    return out_records, common, label_counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Prepare multi-label topic training data from SLIIT papers.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--labels-output", type=Path, default=DEFAULT_LABELS_OUTPUT)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        papers = json.load(f)
    print(f"[prepare_topic_data] loaded {len(papers)} papers")

    records, kept_labels, all_counts = build(papers)
    print(f"[prepare_topic_data] kept {len(records)} labelled papers across {len(kept_labels)} categories")
    print(f"[prepare_topic_data] top-10 labels: {[ (l, all_counts[l]) for l in kept_labels[:10] ]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    with open(args.labels_output, "w", encoding="utf-8") as f:
        json.dump({
            "labels": kept_labels,
            "frequencies": {l: all_counts[l] for l in kept_labels},
        }, f, ensure_ascii=False, indent=2)

    print(f"[prepare_topic_data] wrote {args.output} ({args.output.stat().st_size/1024:.1f} KB)")
    print(f"[prepare_topic_data] wrote {args.labels_output}")


if __name__ == "__main__":
    main()
