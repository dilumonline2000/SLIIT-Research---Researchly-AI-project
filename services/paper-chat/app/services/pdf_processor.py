"""PDF → structured JSON pipeline.

Uses PyMuPDF (fitz) as primary extractor; pdfplumber as fallback for
table-heavy layouts. Produces a JSON shape compatible with the
extracted_data column in uploaded_papers.
"""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any, Dict, List, Optional


_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_YEAR_RE = re.compile(r"(19|20)\d{2}")
_KEYWORDS_RE = re.compile(r"keywords[:\-\s]+(.+?)(?:\n\n|\n[A-Z])", re.IGNORECASE | re.DOTALL)
_ABSTRACT_RE = re.compile(
    r"abstract[\s\.:\-]*\n?(.{200,2500}?)(?:\n\s*(?:1\.|introduction|keywords|index terms))",
    re.IGNORECASE | re.DOTALL,
)
_REF_HEAD_RE = re.compile(r"^\s*references\s*$", re.IGNORECASE | re.MULTILINE)
_SECTION_HEAD_RE = re.compile(r"^(?:\d+\.?\s+)?([A-Z][A-Za-z0-9 \-]{3,60})$", re.MULTILINE)


def extract_text_pymupdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """Primary extractor."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text: List[str] = []
    for page in doc:
        pages_text.append(page.get_text("text") or "")
    full_text = "\n".join(pages_text)
    return {
        "full_text": full_text,
        "pages": pages_text,
        "page_count": len(pages_text),
    }


def extract_text_pdfplumber(pdf_bytes: bytes) -> Dict[str, Any]:
    """Fallback extractor for tricky layouts."""
    import pdfplumber

    pages_text: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    return {
        "full_text": "\n".join(pages_text),
        "pages": pages_text,
        "page_count": len(pages_text),
    }


def extract_text(pdf_bytes: bytes) -> Dict[str, Any]:
    try:
        out = extract_text_pymupdf(pdf_bytes)
        if out["full_text"].strip():
            return out
    except Exception:
        pass
    return extract_text_pdfplumber(pdf_bytes)


def _first_nonempty_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        s = line.strip()
        if s and len(s) > 6:
            return s
    return None


def extract_metadata(full_text: str) -> Dict[str, Any]:
    title = _first_nonempty_line(full_text)

    abstract: Optional[str] = None
    m = _ABSTRACT_RE.search(full_text)
    if m:
        abstract = m.group(1).strip()

    keywords: List[str] = []
    k = _KEYWORDS_RE.search(full_text)
    if k:
        raw = k.group(1).strip()
        keywords = [w.strip() for w in re.split(r"[;,]", raw) if w.strip()][:12]

    doi_m = _DOI_RE.search(full_text)
    doi = doi_m.group(0) if doi_m else None

    year = None
    y = _YEAR_RE.search(full_text[:600])
    if y:
        year = int(y.group(0))

    # Authors heuristic: line right after the title with comma-separated names
    authors: List[str] = []
    if title:
        idx = full_text.find(title)
        after = full_text[idx + len(title): idx + len(title) + 400]
        for line in after.splitlines():
            s = line.strip()
            if not s:
                continue
            # heuristic: line containing 1-6 commas and capitalised words
            if 1 <= s.count(",") <= 8 and re.match(r"^[A-Z]", s):
                authors = [a.strip() for a in s.split(",") if a.strip()][:10]
                break

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "doi": doi,
        "year": year,
        "venue": None,
    }


def extract_sections(full_text: str) -> List[Dict[str, Any]]:
    """Naive section splitting on heading-looking lines."""
    sections: List[Dict[str, Any]] = []
    matches = list(_SECTION_HEAD_RE.finditer(full_text))
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        content = full_text[start:end].strip()
        if not content:
            continue
        sections.append(
            {
                "heading": heading,
                "content": content,
                "page_start": None,
                "page_end": None,
            }
        )
    return sections[:30]  # cap


def extract_references(full_text: str) -> List[Dict[str, Any]]:
    m = _REF_HEAD_RE.search(full_text)
    if not m:
        return []
    block = full_text[m.end():]
    # Split on numbered list patterns
    items = re.split(r"\n\s*\[?\d+[\].]\s+", block)
    refs: List[Dict[str, Any]] = []
    for item in items:
        s = item.strip()
        if not s or len(s) < 20:
            continue
        year_m = _YEAR_RE.search(s)
        refs.append(
            {
                "raw": s[:500],
                "parsed": {
                    "year": int(year_m.group(0)) if year_m else None,
                },
            }
        )
        if len(refs) >= 100:
            break
    return refs


def build_extracted_data(pdf_bytes: bytes) -> Dict[str, Any]:
    base = extract_text(pdf_bytes)
    full_text = base["full_text"]
    metadata = extract_metadata(full_text)
    sections = extract_sections(full_text)
    references = extract_references(full_text)

    word_count = len(full_text.split())
    return {
        "metadata": metadata,
        "sections": sections,
        "tables": [],
        "figures": [],
        "references": references,
        "full_text": full_text,
        "statistics": {
            "word_count": word_count,
            "char_count": len(full_text),
            "page_count": base["page_count"],
            "section_count": len(sections),
            "reference_count": len(references),
            "table_count": 0,
            "figure_count": 0,
        },
    }
