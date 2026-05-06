"""Citation parsing + formatting engine.

Self-contained — no external API calls. Used by `app/routers/citation.py`.

Responsibilities:
  1. Detect the source type (journal | book | conference | website)
  2. Extract structured fields with regex + light heuristics
  3. Format the parsed record in IEEE or APA according to its source type
  4. Build in-text citations
  5. Return a list of missing-field warnings the UI can display

Public API:
    parse(raw_text: str) -> dict
    format_citation(parsed: dict, style: 'ieee' | 'apa') -> str
    in_text(parsed: dict, style: 'ieee' | 'apa', index: int = 1) -> str
    detect_source_type(raw_text: str) -> str
    missing_fields(parsed: dict) -> list[str]
"""

from __future__ import annotations

import re
from typing import Any

# ─── Source-type heuristics ──────────────────────────────────────────────

_URL_RE = re.compile(r"\bhttps?://\S+", re.IGNORECASE)
_DOI_RE = re.compile(r"\b(?:doi:\s*)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
_YEAR_RE = re.compile(r"(?:\(\s*(\d{4})\s*\)|\b(19|20)\d{2}\b)")
_PAGE_RE = re.compile(r"\bpp?\.?\s*(\d+\s*[-–—]\s*\d+)\b", re.IGNORECASE)
_VOLUME_RE = re.compile(r"\bvol\.?\s*(\d+)|\bvolume\s+(\d+)", re.IGNORECASE)
_ISSUE_RE = re.compile(r"\bno\.?\s*(\d+)|\bissue\s+(\d+)", re.IGNORECASE)
_PUBLISHER_HINT = re.compile(
    r"\b(Springer|Wiley|Elsevier|MIT Press|Oxford|Cambridge|Pearson|Routledge|"
    r"O'?Reilly|Manning|Packt|McGraw[- ]Hill|Prentice Hall|Sage|IEEE Press|"
    r"ACM Press|Taylor & Francis|CRC Press|Academic Press|Addison[- ]Wesley)\b",
    re.IGNORECASE,
)
_CONF_HINT = re.compile(
    r"\b(?:Proc(?:eedings)?|Conf(?:erence)?|Workshop|Symposium|"
    r"Int'?l\.?|International)\b",
    re.IGNORECASE,
)
_JOURNAL_HINT = re.compile(
    r"\b(?:Journal|J\.|Trans(?:actions)?|Transactions of the|Letters|Review|Quarterly)\b",
    re.IGNORECASE,
)


def detect_source_type(text: str) -> str:
    if _URL_RE.search(text) and not _DOI_RE.search(text) and not _JOURNAL_HINT.search(text):
        return "website"
    if _CONF_HINT.search(text):
        return "conference"
    if _JOURNAL_HINT.search(text):
        return "journal"
    if _PUBLISHER_HINT.search(text) and not _JOURNAL_HINT.search(text):
        return "book"
    # If a DOI is present but no other strong hints, treat as journal
    if _DOI_RE.search(text):
        return "journal"
    return "journal"  # safe default


# ─── Author extraction ────────────────────────────────────────────────────

_INITIALS_NAME_RE = re.compile(
    r"([A-Z][a-z]+(?:[- ][A-Z][a-z]+)*),?\s+([A-Z](?:\.\s*[A-Z])*\.?)"
)
_NAME_INITIALS_RE = re.compile(
    r"([A-Z](?:\.\s*[A-Z])*\.?)\s+([A-Z][a-z]+(?:[- ][A-Z][a-z]+)*)"
)


def _extract_authors(chunk: str) -> list[str]:
    """Try several common author-list patterns. Returns names normalised to
    'Last, F.' style, suitable for both APA and IEEE post-processing."""
    if not chunk:
        return []
    chunk = chunk.strip().rstrip(".,")

    # Replace " and " / " & " with comma so we have a single delimiter
    cleaned = re.sub(r"\s+&\s+|\s+and\s+", ", ", chunk)
    # Split on semicolon first (common separator), else on comma
    if ";" in cleaned:
        parts = [p.strip() for p in cleaned.split(";") if p.strip()]
    else:
        # Be careful: "Smith, J., Doe, A." has commas inside names too.
        # Heuristic: pair "Last, Initials" tokens.
        parts = _smart_split_authors(cleaned)

    authors: list[str] = []
    for p in parts:
        p = p.strip().rstrip(",.")
        if not p or len(p) < 2:
            continue
        # Already "Last, Initials" form?
        m = _INITIALS_NAME_RE.match(p)
        if m:
            last, initials = m.group(1), m.group(2).replace(" ", "")
            authors.append(f"{last}, {initials.rstrip('.')}.")
            continue
        # "F. Last" or "John Smith" form
        m2 = _NAME_INITIALS_RE.match(p)
        if m2:
            initials, last = m2.group(1).replace(" ", ""), m2.group(2)
            authors.append(f"{last}, {initials.rstrip('.')}.")
            continue
        # Last resort: keep the raw token
        authors.append(p)
    return authors


def _smart_split_authors(text: str) -> list[str]:
    """Split 'Smith, J., Doe, A., Brown, B.' → ['Smith, J.', 'Doe, A.', 'Brown, B.']
    by detecting 'Last, Initials' pairs.
    """
    pieces = [p.strip() for p in text.split(",") if p.strip()]
    out: list[str] = []
    i = 0
    while i < len(pieces):
        cur = pieces[i]
        # Look ahead — if next piece looks like initials, glue them
        if i + 1 < len(pieces) and re.fullmatch(r"[A-Z](?:\.?\s*[A-Z])*\.?", pieces[i + 1]):
            out.append(f"{cur}, {pieces[i + 1]}")
            i += 2
        else:
            out.append(cur)
            i += 1
    return out


# ─── Master parser ────────────────────────────────────────────────────────


def parse(raw_text: str) -> dict[str, Any]:
    """Extract structured fields from a raw citation string."""
    text = (raw_text or "").strip()
    out: dict[str, Any] = {
        "raw": text,
        "source_type": detect_source_type(text),
        "authors": [],
        "title": "",
        "year": None,
        "journal": None,        # journal articles
        "conference": None,     # conference papers
        "publisher": None,      # books
        "url": None,            # websites
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "edition": None,
    }
    if not text:
        return out

    # DOI / URL
    doi_m = _DOI_RE.search(text)
    if doi_m:
        out["doi"] = doi_m.group(1).rstrip(".,")
    url_m = _URL_RE.search(text)
    if url_m:
        out["url"] = url_m.group(0).rstrip(".,)")
    publisher_m = _PUBLISHER_HINT.search(text)
    if publisher_m:
        out["publisher"] = publisher_m.group(0)
    vol_m = _VOLUME_RE.search(text)
    if vol_m:
        out["volume"] = next((g for g in vol_m.groups() if g), None)
    iss_m = _ISSUE_RE.search(text)
    if iss_m:
        out["issue"] = next((g for g in iss_m.groups() if g), None)
    pg_m = _PAGE_RE.search(text)
    if pg_m:
        out["pages"] = pg_m.group(1).replace(" ", "").replace("—", "-").replace("–", "-")

    # Year — pick the latest 4-digit year that's between 1800 and (current+1)
    years = [int(y) for tup in _YEAR_RE.findall(text) for y in tup if y]
    valid = [y for y in years if 1800 <= y <= 2099]
    if valid:
        out["year"] = max(valid) if len(valid) > 1 else valid[0]

    # Authors / title — split on the year position when present
    if out["year"]:
        # APA shape: "Smith, J. (2020). Title. Journal..."
        year_marker = re.search(rf"\(?\s*{out['year']}\s*\)?\.?", text)
        if year_marker:
            author_chunk = text[: year_marker.start()].strip().rstrip(",.()")
            after = text[year_marker.end():].strip().lstrip(",.) ")
            out["authors"] = _extract_authors(author_chunk)
            # Title = sentence up to first period, but keep the rest as venue
            title_m = re.match(r"(.+?)[\.!?](\s+[A-Z]|\s*$)", after)
            if title_m:
                out["title"] = title_m.group(1).strip().rstrip(",.")
                rest_after_title = after[title_m.end():].strip(" .,")
            else:
                out["title"] = after.split(".")[0].strip()
                rest_after_title = ""
            _attach_venue(out, rest_after_title)
        else:
            _fallback_split(out, text)
    else:
        _fallback_split(out, text)

    # If we found a title that begins with a quote, strip the quotes
    if out["title"]:
        out["title"] = out["title"].strip().strip('"').strip("'").strip()

    return out


def _fallback_split(out: dict[str, Any], text: str) -> None:
    """When no year is detected, do a coarse first-sentence-as-title split."""
    sentences = [s.strip() for s in re.split(r"\.(?:\s+|$)", text) if s.strip()]
    if not sentences:
        return
    if len(sentences) >= 2:
        out["authors"] = _extract_authors(sentences[0])
        out["title"] = sentences[1]
        _attach_venue(out, ". ".join(sentences[2:]))
    else:
        out["title"] = sentences[0]


def _attach_venue(out: dict[str, Any], rest: str) -> None:
    """Best-effort venue assignment based on detected source type."""
    if not rest:
        return
    rest = rest.strip().rstrip(".")
    # Remove trailing volume/issue/page noise so the venue is clean
    rest_clean = re.sub(r",?\s*(vol\.?|volume|no\.?|issue|pp?\.?)\s*\d+.*$", "", rest, flags=re.IGNORECASE).strip().rstrip(".,")

    if out["source_type"] == "conference":
        out["conference"] = rest_clean[:200] or None
    elif out["source_type"] == "book":
        # Strip publisher from venue if both detected
        if out["publisher"]:
            rest_clean = rest_clean.replace(out["publisher"], "").strip(", .").strip()
        if rest_clean:
            out["publisher"] = out["publisher"] or rest_clean[:200]
    elif out["source_type"] == "website":
        # Title may already be set; nothing more to do
        pass
    else:
        out["journal"] = rest_clean[:200] or None


# ─── Missing-field warnings ──────────────────────────────────────────────


def missing_fields(parsed: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not parsed.get("authors"):
        warnings.append("Author(s) not found — please add at least one author.")
    if not parsed.get("title"):
        warnings.append("Title not found — please add the paper title.")
    if not parsed.get("year"):
        warnings.append("Year not found — please add the publication year.")

    src = parsed.get("source_type")
    if src == "journal" and not parsed.get("journal"):
        warnings.append("Journal name missing — please add the journal.")
    if src == "conference" and not parsed.get("conference"):
        warnings.append("Conference name missing — please add the conference name.")
    if src == "book" and not parsed.get("publisher"):
        warnings.append("Publisher missing — please add the publisher.")
    if src == "website" and not parsed.get("url"):
        warnings.append("URL missing — please add the link.")

    return warnings


# ─── Formatters ──────────────────────────────────────────────────────────
# Output uses *italic* markers so the frontend can render them as <em>.


def _apa_authors(authors: list[str]) -> str:
    """APA: Last, F. M., Last, F. M., & Last, F. M."""
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]}, & {authors[1]}"
    return ", ".join(authors[:-1]) + f", & {authors[-1]}"


def _ieee_authors(authors: list[str]) -> str:
    """IEEE: F. Last, F. Last, and F. Last."""
    out: list[str] = []
    for a in authors:
        m = re.match(r"([A-Za-z\-' ]+?),\s*([A-Z](?:\.\s*[A-Z])*\.?)", a)
        if m:
            last, init = m.group(1).strip(), m.group(2).replace(" ", "")
            if not init.endswith("."):
                init += "."
            out.append(f"{init} {last}")
        else:
            out.append(a)
    if not out:
        return ""
    if len(out) == 1:
        return out[0]
    if len(out) == 2:
        return f"{out[0]} and {out[1]}"
    return ", ".join(out[:-1]) + f", and {out[-1]}"


def _sentence_case(s: str) -> str:
    """APA title case = sentence case (only first word + proper nouns capitalised).
    Simple heuristic: lowercase everything except the first character and any
    word that was already ALL CAPS (likely an acronym like 'IoT', 'DNN')."""
    if not s:
        return ""
    words = s.split()
    out = []
    for i, w in enumerate(words):
        if w.isupper() and len(w) > 1:
            out.append(w)
        elif i == 0:
            out.append(w[0].upper() + w[1:].lower())
        else:
            out.append(w.lower() if w[0].isupper() and not w[1:].isupper() else w)
    # Re-capitalise after a colon (APA convention)
    joined = " ".join(out)
    joined = re.sub(r":\s+([a-z])", lambda m: ": " + m.group(1).upper(), joined)
    return joined


def _doi_url(doi: str) -> str:
    if doi.startswith("http"):
        return doi
    return f"https://doi.org/{doi.replace('doi:', '').strip()}"


def format_apa(p: dict[str, Any]) -> str:
    parts: list[str] = []
    auth = _apa_authors(p.get("authors") or [])
    if auth:
        parts.append(auth if auth.endswith(".") else f"{auth}.")
    if p.get("year"):
        parts.append(f"({p['year']}).")

    src = p.get("source_type", "journal")
    title = p.get("title") or ""

    if src == "book":
        # Book title in italics, sentence case
        if title:
            parts.append(f"*{_sentence_case(title)}*.")
        if p.get("edition"):
            parts.append(f"({p['edition']}).")
        if p.get("publisher"):
            parts.append(f"{p['publisher']}.")
    elif src == "conference":
        if title:
            parts.append(f"{_sentence_case(title)}.")
        if p.get("conference"):
            parts.append(f"In *{p['conference']}*")
            if p.get("pages"):
                parts.append(f"(pp. {p['pages']}).")
            else:
                parts[-1] = parts[-1] + "."
        if p.get("publisher"):
            parts.append(f"{p['publisher']}.")
    elif src == "website":
        if title:
            parts.append(f"*{_sentence_case(title)}*.")
        if p.get("url"):
            parts.append(p["url"])
    else:  # journal
        if title:
            parts.append(f"{_sentence_case(title)}.")
        if p.get("journal"):
            jpart = f"*{p['journal']}*"
            if p.get("volume"):
                jpart += f", *{p['volume']}*"
            if p.get("issue"):
                jpart += f"({p['issue']})"
            if p.get("pages"):
                jpart += f", {p['pages']}"
            parts.append(f"{jpart}.")
        if p.get("doi"):
            parts.append(_doi_url(p["doi"]))
        elif p.get("url"):
            parts.append(p["url"])

    return " ".join(parts)


def format_ieee(p: dict[str, Any]) -> str:
    parts: list[str] = []
    auth = _ieee_authors(p.get("authors") or [])
    if auth:
        parts.append(f"{auth},")

    src = p.get("source_type", "journal")
    title = p.get("title") or ""

    if src == "book":
        # Book title in italics, no quotes
        if title:
            parts.append(f"*{title}*,")
        if p.get("edition"):
            parts.append(f"{p['edition']},")
        if p.get("publisher"):
            parts.append(f"{p['publisher']},")
        if p.get("year"):
            parts.append(f"{p['year']}.")
    elif src == "conference":
        if title:
            parts.append(f'"{title},"')
        if p.get("conference"):
            parts.append(f"in *{p['conference']}*,")
        if p.get("pages"):
            parts.append(f"pp. {p['pages']},")
        if p.get("year"):
            parts.append(f"{p['year']}.")
    elif src == "website":
        if title:
            parts.append(f'"{title}."')
        if p.get("url"):
            parts.append(f"[Online]. Available: {p['url']}")
    else:  # journal
        if title:
            parts.append(f'"{title},"')
        if p.get("journal"):
            parts.append(f"*{p['journal']}*,")
        if p.get("volume"):
            parts.append(f"vol. {p['volume']},")
        if p.get("issue"):
            parts.append(f"no. {p['issue']},")
        if p.get("pages"):
            parts.append(f"pp. {p['pages']},")
        if p.get("year"):
            parts.append(f"{p['year']}.")
        if p.get("doi"):
            parts.append(f"doi: {p['doi']}.")

    out = " ".join(parts).strip()
    # Tidy duplicated commas/periods that arise from missing fields
    out = re.sub(r"\s*,\s*,", ",", out)
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\s*([.,])", r"\1", out)
    out = out.rstrip(",").strip()
    if out and not out.endswith("."):
        out += "."
    return out


def format_citation(parsed: dict[str, Any], style: str) -> str:
    style = (style or "").lower()
    if style == "ieee":
        return format_ieee(parsed)
    return format_apa(parsed)


def in_text(parsed: dict[str, Any], style: str, index: int = 1) -> str:
    """Generate the in-text citation: APA → (Smith, 2020); IEEE → [1]."""
    if style.lower() == "ieee":
        return f"[{max(1, index)}]"
    authors = parsed.get("authors") or []
    year = parsed.get("year")
    if not authors:
        return f"(Unknown, {year or 'n.d.'})"
    # Take last name of the first author
    first = authors[0]
    last = first.split(",")[0].strip() if "," in first else first.split()[-1]
    if len(authors) == 1:
        return f"({last}, {year or 'n.d.'})"
    if len(authors) == 2:
        second_last = authors[1].split(",")[0].strip() if "," in authors[1] else authors[1].split()[-1]
        return f"({last} & {second_last}, {year or 'n.d.'})"
    return f"({last} et al., {year or 'n.d.'})"


# ─── Reference list ──────────────────────────────────────────────────────


def build_reference_list(parsed_list: list[dict[str, Any]], style: str) -> list[str]:
    """Render N parsed citations into the requested style.

    IEEE: numbered list, preserves input order.
    APA:  alphabetical by first author surname.
    """
    style = style.lower()
    if style == "ieee":
        return [
            f"[{i + 1}] {format_ieee(p)}"
            for i, p in enumerate(parsed_list)
        ]
    # APA: sort by first author last name (case-insensitive), then year
    def key(p: dict[str, Any]) -> tuple[str, int]:
        a = (p.get("authors") or ["zzz"])[0]
        last = a.split(",")[0].strip().lower() if "," in a else a.split()[-1].lower()
        year = p.get("year") or 9999
        return (last, year)

    return [format_apa(p) for p in sorted(parsed_list, key=key)]
