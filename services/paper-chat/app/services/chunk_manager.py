"""Recursive chunking for RAG retrieval."""

from __future__ import annotations

from typing import Any, Dict, List


def _classify(heading: str | None) -> str:
    if not heading:
        return "other"
    h = heading.lower()
    if "abstract" in h:
        return "abstract"
    if "introduction" in h or "background" in h:
        return "introduction"
    if "method" in h or "approach" in h:
        return "methodology"
    if "result" in h or "experiment" in h or "evaluation" in h:
        return "results"
    if "discussion" in h:
        return "discussion"
    if "conclusion" in h or "summary" in h:
        return "conclusion"
    if "reference" in h:
        return "references"
    return "other"


def chunk_document(
    extracted: Dict[str, Any],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[Dict[str, Any]]:
    """Split a paper's extracted_data into RAG chunks.

    Falls back to LangChain RecursiveCharacterTextSplitter if available;
    otherwise a simple word-window splitter so the pipeline never breaks.
    """
    sections = extracted.get("sections") or []
    abstract = (extracted.get("metadata") or {}).get("abstract")
    full_text = extracted.get("full_text") or ""

    splitter = None
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # token-ish heuristic: 1 token ≈ 4 chars
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,
            chunk_overlap=chunk_overlap * 4,
            separators=["\n\n", "\n", ". ", " "],
        )
    except Exception:
        splitter = None

    def _split(text: str) -> List[str]:
        if not text:
            return []
        if splitter is not None:
            return splitter.split_text(text)
        # Naive fallback
        words = text.split()
        size = chunk_size
        step = max(1, size - chunk_overlap)
        return [" ".join(words[i : i + size]) for i in range(0, len(words), step)]

    chunks: List[Dict[str, Any]] = []
    idx = 0

    if abstract:
        for piece in _split(abstract):
            chunks.append(
                {
                    "chunk_index": idx,
                    "chunk_text": piece,
                    "chunk_type": "abstract",
                    "section_heading": "Abstract",
                    "token_count": len(piece.split()),
                }
            )
            idx += 1

    if sections:
        for section in sections:
            heading = section.get("heading")
            ctype = _classify(heading)
            for piece in _split(section.get("content") or ""):
                chunks.append(
                    {
                        "chunk_index": idx,
                        "chunk_text": piece,
                        "chunk_type": ctype,
                        "section_heading": heading,
                        "page_start": section.get("page_start"),
                        "page_end": section.get("page_end"),
                        "token_count": len(piece.split()),
                    }
                )
                idx += 1
    else:
        # No section structure — just split full text
        for piece in _split(full_text):
            chunks.append(
                {
                    "chunk_index": idx,
                    "chunk_text": piece,
                    "chunk_type": "other",
                    "section_heading": None,
                    "token_count": len(piece.split()),
                }
            )
            idx += 1

    return chunks
