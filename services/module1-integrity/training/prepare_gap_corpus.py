"""Extract research-gap statements from the SLIIT paper corpus.

Reads `ml/data/raw/sliit_papers/papers_raw_sliit.json` (4,219 papers) and produces
`data/processed/gap_corpus.json` — a list of (gap_text, source_paper) records used
to train the local gap-analyzer.

Heuristic gap signals (regex over abstract sentences):
    "however ... has not / is not / lacks / limited"
    "future work / further research / future research"
    "remains unclear / remains unexplored / remains an open question"
    "few studies / little research / limited research"
    "research gap"
    "more research is needed"
    "no consensus / not been investigated"

For every match we keep:
  - gap_text: the matched sentence
  - paper_id, title, authors, year, subject, url
  - topic: best-effort topic label (subject if present, else first noun-phrase of title)

This corpus is the *training data* for the retrieval index. No labels needed —
similarity is supervised by SBERT pretraining.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

# ───────────────────────────────────────────────── paths
SERVICE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

DEFAULT_INPUT = PROJECT_ROOT / "ml" / "data" / "raw" / "sliit_papers" / "papers_raw_sliit.json"
DEFAULT_OUTPUT = SERVICE_ROOT / "data" / "processed" / "gap_corpus.json"

# ───────────────────────────────────────────────── gap-signal patterns
# Each pattern carries a "gap_type" tag so the analyzer can later weight them.
GAP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("limitation", re.compile(r"\b(however|although|despite|nevertheless),?\s+[^.]{10,200}\b(not|no|lack|limited|insufficient|few|fail)[^.]{0,200}\.", re.IGNORECASE)),
    ("future_work", re.compile(r"\b(future\s+(work|research|study|studies|direction)|further\s+research)[^.]{5,250}\.", re.IGNORECASE)),
    ("unexplored", re.compile(r"\b(remains?|still)\s+(unclear|unexplored|an\s+open|to\s+be\s+investigated|to\s+be\s+studied)[^.]{0,250}\.", re.IGNORECASE)),
    ("scarcity", re.compile(r"\b(few|little|limited|scarce|sparse)\s+(studies|research|literature|work|attention)[^.]{0,250}\.", re.IGNORECASE)),
    ("research_gap", re.compile(r"\bresearch\s+gap[^.]{0,250}\.", re.IGNORECASE)),
    ("more_needed", re.compile(r"\bmore\s+(research|study|investigation|work|empirical evidence)\s+(is|are|will be)\s+(needed|required|necessary)[^.]{0,250}\.", re.IGNORECASE)),
    ("not_investigated", re.compile(r"\b(has|have|had)\s+not\s+(been|yet)\s+(investigated|studied|examined|explored|addressed)[^.]{0,250}\.", re.IGNORECASE)),
]

# Sentences shorter than this are usually too generic to be a real gap.
MIN_GAP_LEN = 25
MAX_GAP_LEN = 400


def _split_sentences(text: str) -> list[str]:
    """Light sentence splitter — abstracts are well-formed enough that we
    don't need spaCy here."""
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def _extract_gaps(abstract: str) -> list[dict[str, str]]:
    """Find all gap-signal sentences in an abstract."""
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for sent in _split_sentences(abstract):
        if not (MIN_GAP_LEN <= len(sent) <= MAX_GAP_LEN):
            continue
        for gap_type, pat in GAP_PATTERNS:
            if pat.search(sent):
                key = sent.lower()[:120]
                if key in seen:
                    continue
                seen.add(key)
                found.append({"gap_type": gap_type, "gap_text": sent})
                break
    return found


def _normalize_topic(paper: dict[str, Any]) -> str:
    """Pick a topic label. SLIIT papers have a `subject` field which is the
    cleanest signal; fall back to the first 8 words of the title."""
    subj = paper.get("subject") or ""
    if isinstance(subj, list):
        subj = ", ".join(s for s in subj if s)
    subj = (subj or "").strip()
    if subj and len(subj) > 3:
        return subj[:120]
    title = (paper.get("title") or "").strip()
    return " ".join(title.split()[:8])[:120] if title else "general"


def build_corpus(papers: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Yield one record per gap sentence (a paper can contribute several)."""
    records: list[dict[str, Any]] = []
    for p in papers:
        abstract = p.get("abstract") or ""
        if len(abstract) < 80:
            continue
        gaps = _extract_gaps(abstract)
        if not gaps:
            continue

        paper_meta = {
            "paper_id": str(p.get("id") or p.get("handle") or ""),
            "title": (p.get("title") or "").strip(),
            "authors": p.get("authors") or [],
            "year": p.get("year"),
            "url": p.get("url") or p.get("source_url") or "",
            "subject": p.get("subject"),
            "topic": _normalize_topic(p),
        }
        for g in gaps:
            records.append({**paper_meta, **g})
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract research gaps from SLIIT papers.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    print(f"[prepare_gap_corpus] reading {args.input}")
    with open(args.input, encoding="utf-8") as f:
        papers = json.load(f)
    print(f"[prepare_gap_corpus] loaded {len(papers)} papers")

    records = build_corpus(papers)
    print(f"[prepare_gap_corpus] extracted {len(records)} gap sentences")

    type_counts: dict[str, int] = {}
    for r in records:
        type_counts[r["gap_type"]] = type_counts.get(r["gap_type"], 0) + 1
    print(f"[prepare_gap_corpus] gap_type breakdown: {type_counts}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[prepare_gap_corpus] wrote {args.output} ({args.output.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
