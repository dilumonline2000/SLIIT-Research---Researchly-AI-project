"""Plagiarism trend analyzer — local model service.

Two operations:

1. **search_trends(query, top_k)** — given a topic / category in free text,
   find the most similar SLIIT topic-buckets and return their precomputed
   plagiarism trend rows (yearly avg/max/p95 similarity, flagged pairs, etc.).

2. **compare_papers(text_a, text_b)** — for two arbitrary paper texts,
   compute:
     - SBERT cosine similarity over the full text
     - n-gram overlap (4-grams, Jaccard)
     - top-K most similar sentence pairs (with their indices)
     - aggregate plagiarism risk level

Both are deterministic and CPU-only.

Public API:
    is_loaded() -> bool
    load() -> bool
    search_trends(query: str, top_k: int = 5) -> dict
    compare_papers(text_a: str, text_b: str, top_pairs: int = 5) -> dict
    get_model_info() -> dict
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

SERVICE_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SERVICE_ROOT.parent.parent

INDEX_PATH = SERVICE_ROOT / "models" / "trained_plagiarism_analyzer" / "trend_index.pkl"
MODULE1_SBERT = PROJECT_ROOT / "services" / "module1-integrity" / "models" / "sbert_plagiarism"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_INDEX: Optional[dict[str, Any]] = None
_MODEL = None
_MODEL_NAME: str = "unknown"

# Risk thresholds (cosine similarity)
RISK_LOW = 0.30
RISK_MED = 0.60
RISK_HIGH = 0.80


def is_loaded() -> bool:
    return _MODEL is not None


def _load_sbert() -> bool:
    global _MODEL, _MODEL_NAME
    if _MODEL is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
        if MODULE1_SBERT.exists() and any(MODULE1_SBERT.iterdir()):
            _MODEL = SentenceTransformer(str(MODULE1_SBERT))
            _MODEL_NAME = "sbert_plagiarism (SLIIT fine-tuned)"
        else:
            _MODEL = SentenceTransformer(FALLBACK_MODEL)
            _MODEL_NAME = FALLBACK_MODEL
        return True
    except Exception as e:
        logger.error("[PlagiarismAnalyzer] failed to load SBERT: %s", e)
        return False


def load() -> bool:
    """Load the trend index AND the SBERT model. Either alone is OK for some
    operations: search_trends needs both, compare_papers needs only SBERT."""
    global _INDEX
    sbert_ok = _load_sbert()
    if _INDEX is None and INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "rb") as f:
                _INDEX = pickle.load(f)
            logger.info(
                "[PlagiarismAnalyzer] loaded index v%s — %d topics",
                _INDEX.get("version"), len(_INDEX["topics"]),
            )
        except Exception as e:
            logger.error("[PlagiarismAnalyzer] failed to load index: %s", e)
    return sbert_ok


# ─────────────────────────────────────────────────────────────────────────────
# Trend search
# ─────────────────────────────────────────────────────────────────────────────


def search_trends(
    query: str, top_k: int = 5, min_topic_similarity: float = 0.25,
    include_related_papers: bool = True, related_papers_top_k: int = 6,
) -> dict[str, Any]:
    """Find trend buckets close to `query` AND surface real SLIIT papers
    matching the query (so the user always gets relevant evidence even when
    no precomputed bucket is a close match)."""
    if not load():
        return {"loaded": False, "matches": [], "related_papers": []}
    if _INDEX is None:
        return {"loaded": False, "error": "trend index missing", "matches": [], "related_papers": []}
    assert _MODEL is not None

    qvec = _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")[0]
    sims = _INDEX["embeddings"] @ qvec
    order = np.argsort(-sims)
    # Filter by similarity threshold so unrelated buckets don't pollute results.
    kept = [int(i) for i in order if float(sims[int(i)]) >= min_topic_similarity][:top_k]

    matches = []
    for idx in kept:
        meta = _INDEX["topic_meta"][idx]
        matches.append({
            "topic": meta["topic"],
            "similarity": round(float(sims[idx]), 4),
            "n_records": meta["n_records"],
            "n_papers_total": meta["n_papers_total"],
            "avg_similarity_overall": meta["avg_similarity_overall"],
            "max_avg_similarity": meta["max_avg_similarity"],
            "n_high_similarity_pairs_total": meta["n_high_similarity_pairs_total"],
            "latest_year": meta["latest_year"],
            "latest_trend_direction": meta["latest_trend_direction"],
            "yearly": meta["yearly"],
        })

    related_papers: list[dict[str, Any]] = []
    if include_related_papers:
        try:
            from app.services import paper_index
            related_papers = paper_index.find_related(
                query, top_k=related_papers_top_k, min_similarity=0.18,
            )
        except Exception as e:
            logger.info("[PlagiarismAnalyzer] related-paper lookup failed: %s", e)

    return {
        "loaded": True,
        "matches": matches,
        "related_papers": related_papers,
        "total_topics": len(_INDEX["topics"]),
        "model_version": _INDEX.get("version", "unknown"),
        "base_model": _INDEX.get("base_model", "unknown"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pair comparison
# ─────────────────────────────────────────────────────────────────────────────


def _ngrams(text: str, n: int = 4) -> set[str]:
    text = re.sub(r"\s+", " ", (text or "").lower()).strip()
    tokens = re.findall(r"[a-z0-9]+", text)
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)} if len(tokens) >= n else set()


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\(])", text)
    return [p.strip() for p in parts if 20 <= len(p) <= 600][:300]


def _risk_level(sim: float) -> str:
    if sim >= RISK_HIGH:
        return "high"
    if sim >= RISK_MED:
        return "medium"
    if sim >= RISK_LOW:
        return "low"
    return "minimal"


def compare_papers(text_a: str, text_b: str, top_pairs: int = 5) -> dict[str, Any]:
    """Pairwise plagiarism analysis of two paper texts."""
    if not _load_sbert():
        return {"loaded": False}
    assert _MODEL is not None

    text_a = (text_a or "").strip()
    text_b = (text_b or "").strip()
    if not text_a or not text_b:
        return {"loaded": True, "error": "Both texts must be non-empty"}

    # Document-level cosine via centroid embedding
    emb_a, emb_b = _MODEL.encode(
        [text_a, text_b],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    doc_sim = float(np.dot(emb_a, emb_b))

    # 4-gram overlap
    a_ng = _ngrams(text_a, 4)
    b_ng = _ngrams(text_b, 4)
    if a_ng and b_ng:
        inter = len(a_ng & b_ng)
        union = len(a_ng | b_ng)
        ngram_jaccard = inter / max(1, union)
        ngram_overlap_a = inter / max(1, len(a_ng))
        ngram_overlap_b = inter / max(1, len(b_ng))
    else:
        ngram_jaccard = 0.0
        ngram_overlap_a = 0.0
        ngram_overlap_b = 0.0

    # Sentence-level similarity matrix → top pairs
    sents_a = _split_sentences(text_a)
    sents_b = _split_sentences(text_b)
    flagged_pairs: list[dict[str, Any]] = []
    if sents_a and sents_b:
        sa = _MODEL.encode(sents_a, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        sb = _MODEL.encode(sents_b, batch_size=32, convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        M = sa @ sb.T
        # Find top_pairs sentence-pair similarities
        flat = M.ravel()
        # Get indices of top values, then map back
        if flat.size:
            cnt = min(top_pairs, flat.size)
            idx = np.argpartition(-flat, cnt - 1)[:cnt]
            idx = idx[np.argsort(-flat[idx])]
            for k in idx:
                i, j = int(k // M.shape[1]), int(k % M.shape[1])
                sim_val = float(M[i, j])
                if sim_val < 0.5:
                    break
                flagged_pairs.append({
                    "similarity": round(sim_val, 4),
                    "sentence_a": sents_a[i],
                    "sentence_b": sents_b[j],
                    "index_a": i,
                    "index_b": j,
                })

    # Aggregate risk score: SBERT similarity catches paraphrasing (the more
    # common form of academic plagiarism), so weight it more heavily than
    # exact n-gram overlap. n-grams remain useful as a copy-paste tripwire.
    risk_score = round(0.75 * doc_sim + 0.25 * ngram_jaccard, 4)
    risk_level = _risk_level(risk_score)

    return {
        "loaded": True,
        "document_similarity": round(doc_sim, 4),
        "ngram_jaccard": round(ngram_jaccard, 4),
        "ngram_overlap_in_a": round(ngram_overlap_a, 4),
        "ngram_overlap_in_b": round(ngram_overlap_b, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flagged_pairs": flagged_pairs,
        "n_sentences_a": len(sents_a),
        "n_sentences_b": len(sents_b),
        "model_version": _MODEL_NAME,
    }


def get_model_info() -> dict[str, Any]:
    info = {
        "sbert_loaded": _load_sbert(),
        "sbert_version": _MODEL_NAME if _MODEL is not None else None,
        "trend_index_loaded": False,
    }
    if INDEX_PATH.exists():
        # ensure INDEX is loaded
        load()
    if _INDEX is not None:
        info["trend_index_loaded"] = True
        info["n_topics"] = len(_INDEX["topics"])
        info["index_version"] = _INDEX.get("version")
    return info


# ─── HTML report renderers ────────────────────────────────────────────────


def _esc(s: Any) -> str:
    return (str(s) if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_REPORT_BASE_CSS = """
  body { font-family: Georgia, 'Times New Roman', serif; max-width: 880px; margin: 2rem auto; padding: 0 1.5rem; color: #1f2937; line-height: 1.55; }
  h1, h2, h3 { color: #312e81; }
  h1 { border-bottom: 3px solid #6366f1; padding-bottom: .5rem; }
  h2 { margin-top: 2rem; border-bottom: 1px solid #c7d2fe; padding-bottom: .25rem; }
  .meta { color: #4b5563; font-size: .9rem; margin-bottom: 2rem; }
  .block { border: 1px solid #e5e7eb; border-radius: 6px; padding: .75rem 1rem; margin: .75rem 0; background: #f9fafb; }
  .pair { background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: .6rem .9rem; margin: .5rem 0; }
  .badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: .75rem; }
  .badge-high   { background: #fee2e2; color: #991b1b; }
  .badge-medium { background: #fef3c7; color: #92400e; }
  .badge-low    { background: #fef9c3; color: #854d0e; }
  .badge-minimal{ background: #d1fae5; color: #047857; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
  .num { font-size: 1.4rem; font-weight: bold; }
  .label { font-size: .7rem; text-transform: uppercase; color: #6b7280; }
  table { border-collapse: collapse; width: 100%; margin-top: .5rem; }
  th, td { padding: .35rem .5rem; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: .85rem; }
  ul { padding-left: 1.25rem; }
  a { color: #4f46e5; }
"""


def generate_search_report_html(payload: dict[str, Any]) -> str:
    """Render a topic-search result (trends + related papers) as a full HTML page."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    query = _esc(payload.get("query") or "(unspecified)")

    # Topic-bucket matches
    matches_html = ""
    for m in payload.get("matches", []):
        yearly_rows = "".join(
            f"<tr><td>{_esc(y['year'])}</td><td>{_esc(y['n_papers'])}</td>"
            f"<td>{(y['avg_similarity'] * 100):.1f}%</td>"
            f"<td>{(y['max_similarity'] * 100):.1f}%</td>"
            f"<td>{_esc(y['trend_direction'])}</td></tr>"
            for y in m.get("yearly", [])
        )
        pairs_html = ""
        for y in m.get("yearly", []):
            for p in (y.get("top_pairs") or [])[:2]:
                pairs_html += (
                    f"<div class='pair'><strong>{(p['similarity']*100):.1f}%</strong> · {_esc(y['year'])}<br/>"
                    f"<em>A:</em> {_esc(p['paper_a']['title'])}<br/>"
                    f"<em>B:</em> {_esc(p['paper_b']['title'])}</div>"
                )
        matches_html += f"""
        <div class="block">
          <h3>{_esc(m['topic']).title()}
            <span class="badge badge-low">{(m['similarity']*100):.0f}% match</span>
          </h3>
          <p class="meta">
            {m['n_papers_total']} papers · peak avg sim {(m['max_avg_similarity']*100):.1f}% ·
            latest direction: {_esc(m['latest_trend_direction'])}
          </p>
          <table>
            <thead><tr><th>Year</th><th>Papers</th><th>Avg sim</th><th>Max sim</th><th>Trend</th></tr></thead>
            <tbody>{yearly_rows}</tbody>
          </table>
          {f'<h4 style="margin-top:.75rem">Most-similar pairs</h4>{pairs_html}' if pairs_html else ''}
        </div>
        """

    # Related papers
    related_html = ""
    for r in payload.get("related_papers", []):
        link = f' · <a href="{_esc(r["url"])}" target="_blank">SLIIT RDA</a>' if r.get("url") else ""
        related_html += (
            f"<li><strong>{_esc(r['title'])}</strong>"
            f" · <em>{(r.get('similarity', 0) * 100):.0f}% match</em>"
            f"{link}<br/>"
            f"<span style='font-size:.85rem;color:#4b5563'>"
            f"{_esc(', '.join((r.get('authors') or [])[:3]))}"
            f"{(' · ' + _esc(r.get('year'))) if r.get('year') else ''}</span></li>"
        )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<title>Plagiarism Trend Report — {query}</title>
<style>{_REPORT_BASE_CSS}</style></head><body>
  <h1>Plagiarism Trend Report</h1>
  <p class="meta">Query: <strong>{query}</strong> · Generated {now}</p>

  <h2>1 · Matched topic buckets ({len(payload.get('matches', []))})</h2>
  {matches_html or '<p>No topic buckets passed the similarity threshold.</p>'}

  <h2>2 · Related SLIIT papers</h2>
  <ul>{related_html or '<li>None matched at this similarity threshold.</li>'}</ul>

  <hr style="margin-top:3rem"/>
  <p style="font-size:.75rem;color:#9ca3af;">Researchly AI · Module 3 (Data Management)</p>
</body></html>"""


def generate_compare_report_html(result: dict[str, Any], title_a: str = "Paper A", title_b: str = "Paper B") -> str:
    """Render a two-paper comparison result as a full HTML page."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    risk = _esc(result.get("risk_level", "minimal"))

    pairs_html = ""
    for i, p in enumerate(result.get("flagged_pairs", []), start=1):
        sim = p.get("similarity", 0)
        tone = "badge-high" if sim >= 0.85 else "badge-medium" if sim >= 0.7 else "badge-low"
        pairs_html += f"""
        <div class="pair">
          <span class="badge {tone}">{(sim*100):.1f}% similar</span>
          <span style="margin-left:.5rem;font-size:.75rem;color:#6b7280">A#{p['index_a']+1} ↔ B#{p['index_b']+1}</span>
          <p style="margin:.4rem 0 .15rem;font-size:.8rem;color:#4b5563">A:</p>
          <p style="margin:0">{_esc(p['sentence_a'])}</p>
          <p style="margin:.4rem 0 .15rem;font-size:.8rem;color:#4b5563">B:</p>
          <p style="margin:0">{_esc(p['sentence_b'])}</p>
        </div>
        """

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<title>Plagiarism Comparison Report</title>
<style>{_REPORT_BASE_CSS}</style></head><body>
  <h1>Plagiarism Comparison Report</h1>
  <p class="meta">Generated {now} · {_esc(title_a)} ↔ {_esc(title_b)}</p>

  <h2>Risk: <span class="badge badge-{risk}">{risk.upper()}</span>
       <span class="meta" style="margin-left:.5rem">
         Score {(result.get('risk_score', 0)*100):.0f}%
       </span></h2>

  <div class="grid-2">
    <div class="block"><div class="label">Document similarity (SBERT)</div><div class="num">{(result.get('document_similarity', 0)*100):.1f}%</div></div>
    <div class="block"><div class="label">N-gram Jaccard (4-grams)</div><div class="num">{(result.get('ngram_jaccard', 0)*100):.1f}%</div></div>
    <div class="block"><div class="label">Overlap in A</div><div class="num">{(result.get('ngram_overlap_in_a', 0)*100):.1f}%</div></div>
    <div class="block"><div class="label">Overlap in B</div><div class="num">{(result.get('ngram_overlap_in_b', 0)*100):.1f}%</div></div>
  </div>

  <h2>Most similar sentence pairs ({len(result.get('flagged_pairs', []))})</h2>
  {pairs_html or '<p>No flagged pairs above the similarity threshold.</p>'}

  <hr style="margin-top:3rem"/>
  <p style="font-size:.75rem;color:#9ca3af;">
    Researchly AI · Module 3 (Data Management) · {_esc(result.get('model_version', 'unknown'))}
  </p>
</body></html>"""
