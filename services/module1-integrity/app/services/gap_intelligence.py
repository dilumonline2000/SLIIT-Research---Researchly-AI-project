"""Research-intelligence layer on top of `gap_analyzer`.

Enriches the basic SBERT-retrieved gaps with:

  • `gap_classification`            future_work | methodology | dataset | domain | performance
  • `multi_dim_score`              composite of similarity / recency / novelty / gap-type weight
  • `explanation`                  human-readable reason for each gap
  • year-wise trend stats          "declining since 2022", etc.
  • cross-domain opportunities     topic pairs with sparse coverage in the corpus
  • clustering / saturation        which subtopics are over-researched
  • smart recommendations          auto-generated research-direction titles + abstracts

Public API:
    analyze(query, top_k, min_similarity, year_from=None, year_to=None) -> dict
    generate_report_html(payload) -> str
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ─── Gap classification ───────────────────────────────────────────────────

CLASS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("future_work", re.compile(r"\b(future\s+(work|research|direction|study|studies)|further (research|study|investigation))\b", re.IGNORECASE)),
    ("methodology", re.compile(r"\b(method(ology)?|approach|technique|model|algorithm|framework)\b.*\b(lack|limit|miss|need|insufficient|inadequate|fail)|\b(lack|limit|miss|need|insufficient|inadequate)\b.*\b(method(ology)?|approach|technique)\b", re.IGNORECASE)),
    ("dataset",     re.compile(r"\b(dataset|data\s+(availability|set|samples?)|sample\s+size|small\s+(corpus|sample|dataset)|labelled?\s+data|training\s+data)\b", re.IGNORECASE)),
    ("performance", re.compile(r"\b(accuracy|precision|recall|f1|performance|outperform|baseline|state[- ]of[- ]the[- ]art|benchmark)\b.*\b(low|poor|limit|need|further|improve|insufficient)\b|\b(low|poor|limit|need|insufficient)\b.*\b(accuracy|precision|performance)\b", re.IGNORECASE)),
    ("domain",      re.compile(r"\b(in\s+(Sri Lanka|developing|context|local|regional|specific\s+(industry|sector|domain))|sector|industry|context-specific|cultural)\b", re.IGNORECASE)),
]

# Display weights — used in `multi_dim_score`
TYPE_WEIGHTS = {
    "research_gap":       1.10,
    "not_investigated":   1.08,
    "unexplored":         1.06,
    "more_needed":        1.04,
    "future_work":        1.02,
    "scarcity":           1.00,
    "limitation":         0.95,
}

CATEGORY_LABELS = {
    "future_work":  "Future-work gap",
    "methodology":  "Methodological gap",
    "dataset":      "Dataset / data gap",
    "domain":       "Domain / contextual gap",
    "performance":  "Performance gap",
    "general":      "General gap",
}


def classify(gap_text: str, default_type: str = "limitation") -> str:
    """Map a gap sentence to one of the five high-level categories."""
    if not gap_text:
        return "general"
    for cat, pat in CLASS_PATTERNS:
        if pat.search(gap_text):
            return cat
    # Fall back via the original gap-type tag from the corpus
    if default_type in ("future_work", "more_needed"):
        return "future_work"
    if default_type in ("scarcity", "not_investigated"):
        return "domain"
    return "general"


# ─── Trend analysis ───────────────────────────────────────────────────────


def compute_trends(papers: list[dict[str, Any]]) -> dict[str, Any]:
    """Year-wise paper counts + simple slope-based interpretation.

    `papers` is the supporting-paper list from the gap analyzer; each has a `year`.
    """
    counts: Counter[int] = Counter()
    for p in papers:
        try:
            y = int(p.get("year"))
        except (TypeError, ValueError):
            continue
        if 2000 <= y <= datetime.now().year + 1:
            counts[y] += 1

    if not counts:
        return {"by_year": [], "interpretation": "Not enough year data to compute a trend."}

    years = sorted(counts.keys())
    series = [{"year": y, "count": counts[y]} for y in years]

    # Slope over the last 5 years (or fewer)
    recent_years = years[-5:]
    if len(recent_years) >= 3:
        ys = np.array([counts[y] for y in recent_years], dtype="float32")
        xs = np.arange(len(ys), dtype="float32")
        slope = float(np.polyfit(xs, ys, 1)[0])
        avg = float(ys.mean())
        normalized = slope / max(avg, 1.0)
        if normalized > 0.15:
            interp = (
                f"Research on this topic has been **rising** in recent years "
                f"(+{normalized * 100:.0f}% per year through {recent_years[-1]}). "
                "The area is actively growing — consider building on the latest contributions."
            )
        elif normalized < -0.15:
            interp = (
                f"Research has been **declining** since {recent_years[0]} "
                f"({normalized * 100:.0f}% per year). "
                "This may indicate a saturated area — or an unfinished one worth revisiting."
            )
        else:
            interp = (
                f"Activity is **stable** across {recent_years[0]}–{recent_years[-1]}. "
                "A steady stream of work suggests room for incremental contributions."
            )
    else:
        interp = "Too few data points for a robust trend interpretation."

    peak_year, peak_count = counts.most_common(1)[0]
    return {
        "by_year": series,
        "peak_year": peak_year,
        "peak_count": peak_count,
        "total_papers": sum(counts.values()),
        "interpretation": interp,
    }


# ─── Cross-domain opportunities ───────────────────────────────────────────


# Pre-defined high-level domain anchors. A pair (A, B) where the corpus has
# matches for A but very few that *also* match B is a cross-domain opportunity.
DOMAIN_ANCHORS = [
    ("AI / Machine Learning", re.compile(r"\b(machine learning|deep learning|neural|cnn|nlp|ai)\b", re.I)),
    ("Healthcare",            re.compile(r"\b(health|medical|clinical|patient|diagnos|disease|cancer)\b", re.I)),
    ("Agriculture",           re.compile(r"\b(crop|farm|agricultur|yield|plant|fertilizer)\b", re.I)),
    ("Education",             re.compile(r"\b(learning|student|teach|education|e-?learning|MOOC|classroom)\b", re.I)),
    ("Finance / Banking",     re.compile(r"\b(bank|finance|fraud|credit|loan|fintech|insurance)\b", re.I)),
    ("Tourism",               re.compile(r"\b(tour|tourism|hospitality|travel|hotel)\b", re.I)),
    ("IoT / Smart cities",    re.compile(r"\b(iot|sensor|smart\s+(city|home|grid)|edge)\b", re.I)),
    ("Cybersecurity",         re.compile(r"\b(security|cybersecur|attack|intrusion|malware|encryption)\b", re.I)),
    ("Sustainability",        re.compile(r"\b(sustain|climate|carbon|renewable|green|environment)\b", re.I)),
    ("Sri Lanka / Regional",  re.compile(r"\b(sri\s*lanka|colombo|sinhala|tamil)\b", re.I)),
]


def cross_domain_opportunities(
    records: list[dict[str, Any]], query: str, top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find under-explored A+B combinations.

    For the query's primary domain (whichever anchor matches the query best),
    count how many records *also* hit each other domain. Pairs with low
    counts are flagged as opportunities.
    """
    query_l = (query or "").lower()
    primary_domains = [name for name, pat in DOMAIN_ANCHORS if pat.search(query_l)]
    if not primary_domains:
        # Fall back: pick the most common matching domain across the records
        domain_hits: Counter[str] = Counter()
        for r in records:
            t = (r.get("title", "") + " " + r.get("description", "")).lower()
            for name, pat in DOMAIN_ANCHORS:
                if pat.search(t):
                    domain_hits[name] += 1
        if not domain_hits:
            return []
        primary_domains = [domain_hits.most_common(1)[0][0]]

    primary = primary_domains[0]

    # Count pair frequencies: |records that match primary AND each other domain|
    pair_counts: dict[str, int] = defaultdict(int)
    primary_total = 0
    for r in records:
        t = (r.get("title", "") + " " + r.get("description", "")).lower()
        if not any(pat.search(t) for name, pat in DOMAIN_ANCHORS if name == primary):
            continue
        primary_total += 1
        for name, pat in DOMAIN_ANCHORS:
            if name == primary:
                continue
            if pat.search(t):
                pair_counts[name] += 1

    # Opportunities = domains with very few co-occurrences relative to primary_total
    out = []
    for name, _ in DOMAIN_ANCHORS:
        if name == primary:
            continue
        n = pair_counts.get(name, 0)
        # Ratio: 0 means none, primary_total means perfect overlap
        ratio = n / max(primary_total, 1)
        if primary_total > 0 and ratio < 0.20:
            out.append({
                "domain_a": primary,
                "domain_b": name,
                "papers_in_intersection": n,
                "papers_in_primary": primary_total,
                "opportunity_score": round(1.0 - ratio, 3),
                "suggestion": (
                    f"Limited research combining **{primary}** and **{name}** in the SLIIT corpus "
                    f"({n} of {primary_total} papers cover both). A study connecting these areas "
                    "would address a clear gap."
                ),
            })

    out.sort(key=lambda d: d["opportunity_score"], reverse=True)
    return out[:top_k]


# ─── Clustering / over-researched zones ───────────────────────────────────


_STOPWORDS = {
    "the", "a", "an", "of", "in", "and", "for", "to", "with", "on", "by",
    "is", "are", "be", "this", "that", "from", "as", "at", "but", "or",
    "we", "our", "their", "its", "such", "have", "has", "been", "based",
    "using", "use", "used", "approach", "method", "study", "research", "paper",
    "results", "show", "shown", "data", "model", "novel", "proposed", "system",
    "systems",
}


def detect_saturation(records: list[dict[str, Any]], min_count: int = 4) -> list[dict[str, Any]]:
    """Find subtopics with high frequency among the matched papers.

    Returns terms ranked by occurrence — anything appearing in >= `min_count`
    papers is flagged as a 'saturated' / over-researched zone.
    """
    term_counts: Counter[str] = Counter()
    for r in records:
        text = (r.get("topic", "") + " " + r.get("title", "")).lower()
        # Pull out 2+ word phrases that aren't all stopwords
        for m in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text):
            if m.lower() in _STOPWORDS or len(m) < 4:
                continue
            term_counts[m.lower()] += 1
    out = []
    for term, count in term_counts.most_common(15):
        if count >= min_count:
            out.append({
                "term": term,
                "paper_count": count,
                "warning": (
                    f"'{term}' appears in {count} of the matched papers — this subtopic is "
                    "well-explored. Consider differentiating your contribution."
                ),
            })
    return out[:8]


# ─── Smart recommendations ────────────────────────────────────────────────


def recommend_directions(
    query: str, gaps: list[dict[str, Any]], cross_domain: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Synthesise 3-5 actionable research directions from gaps + cross-domain pairs."""
    out: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    # 1. From gap classification — one suggestion per category present
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for g in gaps:
        by_class[g.get("classification", "general")].append(g)

    for cat, items in by_class.items():
        if cat == "general" or not items:
            continue
        seed = items[0]
        title = _gap_to_title(query, cat, seed)
        if title in seen_titles:
            continue
        seen_titles.add(title)
        out.append({
            "title": title,
            "rationale": _gap_to_rationale(cat, seed),
            "problem_statement": _gap_to_problem(query, cat, seed),
            "based_on": "gap_class:" + cat,
            "supporting_paper": seed.get("supporting_paper"),
        })

    # 2. From cross-domain pairs — pick top 2
    for cd in cross_domain[:2]:
        title = f"Bridging {cd['domain_a']} and {cd['domain_b']} for {query.title()}"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        out.append({
            "title": title,
            "rationale": cd["suggestion"],
            "problem_statement": (
                f"Although {cd['domain_a']} has been studied in the SLIIT corpus, only "
                f"{cd['papers_in_intersection']} papers also engage with {cd['domain_b']}. "
                f"This study investigates how {cd['domain_a']} techniques can be applied to "
                f"{cd['domain_b']} challenges — specifically in the context of {query}."
            ),
            "based_on": "cross_domain",
            "supporting_paper": None,
        })

    return out[:5]


def _gap_to_title(query: str, cat: str, gap: dict[str, Any]) -> str:
    seed = (gap.get("topic") or query).strip()
    seed = re.sub(r"\s+", " ", seed)[:60]
    templates = {
        "future_work":  f"Extending {seed}: Addressing the future-work agenda from prior SLIIT studies",
        "methodology":  f"A novel methodology for {seed}",
        "dataset":      f"Building a SLIIT-context dataset for {seed}",
        "domain":       f"{seed.title()} in the Sri Lankan context",
        "performance":  f"Improving accuracy and performance in {seed}",
    }
    return templates.get(cat, f"Investigating {seed}")


def _gap_to_rationale(cat: str, gap: dict[str, Any]) -> str:
    rationales = {
        "future_work":  "Earlier SLIIT papers explicitly call out this direction as future work — picking it up gives an immediate, defensible motivation.",
        "methodology":  "Existing approaches were criticised in the source paper — proposing a new method addresses a stated weakness.",
        "dataset":      "Multiple SLIIT papers cite limited or non-local datasets as a constraint — building one is publishable in its own right.",
        "domain":       "The cited gap is specific to the Sri Lankan / regional context — global solutions may not transfer cleanly.",
        "performance":  "The supporting paper itself flags performance limitations — an improvement here is directly comparable.",
    }
    return rationales.get(cat, "Addresses an under-explored area in the SLIIT corpus.")


def _gap_to_problem(query: str, cat: str, gap: dict[str, Any]) -> str:
    src = gap.get("supporting_paper") or {}
    cite = ""
    if src.get("title"):
        authors = src.get("authors") or ["prior SLIIT research"]
        first_author = (authors[0] if isinstance(authors, list) and authors else "prior research")
        last = first_author.split(",")[0] if "," in str(first_author) else str(first_author)
        cite = f" {last} et al. ({src.get('year', 'n/a')}) noted that "
    snippet = (gap.get("description") or "").strip()
    if len(snippet) > 240:
        snippet = snippet[:237].rsplit(" ", 1)[0] + "…"
    return (
        f"This research investigates {query}. {cite}{snippet} Building on this observation, the "
        f"study proposes to address the {CATEGORY_LABELS.get(cat, 'identified')} highlighted in prior work."
    )


# ─── Multi-dimensional scoring ────────────────────────────────────────────


def multi_dim_score(gap: dict[str, Any]) -> float:
    """Combine similarity / gap-type / recency / novelty into a 0..1 ranking score."""
    sim = float(gap.get("similarity", 0.0))
    type_w = TYPE_WEIGHTS.get(gap.get("gap_type", "limitation"), 1.0)
    recency = float(gap.get("recency_score", 0.5))
    novelty = float(gap.get("novelty_score", 0.5))
    score = 0.45 * sim * type_w + 0.20 * (1 - recency) + 0.20 * novelty + 0.15 * sim
    return round(min(1.0, score), 3)


def explain(gap: dict[str, Any]) -> str:
    """Concise per-gap explanation paragraph suitable for tooltips / cards."""
    p = gap.get("supporting_paper") or {}
    cls = gap.get("classification") or "general"
    label = CATEGORY_LABELS.get(cls, "Gap")
    sim_pct = int(round(float(gap.get("similarity", 0)) * 100))
    nov_pct = int(round(float(gap.get("novelty_score", 0)) * 100))
    rec_pct = int(round(float(gap.get("recency_score", 0)) * 100))
    src = (p.get("title") or "an SLIIT paper")
    yr = p.get("year") or "n/a"
    return (
        f"{label}. Topical similarity to your query is {sim_pct}% (novelty {nov_pct}%, "
        f"staleness {rec_pct}%). The gap was extracted from \"{src}\" ({yr}) — the source "
        "paper itself flagged this as an unresolved or future-work item, which is why we "
        "surface it here."
    )


# ─── Main entry point ─────────────────────────────────────────────────────


def analyze(
    query: str,
    top_k: int = 8,
    min_similarity: float = 0.25,
    year_from: int | None = None,
    year_to: int | None = None,
    expand_papers: bool = True,
) -> dict[str, Any]:
    """Run the existing analyzer + apply the intelligence layer."""
    from app.services import gap_analyzer

    base = gap_analyzer.analyze(query, top_k=max(top_k, 12), min_similarity=min_similarity)
    if not base.get("loaded"):
        return {"loaded": False, "gaps": [], "trends": None, "cross_domain": [],
                "recommendations": [], "saturation": [], "filters": {"year_from": year_from, "year_to": year_to}}

    raw_gaps: list[dict[str, Any]] = base.get("gaps", [])

    # Optional year filter on supporting papers
    def _in_range(year: Any) -> bool:
        try:
            y = int(year)
        except (TypeError, ValueError):
            return year_from is None and year_to is None
        if year_from is not None and y < year_from:
            return False
        if year_to is not None and y > year_to:
            return False
        return True

    filtered: list[dict[str, Any]] = []
    for g in raw_gaps:
        sup = g.get("supporting_paper") or {}
        if not _in_range(sup.get("year")):
            continue
        g["classification"] = classify(g.get("description", ""), g.get("gap_type", ""))
        g["category_label"] = CATEGORY_LABELS.get(g["classification"], "Gap")
        g["multi_dim_score"] = multi_dim_score(g)
        g["explanation"] = explain(g)
        filtered.append(g)

    filtered.sort(key=lambda x: x["multi_dim_score"], reverse=True)
    top_gaps = filtered[:top_k]

    supporting = [g.get("supporting_paper", {}) for g in filtered]

    trends = compute_trends(supporting)
    saturation = detect_saturation(filtered)
    cross = cross_domain_opportunities(filtered, query=query)
    recs = recommend_directions(query, top_gaps, cross)

    # Class distribution for the donut chart
    class_dist: Counter[str] = Counter(g["classification"] for g in top_gaps)

    return {
        "loaded": True,
        "query": query,
        "filters": {"year_from": year_from, "year_to": year_to},
        "gaps": top_gaps,
        "all_gaps_after_filter": len(filtered),
        "total_papers_analyzed": base.get("total_papers_analyzed", 0),
        "total_corpus_size": base.get("total_corpus_size", 0),
        "model_version": base.get("model_version", "unknown"),
        "base_model": base.get("base_model", "unknown"),
        "classification_distribution": [
            {"category": k, "label": CATEGORY_LABELS.get(k, k.title()), "count": v}
            for k, v in class_dist.most_common()
        ],
        "trends": trends,
        "saturation": saturation,
        "cross_domain": cross,
        "recommendations": recs,
        "expanded_papers": expand_papers,
    }


# ─── HTML report generator ────────────────────────────────────────────────


def generate_report_html(payload: dict[str, Any]) -> str:
    """Render the analysis as a self-contained HTML page suitable for download.

    Users can open the .html in their browser, then File → Print → Save as PDF
    to get a PDF without needing a server-side PDF library.
    """
    q = payload.get("query") or "(unspecified)"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def esc(s: Any) -> str:
        return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    gaps_html = ""
    for i, g in enumerate(payload.get("gaps", []), start=1):
        sp = g.get("supporting_paper") or {}
        gaps_html += f"""
        <div class="gap">
          <div class="gap-head">
            <span class="rank">#{i}</span>
            <span class="cat cat-{esc(g.get('classification','general'))}">{esc(g.get('category_label',''))}</span>
            <span class="score">Score: {(g.get('multi_dim_score', 0) * 100):.0f}%</span>
          </div>
          <p class="desc">{esc(g.get('description',''))}</p>
          <p class="explanation">{esc(g.get('explanation',''))}</p>
          {f'<p class="source">Source: <em>{esc(sp.get("title",""))}</em> ({esc(sp.get("year","n/a"))})</p>' if sp.get('title') else ''}
        </div>
        """

    cross_html = "".join(
        f'<li><strong>{esc(c["domain_a"])} × {esc(c["domain_b"])}</strong> — '
        f'{c["papers_in_intersection"]}/{c["papers_in_primary"]} papers cover both '
        f'(opportunity score {c["opportunity_score"]:.2f})</li>'
        for c in payload.get("cross_domain", [])
    )

    rec_html = ""
    for r in payload.get("recommendations", []):
        rec_html += f"""
        <div class="rec">
          <h3>{esc(r.get('title',''))}</h3>
          <p class="rationale">{esc(r.get('rationale',''))}</p>
          <p>{esc(r.get('problem_statement',''))}</p>
        </div>
        """

    trends = payload.get("trends") or {}
    trend_rows = "".join(
        f"<tr><td>{esc(b['year'])}</td><td>{esc(b['count'])}</td></tr>"
        for b in trends.get("by_year", [])
    )

    sat_html = "".join(
        f"<li><code>{esc(s['term'])}</code> — appears in {s['paper_count']} matched papers</li>"
        for s in payload.get("saturation", [])
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Research Gap Report — {esc(q)}</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 880px; margin: 2rem auto; padding: 0 1.5rem; color: #1f2937; line-height: 1.55; }}
  h1, h2, h3 {{ color: #312e81; }}
  h1 {{ border-bottom: 3px solid #6366f1; padding-bottom: .5rem; }}
  h2 {{ margin-top: 2rem; border-bottom: 1px solid #c7d2fe; padding-bottom: .25rem; }}
  .meta {{ color: #4b5563; font-size: .9rem; margin-bottom: 2rem; }}
  .gap, .rec {{ border: 1px solid #e5e7eb; border-radius: 6px; padding: .75rem 1rem; margin: .75rem 0; background: #f9fafb; }}
  .gap-head {{ display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; margin-bottom: .5rem; }}
  .rank {{ font-weight: bold; color: #6366f1; }}
  .cat {{ display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .75rem; }}
  .cat-future_work {{ background: #ede9fe; color: #5b21b6; }}
  .cat-methodology {{ background: #dbeafe; color: #1e40af; }}
  .cat-dataset     {{ background: #fef3c7; color: #92400e; }}
  .cat-domain      {{ background: #dcfce7; color: #166534; }}
  .cat-performance {{ background: #fee2e2; color: #991b1b; }}
  .cat-general     {{ background: #f3f4f6; color: #374151; }}
  .score {{ margin-left: auto; font-size: .8rem; color: #6b7280; }}
  .desc {{ font-style: italic; }}
  .explanation {{ font-size: .85rem; color: #4b5563; margin-top: .5rem; }}
  .source {{ font-size: .8rem; color: #6b7280; margin-top: .35rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ padding: .35rem .5rem; border-bottom: 1px solid #e5e7eb; text-align: left; }}
  ul {{ padding-left: 1.25rem; }}
</style>
</head>
<body>
  <h1>Research Gap Report</h1>
  <p class="meta">
    Query: <strong>{esc(q)}</strong>
    {f' · {esc(payload["filters"]["year_from"])}–{esc(payload["filters"]["year_to"])}' if payload.get("filters", {}).get("year_from") or payload.get("filters", {}).get("year_to") else ''}
    · Generated {now}
    · Corpus: {esc(payload.get("total_corpus_size", 0))} gaps from SLIIT papers
  </p>

  <h2>Summary</h2>
  <p>
    The system identified <strong>{len(payload.get("gaps", []))}</strong> ranked research gaps,
    {len(payload.get("cross_domain", []))} cross-domain opportunities, and produced
    {len(payload.get("recommendations", []))} suggested research directions.
  </p>

  <h2>1 · Top Research Gaps</h2>
  {gaps_html or '<p>No gaps matched.</p>'}

  <h2>2 · Trend Analysis</h2>
  <p>{esc(trends.get("interpretation","No trend data."))}</p>
  {f'<table><thead><tr><th>Year</th><th>Papers</th></tr></thead><tbody>{trend_rows}</tbody></table>' if trend_rows else ''}

  <h2>3 · Cross-Domain Opportunities</h2>
  <ul>{cross_html or '<li>No notable cross-domain opportunities.</li>'}</ul>

  <h2>4 · Recommended Research Directions</h2>
  {rec_html or '<p>No recommendations generated.</p>'}

  <h2>5 · Saturated Subtopics (avoid duplicating)</h2>
  <ul>{sat_html or '<li>No subtopic appears overly saturated.</li>'}</ul>

  <hr style="margin-top:3rem"/>
  <p style="font-size:.75rem;color:#9ca3af;">
    Generated by Researchly AI · model: {esc(payload.get("base_model","unknown"))}
  </p>
</body>
</html>"""
