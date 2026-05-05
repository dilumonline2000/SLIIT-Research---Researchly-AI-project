"""Extract reusable proposal templates from the SLIIT paper corpus.

Reads `ml/data/raw/sliit_papers/papers_raw_sliit.json` and produces
`data/processed/proposal_corpus.json` — papers with a usable abstract become
"proposal exemplars" the retriever can pull from to compose new proposals.

For each paper we keep:
  - paper_id, title, authors, year, url, subject
  - abstract (used both as embedding text and as candidate problem-statement)
  - heuristically extracted: problem_statement, objectives_text, methodology_text

The retriever later finds top-K most-similar exemplars to a user's topic and
composes a new proposal by blending their fields.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SERVICE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

DEFAULT_INPUT = PROJECT_ROOT / "ml" / "data" / "raw" / "sliit_papers" / "papers_raw_sliit.json"
DEFAULT_OUTPUT = SERVICE_ROOT / "data" / "processed" / "proposal_corpus.json"

# Sentences that typically introduce a problem / objective / methodology.
PROBLEM_PATTERNS = [
    re.compile(r"\b(this (paper|study|research|work)|we|the authors)\s+(investigates?|examines?|analyzes?|studies|addresses|explores?|proposes?|presents?)[^.]{20,400}\.", re.IGNORECASE),
    re.compile(r"\b(the (problem|aim|goal|objective|purpose) of this)[^.]{10,400}\.", re.IGNORECASE),
]
OBJECTIVE_PATTERNS = [
    re.compile(r"\b(objective|aim|goal)s?[^.]{5,300}\.", re.IGNORECASE),
    re.compile(r"\bin order to[^.]{10,300}\.", re.IGNORECASE),
]
METHOD_PATTERNS = [
    re.compile(r"\b(use|using|employ|adopt|apply|conduct|perform|implement|develop)[a-z]*\s+([a-z]+\s+){0,4}(method|approach|technique|model|algorithm|framework|analysis|survey|interview|experiment|prototype|simulation)[^.]{0,300}\.", re.IGNORECASE),
    re.compile(r"\bthematic\s+analysis[^.]{0,250}\.", re.IGNORECASE),
    re.compile(r"\bmachine\s+learning[^.]{0,250}\.", re.IGNORECASE),
    re.compile(r"\bdeep\s+learning[^.]{0,250}\.", re.IGNORECASE),
]


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def _first_match(sentences: list[str], patterns: list[re.Pattern[str]]) -> str:
    for sent in sentences:
        for pat in patterns:
            if pat.search(sent):
                return sent
    return ""


def _extract_proposal_fields(abstract: str) -> dict[str, str]:
    sents = _split_sentences(abstract)
    if not sents:
        return {"problem_statement": "", "objectives_text": "", "methodology_text": ""}
    return {
        "problem_statement": _first_match(sents, PROBLEM_PATTERNS) or sents[0],
        "objectives_text": _first_match(sents, OBJECTIVE_PATTERNS),
        "methodology_text": _first_match(sents, METHOD_PATTERNS),
    }


def build_corpus(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in papers:
        abstract = (p.get("abstract") or "").strip()
        title = (p.get("title") or "").strip()
        if len(abstract) < 120 or not title:
            continue
        subj = p.get("subject")
        if isinstance(subj, list):
            subj = ", ".join(s for s in subj if s)
        fields = _extract_proposal_fields(abstract)
        out.append({
            "paper_id": str(p.get("id") or p.get("handle") or ""),
            "title": title,
            "authors": p.get("authors") or [],
            "year": p.get("year"),
            "url": p.get("url") or p.get("source_url") or "",
            "subject": subj,
            "abstract": abstract,
            **fields,
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build proposal exemplar corpus from SLIIT papers.")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--limit", type=int, default=0, help="Optional cap (0 = no cap).")
    args = ap.parse_args()

    print(f"[prepare_proposal_corpus] reading {args.input}")
    with open(args.input, encoding="utf-8") as f:
        papers = json.load(f)
    print(f"[prepare_proposal_corpus] loaded {len(papers)} papers")

    records = build_corpus(papers)
    if args.limit and len(records) > args.limit:
        records = records[: args.limit]
    print(f"[prepare_proposal_corpus] kept {len(records)} usable exemplars")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[prepare_proposal_corpus] wrote {args.output} ({args.output.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
