# -*- coding: utf-8 -*-
from _build_excel import build_workbook

ROWS = [
    dict(id="M4-01", feature="Trend Forecast (all topics)", endpoint="GET /analytics/trends",
         input="horizon=3 (default, all 7 topics)",
         criteria="growth_pct and trend_direction should be plausible; forecast should reflect genuine historical "
                  "trajectory, not an artifact of the calculation.",
         actual="ALL 7 topics report trend_direction=\"rising\" with implausible growth_pct: general +144%, "
               "business +397%, social_sciences +1040%, computing +1412%, health +238%, engineering +347%, "
               "sciences +80%.",
         result="FAIL", severity="High",
         notes="Root cause identified: `growth_pct = (forecast_end − latest_historical) / latest_historical × 100` "
               "uses the single MOST RECENT year's raw count as its denominator. Every topic's most recent year "
               "(2026) is the CURRENT, INCOMPLETE year — e.g. \"computing\" drops from 144 papers in 2025 to just "
               "4 in 2026 (a partial-year artifact, not a real collapse), so dividing a normal forecast "
               "(~60/year) by that artificially tiny base produces (60.5−4)/4×100 = 1412%, matching the observed "
               "value exactly. This single root cause explains all 7 anomalous results uniformly and would "
               "affect the module's headline metric every time it runs during the current (incomplete) year. "
               "trend_direction itself (computed from a 3-year rolling average, not the single last point) is "
               "more defensible and likely still broadly correct. Also note: NRMSE (RMSE ÷ series mean) is 0.69-"
               "1.23 across topics — i.e. the ARIMA(1,1,1) fixed-order fit's error is comparable to or EXCEEDS "
               "the series' own mean for computing (1.045) and health (1.227), a poor fit by the model's own "
               "reported accuracy metric.")
    ,
    dict(id="M4-02", feature="Trend Forecast (single topic, longer horizon)", endpoint="GET /analytics/trends",
         input="topic=\"computing\", horizon=5",
         criteria="Same as M4-01.",
         actual="growth_pct=+1410-1412% again for \"computing\" — same artifact as M4-01, unaffected by the "
               "different horizon.",
         result="FAIL", severity="High",
         notes="Confirms the bug is independent of horizon length — it's purely a base-value artifact from the "
               "single latest data point, not a forecast-quality issue.")
    ,
    dict(id="M4-03", feature="Trend Compare (multi-topic ranking)", endpoint="POST /analytics/trends/compare",
         input="topics=[computing, health, business], horizon=3",
         criteria="The growth-based ranking of topics should be meaningful and comparable.",
         actual="Ranking: computing (+1412%) > business (+397%) > health (+238%) — inherits the same inflated "
               "growth_pct values from M4-01, so the \"fastest growing\" ranking itself is built on the same "
               "flawed metric.",
         result="FAIL", severity="High",
         notes="Same root cause as M4-01/M4-02. Because every topic's baseline is equally distorted by the "
               "partial 2026 data point, the RELATIVE ranking might still roughly track real growth differences "
               "(all values are inflated by a similar mechanism), but the displayed percentages themselves are "
               "not meaningful or presentable to a user as-is.")
    ,
    dict(id="M4-04", feature="Trend Insights (emerging topics)", endpoint="GET /analytics/trends/insights",
         input="horizon=3, top_k=5",
         criteria="A topic's plain-language interpretation should match the sign/magnitude of its own computed "
                  "score (positive score → accelerating language; negative score → decelerating/declining "
                  "language).",
         actual="\"computing\" appears in the `emerging` list with score=-1.772 (NEGATIVE — recent_slope=0.1 vs. "
               "long_term_slope=3.8, i.e. genuinely decelerating sharply), yet its canned interpretation text "
               "reads: \"Computing has a recent slope of +0.1 papers/year vs a long-term +3.8/year — "
               "accelerating sharply.\"",
         result="FAIL", severity="Medium",
         notes="Two distinct bugs converge here: (1) the interpretation string in `emerging_topics()` is a fixed "
               "template that always says \"accelerating sharply\" regardless of whether `emergence` "
               "(recent_slope − long_term_slope) is actually positive or negative — directly contradicting the "
               "numbers in the same sentence. (2) The underlying recent_slope calculation includes the same "
               "partial-2026 data point as M4-01, artificially dragging \"computing\"'s recent trajectory down "
               "and causing it to look like it's decelerating when a full year of 2026 data might show "
               "otherwise. Recommend both: fix the interpretation template to branch on the sign of `emergence`, "
               "and exclude/flag the current in-progress year from slope and growth calculations.")
    ,
    dict(id="M4-05", feature="Available Topics List", endpoint="GET /analytics/trends/topics",
         input="—",
         criteria="Should list the actual topics with fitted models.",
         actual="[\"general\", \"all\", \"business\", \"social_sciences\", \"computing\", \"health\", "
               "\"engineering\", \"sciences\"] — consistent across all forecast responses.",
         result="PASS", severity="",
         notes="Accurate, consistent metadata.")
    ,
    dict(id="M4-06", feature="Quality Score (strong technical abstract)", endpoint="POST /analytics/quality-score",
         input="Well-written abstract with inline [1] and (Author, Year) citations, explicit methodology "
               "(\"systematic experimental design\", \"transfer learning\", \"cross-validation\").",
         criteria="Should score highly and show clear differentiation across the 4 dimensions reflecting the "
                  "text's actual strengths.",
         actual="overall=0.828, originality=0.810, citation_impact=0.612, methodology=0.949, clarity=0.974 — "
               "well-differentiated, plausible scores that correctly reflect the strong methodology/clarity of "
               "this text.",
         result="PASS", severity="",
         notes="Good discrimination; the blended model+heuristic scoring (per-dimension weights documented in the "
               "module's own technical report) produces sensible, non-extreme results for a genuinely strong "
               "text.")
    ,
    dict(id="M4-07", feature="Quality Score (generic non-research text)", endpoint="POST /analytics/quality-score",
         input="An HR \"Leave Request Form\" — administrative boilerplate with no research content.",
         criteria="Overall score should be low; individual dimensions should reflect the text's genuine lack of "
                  "research characteristics.",
         actual="overall=0.236 (correctly low), originality=0.086, citation_impact=0.04, methodology=0.0018 (all "
               "correctly near-zero) — BUT clarity=1.0 (perfect score) despite this not being coherent academic "
               "writing at all. Topic classified as \"health\" (31% confidence) for a form with zero health "
               "content.",
         result="PARTIAL", severity="Low",
         notes="The overall score correctly ends up very low because originality/citation/methodology (75% "
               "combined weight) all correctly bottom out — the weighted-blend design successfully prevents one "
               "maxed sub-score from making a non-paper look good, which is a positive validation of that design "
               "choice. However, \"clarity\" as implemented is purely a word/sentence-length heuristic (short "
               "simple sentences = \"clear\"), so it cannot distinguish clear ACADEMIC writing from clear "
               "non-academic writing — worth documenting as a known scope limitation of that dimension rather "
               "than a functional bug. The spurious \"health\" topic classification for content-free text is a "
               "minor, expected symptom of forcing a top-1 label with no confidence floor (Module 4's own "
               "6-label classifier, separate from Module 3's 80-label one, shows the same low-signal-forces-a-"
               "guess pattern).")
    ,
    dict(id="M4-08", feature="Quality Score (missing input — edge case)", endpoint="POST /analytics/quality-score",
         input="Empty request body (no proposal_id, no title/abstract)",
         criteria="Should reject with a clear 400, not crash or silently return a default score.",
         actual="400 \"Provide either proposal_id or (title + abstract)\".",
         result="PASS", severity="",
         notes="Correct input validation.")
    ,
    dict(id="M4-09", feature="Success Prediction (strong abstract, 2 authors)", endpoint="POST /analytics/predict",
         input="Same strong abstract as M4-06, 2 authors, year=2026.",
         criteria="success_probability should follow the documented blend formula "
                  "(0.40·model + 0.60·heuristic) exactly when computed by hand from the returned raw features.",
         actual="success_probability=0.6319, prediction=\"successful\", risk_level=\"medium\". Hand-computed "
               "heuristic from returned features (abstract_length=690, methodology_count=3, citations=2, "
               "author_count=2, avg_word_len=6.26, avg_sent_len=14.43): heuristic ≈ 0.789. Solving "
               "0.40·model + 0.60·0.789 = 0.6319 gives model_proba ≈ 0.396 — a plausible, internally-consistent "
               "XGBoost output. Formula verified correct against real data.",
         result="PASS", severity="Low",
         notes="Blend formula independently verified by hand-calculation, not just trusted from the code — "
               "confirms the documented 40/60 blend is implemented exactly as specified. Minor UX inconsistency "
               "noted: risk_level=\"medium\" is paired with the single recommendation \"Strong paper across all "
               "dimensions — ready for submission\", which reads as mildly self-contradictory (if truly "
               "submission-ready, one would expect \"low\" risk).")
    ,
    dict(id="M4-10", feature="Success Prediction (weak/generic text)", endpoint="POST /analytics/predict",
         input="The same HR Leave Request Form text as M4-07.",
         criteria="Should score low with actionable recommendations.",
         actual="success_probability=0.1999, prediction=\"needs_improvement\", risk_level=\"high\", 4 relevant, "
               "well-targeted recommendations (methodology, citations, abstract length, collaboration).",
         result="PASS", severity="",
         notes="Correctly and clearly differentiates from the strong-abstract case (M4-09).")
    ,
    dict(id="M4-11", feature="Success Prediction (too-short abstract — edge case)", endpoint="POST /analytics/predict",
         input="abstract=\"Too short\" (9 characters)",
         criteria="Should reject with a clear 400, not attempt to score near-empty text.",
         actual="400 \"Abstract must be at least 50 characters\".",
         result="PASS", severity="",
         notes="Correct input validation.")
    ,
    dict(id="M4-12", feature="Concept Mind Map (topic-based)", endpoint="POST /analytics/mindmap",
         input="topic=\"machine learning for plant disease detection\", max_nodes=20",
         criteria="Should extract meaningful multi-word concept phrases (via KeyBERT) and expand them into a "
                  "richer, weighted concept graph via the trained GCN (up to max_nodes=20, with domain "
                  "clustering).",
         actual="Only 5 trivial single-word nodes returned: \"machine\", \"learning\", \"for\", \"plant\", "
               "\"disease\" — all uniformly weighted 0.5, domain_cluster=\"general\" for every node, 4 edges all "
               "connecting directly to node 0. \"for\" (a stopword/preposition) is included as a \"concept\".",
         result="FAIL", severity="High",
         notes="Root cause confirmed directly: server log shows \"ERROR:app.models.mindmap_gnn:torch-geometric "
               "not installed\", and a direct package check in this environment confirms BOTH required "
               "dependencies are missing — `pip show keybert` and `pip show torch_geometric` both report "
               "ModuleNotFoundError. This means: (1) KeyBERT's ImportError silently triggers the router's naive "
               "fallback (`req.topic.split()[:5]`), which is why a stopword like \"for\" leaked through as a "
               "\"concept\" — real KeyBERT would never do that; (2) the GCN model can never load "
               "(`HAS_PYG=False`), so the entire graph-expansion step — the actual \"GNN mind map\" the spec "
               "calls for — never runs, regardless of input. This is the single most severe, concretely-diagnosed "
               "finding across all four modules' validation: one of Module 4's four flagship ML models is "
               "completely non-functional in this environment due to two missing Python packages, not a logic "
               "bug. Fix: add `keybert` and `torch-geometric` (with a compatible PyTorch build) to "
               "requirements.txt / the service's Dockerfile.")
    ,
    dict(id="M4-13", feature="Concept Mind Map (department-based, no topic)", endpoint="POST /analytics/mindmap",
         input="department=\"Computer Science\", max_nodes=15, no topic given",
         criteria="Should build a department-level concept neighbourhood via the GCN.",
         actual="A single isolated node (\"Computer Science\") with zero edges — no expansion occurred at all.",
         result="FAIL", severity="High",
         notes="Same root cause as M4-12 (missing keybert/torch-geometric packages) — confirms the failure is "
               "systemic across both entry points into this feature, not input-specific.")
    ,
    dict(id="M4-14", feature="Cross-Module Dashboard KPIs", endpoint="GET /analytics/dashboard",
         input="—",
         criteria="Should aggregate real counts/averages from research_proposals, quality_scores, "
                  "success_predictions, supervisor_matches, and research_papers.keywords, and degrade gracefully "
                  "per-KPI if any one query fails.",
         actual="total_proposals=0, avg_quality_score=0.0, top_trending_topics=[], at_risk_projects=0, "
               "active_supervisors=0 — all correctly zero, matching the confirmed-empty state of every backing "
               "table in this environment (research_proposals, quality_scores, success_predictions, "
               "supervisor_matches all verified 0 rows).",
         result="BLOCKED", severity="N/A",
         notes="The per-KPI try/except degradation pattern is confirmed working correctly (no partial crash, "
               "consistent zeros), which is itself a useful PASS-level confirmation of the resilience design. "
               "However the actual AGGREGATION arithmetic (averages, counts, distinct-supervisor logic) cannot be "
               "validated for correctness until these tables contain real data in this environment — needs "
               "re-validation once populated.")
    ,
    dict(id="M4-15", feature="Service Health + trained-model metadata", endpoint="GET /health",
         input="—",
         criteria="Should report which trained models loaded and their own recorded training metrics.",
         actual="All 4 model bundles report loaded=true with real recorded metrics: quality_predictor R²=0.997-"
               "0.999 across all 5 targets; success_predictor accuracy=0.983, ROC-AUC=0.999.",
         result="PASS", severity="Low",
         notes="Endpoint itself is accurate and working. Worth flagging for the report/viva: these near-perfect "
               "R²/ROC-AUC figures should NOT be read as evidence of strong real-world generalisation — the "
               "codebase's own docstring in success_predictor.py explicitly states \"the trained XGBoost model is "
               "a near-perfect memorisation of the training heuristic\" it was fit on. The suspiciously "
               "textbook-perfect metrics are consistent with, and explained by, that documented limitation, not a "
               "new discovery from this validation — presenting these numbers without that context in a report "
               "or viva would overstate the model's genuine predictive power.")
]

ENV_NOTES = [
    "Trend Forecasting, Quality Scoring, and Success Prediction all use locally-shipped trained model bundles "
    "(models/trained_trend_forecaster, trained_quality_predictor, trained_success_predictor) and score "
    "caller-supplied text directly — none of these depend on the live Supabase corpus tables, so all were fully "
    "testable with genuine evidence, including hand-verification of the documented blend formulas against real "
    "returned feature values.",
    "The Cross-Module Dashboard depends entirely on Supabase tables (research_proposals, quality_scores, "
    "success_predictions, supervisor_matches — all confirmed 0 rows in this environment); its aggregation "
    "arithmetic could not be exercised against real data, though its graceful-degradation behaviour on empty "
    "data was confirmed correct.",
    "The Concept Mind Map feature's failure (M4-12, M4-13) is a DEPENDENCY/DEPLOYMENT issue, independently "
    "confirmed via `pip show keybert` and `pip show torch_geometric` in this environment's virtual environment — "
    "both report \"not installed\". This should be checked against whatever environment currently backs the "
    "deployed/demo instance of the app, since the same gap would produce the same silent degradation there.",
]

KEY_FINDINGS = [
    ("High", "Concept Mind Map (GCN-based) is completely non-functional — confirmed via server logs and direct "
     "package checks that both `keybert` and `torch-geometric` are missing from the environment, so the feature "
     "always falls to a crude single-word fallback regardless of input (M4-12, M4-13)."),
    ("High", "Trend Forecasting's headline growth_pct metric is systemically wrong for every topic (+80% to "
     "+1412%) because it divides by the current, incomplete year's raw paper count rather than a stable "
     "baseline — affects /trends, /trends/compare, and by extension anything built on top of them (M4-01, "
     "M4-02, M4-03)."),
    ("Medium", "Emerging-topics interpretation text is a fixed template that says \"accelerating sharply\" even "
     "for a topic with a negative (decelerating) score, directly contradicting the numbers in the same sentence "
     "(M4-04)."),
    ("Low", "\"Clarity\" quality dimension is a pure word/sentence-length heuristic and cannot distinguish "
     "genuinely clear academic writing from simply short, simple non-academic text — a documented scope "
     "limitation rather than a bug, since the overall score still correctly stays low via the other three "
     "dimensions (M4-07)."),
    ("Low", "Reported training metrics (R²≈0.997-0.999, ROC-AUC≈0.999) should be read alongside the codebase's "
     "own documented caveat that the model largely memorised its synthetic training heuristic (M4-15)."),
]

NARRATIVE = (
    "Quality Scoring and Success Prediction are both well-validated: their documented blend formulas were "
    "independently hand-verified against real returned feature data and found mathematically correct, both "
    "features correctly and clearly differentiate strong technical writing from generic non-research text, and "
    "both correctly reject invalid/too-short input with clear errors. Trend Forecasting is more concerning: every "
    "single topic in the corpus reports an implausible triple/quadruple-digit growth percentage, traced to a "
    "specific, fixable calculation bug (using the current incomplete year as the growth baseline) rather than a "
    "problem with the ARIMA models themselves — this needs to be fixed before the forecasting dashboard is shown "
    "to real users, since the headline percentage is currently the least trustworthy number the module produces. "
    "The most serious finding in this module, and across the whole validation exercise, is that the Concept Mind "
    "Map feature — one of the four \"flagship\" ML models named in the original project specification — is "
    "completely non-functional in this environment: two required Python packages are simply not installed, so "
    "every mind-map request silently degrades to a trivial fallback with no real graph structure at all, "
    "including a bare stopword leaking through as a \"concept\". This is a deployment/dependency gap rather than "
    "a logic error, and is straightforward to fix by adding the missing packages to the service's requirements — "
    "but it should be treated as the top-priority item from this entire validation pass, since it means the "
    "feature has likely never produced a genuine GNN-based result in this environment. The Cross-Module "
    "Dashboard's own logic checked out correctly on the (currently empty) data available, but needs re-testing "
    "once the corpus and downstream tables are populated."
)

if __name__ == "__main__":
    build_workbook(
        "Module4_Analytics_Validation_Report.xlsx",
        4, "Research Performance Analytics", "H. W. S. S. Jayasundara",
        "services/module4-analytics (FastAPI, port 8004)",
        ROWS, ENV_NOTES, KEY_FINDINGS, NARRATIVE,
    )
