# -*- coding: utf-8 -*-
from _build_excel import build_workbook

ROWS = [
    dict(id="M2-01", feature="Supervisor Matching (AI/ML proposal)", endpoint="POST /matching/supervisors",
         input="Proposal: CNN-based plant disease detection mobile app for farmers. top_k=5, min_similarity=0.1",
         criteria="Top matches should have Deep Learning / Computer Vision / Machine Learning research interests, "
                  "with descending similarity and coherent explanations.",
         actual="All 5 matches are Deep Learning/Computer Vision/Image Processing supervisors, similarity 0.740-"
               "0.766, explanations correctly name the overlapping interest area for each.",
         result="PASS", severity="",
         notes="Excellent precision — every top-5 result is a genuinely appropriate supervisor for this proposal.")
    ,
    dict(id="M2-02", feature="Supervisor Matching (cybersecurity proposal)", endpoint="POST /matching/supervisors",
         input="Proposal: ML-based network intrusion detection system. top_k=5, min_similarity=0.1",
         criteria="Top matches should have Cyber Security / Network Security research interests.",
         actual="All 5 matches are Cyber Security specialists (Computer Networks, Critical Infrastructure "
               "Security, Cyber Forensics, IoT Security), similarity 0.832-0.860 — the highest similarity band "
               "seen across all matching tests.",
         result="PASS", severity="",
         notes="Strongest-precision result of the three domain tests; cybersecurity appears to be a "
               "well-represented, cleanly-separated cluster in the supervisor embedding space.")
    ,
    dict(id="M2-03", feature="Supervisor Matching (legacy interests+abstract format)", endpoint="POST /matching/supervisors",
         input="Legacy request shape: research_interests=[\"NLP\",\"sentiment analysis\"], abstract about customer "
               "review sentiment analysis. top_k=5",
         criteria="Legacy input should be correctly converted to a proposal string internally and matched with "
                  "the same quality as the free-text path.",
         actual="All 5 matches are NLP/Computational Linguistics/GenAI supervisors, similarity 0.847-0.881 — "
               "confirms the legacy request format (`research_interests[] + abstract`) is converted correctly "
               "and matches with equal quality to the new free-text `proposal` field.",
         result="PASS", severity="",
         notes="Backwards-compatibility path works correctly, not just the new preferred format.")
    ,
    dict(id="M2-04", feature="Supervisor Matching (empty proposal — edge case)", endpoint="POST /matching/supervisors",
         input="proposal=\"\" (empty string), top_k=5, no research_interests/abstract given",
         criteria="Empty/invalid input should ideally return an empty result or a clear error, not a "
                  "confident-looking match list.",
         actual="Returned 5 supervisors with similarity 0.824-0.841 and explanations phrased as \"excellent "
               "match ... with closely related expertise\" — matched against the internal placeholder string "
               "\"general research\", not flagged as an invalid/empty input to the caller.",
         result="PARTIAL", severity="Low",
         notes="Code path: `req.proposal` is falsy so the code falls into the legacy branch, finds no "
               "interests/abstract either, and defaults `query_text = \"general research\"` — which is truthy, so "
               "the emptiness check (`if not query_text...`) never triggers and the request proceeds to a normal "
               "match. A student who submits the form with no proposal text would see a plausible-looking, "
               "confidently-worded supervisor list rather than a prompt to enter their research topic.")
    ,
    dict(id="M2-05", feature="Supervisor Profile (papers/charts/AI summary) — supervisor 1", endpoint="GET /matching/supervisors/1/papers",
         input="supervisor_id=1 (Koliya Pulasinghe)",
         criteria="Should return real Semantic Scholar publication data, an accurate year-distribution chart, and "
                  "(if generated) an AI research-focus summary that's actually grounded in the fetched titles.",
         actual="49 real papers returned (2003-2026) with correct DOIs/venues; year_distribution matches the raw "
               "paper list exactly. Gemini research_focus summary: \"...primarily researches AI-driven systems "
               "for autism intervention and therapy in Sinhala-speaking children, often utilizing speech "
               "recognition, synthesis, and child-robot interaction with NAO robots...\" — independently verified "
               "against the actual paper titles (many literally about Sinhala speech recognition, ASD/autism, NAO "
               "robots) and found to be accurate, not a generic/hallucinated summary.",
         result="PASS", severity="",
         notes="High-quality result across all three sub-components (live API integration, chart data, and "
               "grounded LLM summarisation). The rate-limit pacing logic (1 req/s serialised via asyncio.Lock) "
               "worked without any 429 errors during this test.")
    ,
    dict(id="M2-06", feature="Supervisor Profile (papers/charts/AI summary) — supervisor 2", endpoint="GET /matching/supervisors/2/papers",
         input="supervisor_id=2 (Samantha Thelijjagoda)",
         criteria="Same as M2-05.",
         actual="50 real papers returned correctly with accurate year distribution and topic list. "
               "research_focus=null — the AI summary was NOT generated for this supervisor.",
         result="PARTIAL", severity="Medium",
         notes="Server log confirms: \"WARNING:app.routers.supervisor:Gemini research-focus summary failed for "
               "'Samantha Thelijjagoda': Unterminated string starting at: line 4 column 5 (char 402)\" — a Gemini "
               "JSON-parsing failure, same class of issue as M1-15 and M2-12. The papers/charts portion of the "
               "feature is unaffected and correct; only the AI-summary sub-feature silently degrades to null with "
               "no user-facing indication that it was attempted and failed vs. simply unavailable.")
    ,
    dict(id="M2-07", feature="Supervisor Profile (invalid ID)", endpoint="GET /matching/supervisors/999999/papers",
         input="supervisor_id=999999 (does not exist)",
         criteria="Should return a clear 404, not a 500 or an empty-but-200 response.",
         actual="404 \"Supervisor 999999 not found\".",
         result="PASS", severity="",
         notes="Correct, clear error handling for an invalid ID.")
    ,
    dict(id="M2-08 / M2-09", feature="Peer Groups List (open / all)", endpoint="GET /matching/groups",
         input="status=open, then status=all",
         criteria="Should return the real peer_groups rows filtered correctly by status.",
         actual="Both return the same 3 real groups (confirmed all 3 existing rows have status=\"open\", so \"all\" "
               "and \"open\" are expected to coincide with this data). Response shape and pagination fields "
               "correct.",
         result="PASS", severity="",
         notes="IMPORTANT — documentation defect found while building this test: this router (app/routers/peer.py) "
               "is documented in its own module docstring as being mounted at \"/peers/groups\", but main.py "
               "actually mounts it with `prefix=\"/matching\"`, so the real path is \"/matching/groups\". The "
               "gateway (module2.routes.ts) already uses the correct real path, so end users are unaffected — but "
               "the router's own source-code docstring is wrong and would mislead anyone reading it as API "
               "reference (as it initially did during this validation). Recommend fixing the docstring to match "
               "main.py's actual mount prefix.")
    ,
    dict(id="M2-10", feature="Aspect-Based Sentiment (clearly positive text)", endpoint="POST /feedback/analyze",
         input="Feedback text unambiguously praising methodology, writing, originality, and data-analysis support.",
         criteria="Should return positive sentiment with high, well-differentiated confidence across all 4 aspects.",
         actual="overall_sentiment=\"positive\", overall_score=0.95. Per-aspect positive probabilities: "
               "methodology 0.95, writing 0.90, originality 0.95, data_analysis 0.98.",
         result="PASS", severity="",
         notes="Genuine Gemini call succeeded; well-calibrated, differentiated aspect scores.")
    ,
    dict(id="M2-11", feature="Aspect-Based Sentiment (clearly negative text)", endpoint="POST /feedback/analyze",
         input="Feedback text unambiguously critical of methodology, writing, originality, and data-analysis "
               "support.",
         criteria="Should return negative sentiment with high, well-differentiated confidence across all 4 "
                  "aspects.",
         actual="overall_sentiment=\"negative\", overall_score=-0.95. Per-aspect negative probabilities: "
               "methodology 0.95, writing 0.90, originality 0.95, data_analysis 0.99.",
         result="PASS", severity="",
         notes="Genuine Gemini call succeeded; correctly mirrors M2-10's quality at the negative extreme.")
    ,
    dict(id="M2-12", feature="Aspect-Based Sentiment (mixed/nuanced text — the core use case)", endpoint="POST /feedback/analyze",
         input="Feedback text that is positive about methodology but negative/lukewarm about writing, "
               "originality, and data-analysis — i.e. the realistic case aspect-based sentiment exists to handle.",
         criteria="Should differentiate sentiment PER ASPECT (e.g. methodology positive, others negative/neutral) "
                  "— this is the feature's entire reason for existing over plain overall sentiment.",
         actual="overall_sentiment=\"neutral\", overall_score=0.0, ALL FOUR aspects flatly \"neutral\", "
               "aspect_probabilities=null — zero differentiation despite the input text clearly having mixed "
               "sentiment.",
         result="FAIL", severity="High",
         notes="Server log confirms: \"INFO:app.routers.feedback:Gemini sentiment unavailable, using neutral "
               "default: Unterminated string starting at: line 4 column 19 (char 206)\" — a Gemini JSON-parse "
               "failure. This is the single most consequential finding for this feature: across the 3 sentiment "
               "test calls made in this session, 2 of 3 (M2-06's research-focus call and this one) failed to "
               "parse Gemini's JSON output; only the two emotionally-extreme cases (M2-10, M2-11) succeeded. The "
               "case that most needs per-aspect differentiation — mixed sentiment — is exactly the one that "
               "silently collapsed to a useless flat \"neutral\" with no error surfaced to the caller. This "
               "reliability gap should be investigated (likely a prompt/max_tokens truncation issue in "
               "shared/gemini_client.py) before this feature can be trusted for real feedback analysis.")
    ,
    dict(id="M2-13", feature="Rateable Supervisor Directory", endpoint="GET /feedback/supervisors",
         input="—",
         criteria="Should list both SLIIT-directory and system-registered supervisors with consistent schema.",
         actual="Returns a well-formed list combining \"sliit:N\" and \"system:<uuid>\" keyed entries with "
               "consistent fields (name, email, department, research_areas, availability).",
         result="PASS", severity="",
         notes="Correct, consistent dual-source directory listing.")
    ,
    dict(id="M2-14", feature="Supervisor Effectiveness Scoring (list)", endpoint="GET /effectiveness",
         input="limit=30",
         criteria="overall_score should exactly match the documented weighted-blend formula "
                  "(0.40·stars + 0.25·sentiment + 0.15·satisfaction + 0.20·completion, re-normalised over "
                  "available signals) when computed by hand from the same row's raw data.",
         actual="Top result: avg_stars=5.0, n_ratings=1, overall_score=0.8. Hand-verified: star_norm=1.0 "
               "(weight .40), sentiment derived from stars-only fallback (5★→score 1.0, weight .25), "
               "satisfaction=1.0 (weight .15), completion=0.0 for this SLIIT-directory entry (weight .20, always "
               "0 for non-system supervisors) → 0.40+0.25+0.15+0.00 = 0.80 exactly. Formula verified correct.",
         result="PASS", severity="Medium",
         notes="The score computation itself is mathematically verified correct against real data. However this "
               "verification surfaces a structural design finding: because `completion_rate` is unconditionally "
               "included in the blend at weight 0.20 but is ALWAYS 0.0 for SLIIT-directory supervisors (they have "
               "no supervisor_matches rows to compute completion from — only \"system\"-registered supervisors "
               "can have a nonzero value), every SLIIT-directory supervisor has a hard ceiling of ~0.80 on their "
               "effectiveness score no matter how perfect their ratings are. If SLIIT-directory and "
               "system-registered supervisors are ever compared/ranked side by side on this score, the "
               "comparison would be structurally unfair. Recommend either excluding the completion term for "
               "sources where it's inapplicable (re-normalising over the remaining signals, as already done for "
               "missing star/sentiment data) or clearly labelling the two supervisor types as non-comparable.")
]

ENV_NOTES = [
    "Supabase tables actually used by this module: `peer_groups` (3 real rows), `peer_group_join_requests` (2), "
    "`supervisor_ratings` (5), `profiles` (9) — all populated, so Peer Connect and Effectiveness Scoring were "
    "fully testable against real data. `supervisor_matches` (completion-rate source for system supervisors) is "
    "empty, so the completion-rate component of the effectiveness formula could not be exercised with a nonzero "
    "value in this environment, though its logic was independently verified by code review.",
    "Supervisor matching itself does not depend on Supabase at all — it reads a local JSON file "
    "(data/supervisors_with_embeddings.json), so its results are fully live/production-representative regardless "
    "of database state.",
    "Live Semantic Scholar and Gemini API calls succeeded overall, but Gemini's JSON output was malformed on 2 "
    "of the ~5 calls made in this session across two different endpoints (M2-06, M2-12) — a real, repeatable "
    "reliability signal for this module, not a one-off fluke.",
    "Per team decision, write endpoints (submitting a rating, creating a peer group, join requests) were not "
    "exercised live to avoid writing test data into the real database; /feedback/analyze was used instead of "
    "/feedback/submit for sentiment testing since it performs the same analysis without persisting a row.",
]

KEY_FINDINGS = [
    ("High", "Aspect-based sentiment analysis silently collapses to an undifferentiated \"neutral\" response for "
     "mixed-sentiment feedback — precisely the case the feature exists to handle — due to a Gemini JSON-parsing "
     "failure with no error surfaced to the caller (M2-12). This failure mode was reproduced twice in one "
     "session (also M2-06)."),
    ("Medium", "The Supervisor Effectiveness score formula is mathematically verified correct, but structurally "
     "caps every SLIIT-directory supervisor's maximum achievable score at ~0.80 because the completion-rate term "
     "is always zero for that source type (M2-14)."),
    ("Medium", "app/routers/peer.py's own module docstring documents the wrong mount path (\"/peers/groups\" "
     "instead of the actual \"/matching/groups\"), which would mislead a developer reading the source as API "
     "reference (M2-08/09)."),
    ("Low", "An empty proposal string silently matches against a placeholder \"general research\" query instead "
     "of returning an empty result or validation error (M2-04)."),
]

NARRATIVE = (
    "Supervisor Matching is the strongest-performing feature in this module: all three domain-specific test "
    "proposals (AI/ML, cybersecurity, NLP) returned highly relevant supervisors with sensible similarity scores, "
    "and both the new free-text and legacy request formats work equally well. The Supervisor Profile feature's "
    "live Semantic Scholar integration and Gemini research-focus summarisation are impressive when they work — "
    "the AI summary for supervisor 1 was independently verified as accurate and genuinely grounded in the fetched "
    "publication titles — but the underlying Gemini call is not reliable: 2 of roughly 5 Gemini-dependent calls "
    "in this session failed to parse, and the resulting silent degradation is most damaging in Aspect-Based "
    "Sentiment Analysis, where a clearly mixed-sentiment test input collapsed to a flat, useless \"neutral\" "
    "result with zero differentiation and no error signal — this is the single highest-priority finding from this "
    "validation and should be investigated before the Feedback feature is relied upon for real supervisor "
    "reviews. Effectiveness Scoring's formula was independently hand-verified against real data and is "
    "mathematically correct, but has a structural fairness gap for SLIIT-directory supervisors that the team "
    "should be aware of. One source-level documentation bug (peer.py's docstring) was found and should be "
    "corrected. None of these findings require an architectural change — they are each a specific, fixable issue "
    "in a specific function."
)

if __name__ == "__main__":
    build_workbook(
        "Module2_Collaboration_Validation_Report.xlsx",
        2, "Collaboration & Recommendation", "S. P. U. Gunathilaka",
        "services/module2-collaboration (FastAPI, port 8002)",
        ROWS, ENV_NOTES, KEY_FINDINGS, NARRATIVE,
    )
