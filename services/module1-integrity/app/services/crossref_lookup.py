"""CrossRef + Semantic Scholar metadata lookup.

CrossRef is free, no API key, generous rate limits. Semantic Scholar is the
fallback for cases CrossRef doesn't cover (e.g. some computer-science venues).

Public API:
    lookup_doi(doi: str) -> dict | None
    search_title(title: str, limit: int = 5) -> list[dict]
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CROSSREF_BASE = "https://api.crossref.org"
SEMSCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
TIMEOUT = 12.0
USER_AGENT = "Researchly-AI/1.0 (mailto:noreply@researchly.local)"


def _normalize_crossref(item: dict[str, Any]) -> dict[str, Any]:
    """Map CrossRef's response shape to our internal `parsed` shape."""
    authors_list = item.get("author") or []
    authors: list[str] = []
    for a in authors_list:
        family = a.get("family") or ""
        given = a.get("given") or ""
        if family and given:
            initials = ".".join(p[0] for p in given.split() if p) + "."
            authors.append(f"{family}, {initials}")
        elif family:
            authors.append(family)

    title = ""
    if item.get("title"):
        title = item["title"][0] if isinstance(item["title"], list) else str(item["title"])

    container = ""
    if item.get("container-title"):
        container = item["container-title"][0] if isinstance(item["container-title"], list) else str(item["container-title"])

    issued = item.get("issued", {}).get("date-parts") or []
    year = None
    if issued and isinstance(issued[0], list) and issued[0]:
        try:
            year = int(issued[0][0])
        except (TypeError, ValueError):
            year = None

    src_type_raw = (item.get("type") or "").lower()
    if "book" in src_type_raw and "chapter" not in src_type_raw:
        src_type = "book"
    elif "proceedings" in src_type_raw or "conference" in src_type_raw:
        src_type = "conference"
    elif "journal" in src_type_raw:
        src_type = "journal"
    else:
        src_type = "journal"

    out: dict[str, Any] = {
        "source_type": src_type,
        "authors": authors,
        "title": title.strip(),
        "year": year,
        "journal": container if src_type in ("journal", None) else None,
        "conference": container if src_type == "conference" else None,
        "publisher": item.get("publisher"),
        "url": item.get("URL"),
        "volume": str(item["volume"]) if item.get("volume") else None,
        "issue": str(item["issue"]) if item.get("issue") else None,
        "pages": item.get("page"),
        "doi": item.get("DOI"),
        "edition": item.get("edition") if item.get("edition") else None,
    }
    return out


def lookup_doi(doi: str) -> dict[str, Any] | None:
    """Fetch citation metadata for a DOI from CrossRef. Returns None on failure."""
    doi = (doi or "").strip()
    if not doi:
        return None
    if doi.startswith("http"):
        # Strip url prefix
        doi = doi.split("doi.org/", 1)[-1]
    doi = doi.replace("doi:", "").strip()

    try:
        with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(f"{CROSSREF_BASE}/works/{doi}")
            if r.status_code == 200:
                msg = (r.json() or {}).get("message")
                if msg:
                    return _normalize_crossref(msg)
            logger.info("CrossRef DOI lookup %s -> %d", doi, r.status_code)
    except Exception as e:
        logger.warning("CrossRef lookup failed for %s: %s", doi, e)
    return None


def search_title(title: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search CrossRef by title. Returns up to `limit` candidate metadata records."""
    title = (title or "").strip()
    if not title:
        return []
    try:
        with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(
                f"{CROSSREF_BASE}/works",
                params={"query.bibliographic": title, "rows": limit},
            )
            if r.status_code == 200:
                items = ((r.json() or {}).get("message") or {}).get("items") or []
                return [_normalize_crossref(it) for it in items]
            logger.info("CrossRef title search %r -> %d", title, r.status_code)
    except Exception as e:
        logger.warning("CrossRef title search failed: %s", e)
    return []
