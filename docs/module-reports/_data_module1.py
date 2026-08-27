# -*- coding: utf-8 -*-
from _build_excel import build_workbook

ROWS = [
    dict(id="M1-01", feature="Citation Parser (APA journal)", endpoint="POST /citations/parse",
         input="Clean APA-style journal citation: \"Perera, K. and Silva, M. (2021). Deep learning for crop disease "
               "detection in Sri Lanka. Journal of Agricultural Informatics, 12(3), 45-58.\"",
         criteria="Authors, title, year, journal, volume, issue, pages should all be correctly extracted; formatted "
                  "APA/IEEE strings should be well-formed.",
         actual="Authors/year/title extracted correctly. journal field = \"ournal of Agricultural Informatics, 12(3), "
                "45-58\" (missing leading 'J'; volume/issue/pages not split out, all in the string). "
                "confidence=0.75 despite the defect.",
         result="PARTIAL", severity="Medium",
         notes="Root cause: citation_engine.py's title-splitting regex `(.+?)[\\.!?](\\s+[A-Z]|\\s*$)` matches the "
               "sentence-ending period PLUS the following capital letter as part of the same match, so the venue "
               "text after the title loses its first character. Separately, _VOLUME_RE/_PAGE_RE only match "
               "\"vol./volume\"/\"pp.\" keyword forms and don't recognise the common inline \"12(3), 45-58\" "
               "journal-citation shorthand, so volume/issue/pages stay null even though present in the source text. "
               "The confidence formula still awards full journal-field credit since the (wrong) string is truthy.")
    ,
    dict(id="M1-02", feature="Citation Parser (IEEE-formatted input)", endpoint="POST /citations/parse",
         input="Already-IEEE-formatted citation: \"J. Fernando, S. Bandara and A. Kumar, \\\"IoT-based smart "
               "irrigation system,\\\" in Proc. IEEE Int'l Conf. on Smart Computing, 2020, pp. 112-119.\"",
         criteria="Parser should extract authors/title/venue/year reasonably even for non-APA input, or at minimum "
                  "degrade gracefully with accurate low-confidence + warnings.",
         actual="source_type correctly detected as \"conference\". authors=[] (empty), title=\"Fernando, S\" "
                "(wrong — this is a truncated author name, not a title), everything else mashed into the "
                "\"conference\" field, year not detected despite \"2020\" being present. confidence=0.35, 2 warnings.",
         result="FAIL", severity="Medium",
         notes="The parser's split logic assumes APA author-year-title ordering; when fed genuinely IEEE-ordered "
               "input (Authors, \"Title,\" in Venue, pp, year.) the author/title split breaks down completely. This "
               "is a real functional gap for a citation tool that a student could reasonably paste an IEEE-style "
               "reference into (e.g. copied from another paper's reference list). Confidence score (0.35) does "
               "correctly signal low quality, so the UI warning system would still flag it, but the auto-parsed "
               "fields would actively mislead if a user pasted an IEEE reference without checking.")
    ,
    dict(id="M1-03", feature="Citation Parser (unstructured/incomplete)", endpoint="POST /citations/parse",
         input="Deliberately unstructured text: \"Some paper about machine learning without proper structure\"",
         criteria="No crash; appropriate warnings for each missing required field; low confidence score reflecting "
                  "poor extraction.",
         actual="authors=[], year=null, journal=null, title=full input text (correct fallback). 3 accurate "
                "warnings (author/year/journal missing). confidence=0.25.",
         result="PASS", severity="",
         notes="Correct graceful degradation — this is exactly the intended behaviour for genuinely unparseable "
               "input; the low confidence score and warning list give the user an honest signal rather than a "
               "false-confident wrong parse.")
    ,
    dict(id="M1-04", feature="Citation Formatter (clean structured input)", endpoint="POST /citations/format",
         input="Well-formed structured record (authors, title, year, journal, vol/issue/pages, DOI) → style=ieee",
         criteria="Output should match IEEE citation style exactly: initials-then-surname authors, quoted title, "
                  "italic venue, vol./no./pp./year, doi:.",
         actual="\"K. Perera and M. Silva, \\\"Deep learning for crop disease detection in Sri Lanka,\\\" *Journal "
               "of Agricultural Informatics*, vol. 12, no. 3, pp. 45-58, 2021. doi: 10.1234/jai.2021.0012.\" — "
               "correct on every field.",
         result="PASS", severity="",
         notes="Confirms the formatter itself is correct; the defects found in M1-01/M1-02 are isolated to the "
               "regex-based PARSER (raw text → structured fields), not the formatter (structured fields → styled "
               "string). Whenever the input record is already correctly structured, formatting is reliable.")
    ,
    dict(id="M1-05", feature="DOI Lookup (CrossRef, real DOI)", endpoint="POST /citations/lookup-doi",
         input="Real, independently-verifiable DOI: 10.1038/nphys1170",
         criteria="Should return the genuine CrossRef metadata for this DOI and format it correctly in both styles.",
         actual="Returned correct real metadata: Aspelmeyer, M. (2009), \"Measured measurement\", Nature Physics, "
               "vol 5(1), pp 11-12. Both APA and IEEE formatted strings are well-formed and accurate. "
               "confidence=0.85, source=\"crossref\".",
         result="PASS", severity="",
         notes="Independently verifiable — this is a real, published Nature Physics commentary. CrossRef "
               "integration and downstream formatting both work correctly end-to-end for real DOIs.")
    ,
    dict(id="M1-06", feature="Similar Papers (SBERT retrieval)", endpoint="POST /citations/similar-papers",
         input="Query: \"machine learning for early detection of plant diseases\", top_k=5",
         criteria="Returned papers should be genuinely topically relevant, real SLIIT papers, with sensibly "
                  "decreasing similarity scores.",
         actual="5 real SLIIT papers returned, ALL genuinely on-topic (plant/crop disease detection via ML/CNN, "
               "Twitter-annexed disease detection, soilless-farming disease detection, banana disease ID, "
               "greenhouse disease monitoring). Similarity smoothly decreasing 0.655 → 0.589.",
         result="PASS", severity="",
         notes="Excellent precision — every one of the top-5 results is a genuine match for the query topic. "
               "Strong evidence the SBERT retrieval layer (shared by several Module 1 features) works well.")
    ,
    dict(id="M1-07", feature="Reference List Builder (APA sort order)", endpoint="POST /citations/reference-list",
         input="Two entries: Zhang, Y. (2019, journal J.X) and Amir, A. (2020, journal J.Y); style=apa",
         criteria="APA style should sort entries alphabetically by first-author surname, not input order.",
         actual="Output order: \"Amir, A. (2020)...\" then \"Zhang, Y. (2019)...\" — correctly alphabetised "
               "despite Zhang being listed first in the request.",
         result="PASS", severity="",
         notes="Confirms the APA sort-by-surname logic (as opposed to IEEE's preserve-input-order numbering) "
               "works correctly.")
    ,
    dict(id="M1-08", feature="Research Gap Analysis (specific compound topic)", endpoint="POST /gaps/analyze",
         input="Topic: \"machine learning for crop disease detection in Sri Lanka\", top_k=6, min_similarity=0.15",
         criteria="Returned gaps should be substantively relevant to the query topic, grounded in real supporting "
                  "papers, with sensible trend/classification/recommendation output.",
         actual="Pipeline executed correctly (553-gap SBERT index, scoring, classification, trends, cross-domain, "
               "recommendations all populated) but only 1 of 6 returned gaps (paddy-yield ANN prediction) is "
               "genuinely on-topic; the other 5 are about adolescent perfectionism, industrial machine-failure "
               "prediction, temperature/humidity trends, roofing-material lifecycle analysis, and child mortality "
               "— matched mainly on loose keyword overlap (\"Sri Lanka\", \"machine learning\") at similarity "
               "0.32-0.41, not real topical relevance.",
         result="PARTIAL", severity="Medium",
         notes="Not a code defect — the ranking/scoring math is internally consistent — but a real precision "
               "limitation: the underlying gap corpus (553 extracted gap statements from 494 papers) is thin "
               "for a specific compound topic like this, so the system stretches down toward its similarity floor "
               "to fill top_k=6 rather than returning fewer, more relevant results. Cross-domain opportunity "
               "suggestions are also computed from a primary-domain sample of just 1 paper "
               "(\"papers_in_primary\": 1), so their opportunity_score=1.0 claims are statistically thin evidence "
               "presented with high apparent confidence.")
    ,
    dict(id="M1-09", feature="Research Gap Analysis (out-of-corpus topic)", endpoint="POST /gaps/analyze",
         input="Deliberately obscure/out-of-corpus topic: \"quantum cryptography for underwater acoustic sensor "
               "networks\", top_k=6, min_similarity=0.15",
         criteria="For a topic with essentially no real corpus coverage, the system should ideally signal low "
                  "confidence / no strong matches rather than presenting weak matches as confident findings.",
         actual="Returned 6 \"gaps\" down to similarity 0.15-0.33 (Sinhala Sign Language, smart-city anomaly "
               "detection, institutional repositories, underwater robotic arm, image tampering) — only the "
               "underwater-robotics one is even tangentially related. Trend interpretation claims \"rising +32%\" "
               "based on a total of just 12 supporting papers across the whole result set.",
         result="PARTIAL", severity="Medium",
         notes="Confirms the same pattern as M1-08 on a harder case: `min_similarity` acts only as a per-candidate "
               "floor, not an overall-confidence gate — there is no \"no strong matches found\" response path even "
               "when every returned result is weak. A student searching a genuinely novel/niche topic could be "
               "misled into thinking these loosely-related papers represent real evidenced gaps in that space.")
    ,
    dict(id="M1-10", feature="Gap Analyzer status/health", endpoint="GET /gaps/status",
         input="—",
         criteria="Should accurately report index size and model version.",
         actual="loaded=true, 553 gaps, 494 unique papers, embedding_dim=384, base_model=\"sbert_plagiarism "
               "(SLIIT fine-tuned)\" — consistent with observed behaviour in M1-08/09.",
         result="PASS", severity="",
         notes="Metadata is accurate and internally consistent with the corpus size implied by the actual "
               "analyze() results.")
    ,
    dict(id="M1-11", feature="Proposal Generation (well-covered topic)", endpoint="POST /proposals/generate",
         input="Topic: \"IoT-based smart irrigation for paddy fields\", domain=\"Agriculture Technology\", top_k=5",
         criteria="Retrieved exemplar papers should be genuinely relevant; composed proposal sections should read "
                  "coherently and cite real sources.",
         actual="All 5 retrieved papers are directly on-topic (canal-automation irrigation, IoT crop-yield "
               "sensors, IoT crop recommender, IoT/AI gardening irrigation, domestic smart irrigation) with strong "
               "similarity 0.632-0.721. Composed problem statement correctly quotes and attributes the top "
               "exemplar (Sanjula et al., 2020) by name and year. Objectives/methodology/outcomes are coherent "
               "and topic-appropriate.",
         result="PASS", severity="",
         notes="Strong result — this is the module's largest SBERT index (3,858 exemplars vs. 553 for gap "
               "analysis), and it shows: precision here is markedly better than the gap-analysis tests (M1-08/09), "
               "confirming corpus size is the key driver of result quality for this retrieval-based design.")
    ,
    dict(id="M1-12", feature="Proposal Retriever status/health", endpoint="GET /proposals/status",
         input="—",
         criteria="Should accurately report index size and model version.",
         actual="loaded=true, 3858 exemplars, embedding_dim=384 — consistent with observed strong M1-11 results.",
         result="PASS", severity="",
         notes="Accurate, consistent metadata.")
    ,
    dict(id="M1-13", feature="Plagiarism Check (novel text)", endpoint="POST /plagiarism/check",
         input="Deliberately unique, never-published sentence about \"purple sea urchins in Antarctic waters\", "
               "threshold=0.8",
         criteria="Should correctly report low/no risk for genuinely novel text.",
         actual="risk_level=\"low\", overall_score=0.0, no flagged passages.",
         result="BLOCKED", severity="N/A",
         notes="Result looks correct on its face, but cannot be treated as validating evidence: direct inspection "
               "of the Supabase database (read-only query) confirms the `research_papers` table backing this "
               "feature's pgvector match has 0 rows and 0 embeddings in this environment. The endpoint will "
               "return this exact \"low/0.0\" response for ANY input, correct or not, until the corpus is "
               "populated with embeddings. This test cannot distinguish \"working correctly\" from \"backing data "
               "missing\" — needs re-validation once research_papers has real embedded rows.")
    ,
    dict(id="M1-14", feature="Plagiarism Check (generic but plausible academic sentence)", endpoint="POST /plagiarism/check",
         input="Realistic, generic-sounding ML sentence about CNNs for image classification, threshold=0.75 "
               "(a sentence type likely to closely resemble real corpus content)",
         criteria="If the corpus contains genuinely similar content, should flag at least moderate similarity; "
                  "should not silently look identical to a true \"no match\" case.",
         actual="Identical result to M1-13: risk_level=\"low\", overall_score=0.0, no flagged passages.",
         result="BLOCKED", severity="N/A",
         notes="Same environment blocker as M1-13. Additionally, independent of the empty-table issue, code review "
               "shows a design quirk worth re-testing once data exists: the SQL RPC filters by `match_threshold` "
               "server-side, so when no paper clears the threshold the code appends a placeholder 0.0 rather than "
               "the true (sub-threshold) similarity — meaning `overall_score: 0.0` will always be reported for "
               "\"no match above threshold\", which is indistinguishable from a genuine zero-similarity result. "
               "Recommend the endpoint report the true top similarity even when it's below threshold.")
    ,
    dict(id="M1-15", feature="Mind Map Generation", endpoint="POST /mindmaps/generate",
         input="~90-word paragraph about CNN-based plant-disease detection (background/methodology/results/future "
               "work), max_nodes=15",
         criteria="Central node and concept hierarchy should reflect genuine key concepts from the text (e.g. "
                  "\"deep learning\", \"plant disease detection\", \"CNN\"), not just raw word frequency.",
         actual="Central node = \"investigates\" (a verb); other nodes are single common words (\"deep\", "
               "\"learning\", \"specifically\", \"convolutional\", \"neural\", \"networks\", \"plant\", "
               "\"diseases\"...) all with weight exactly 1.0. This is the pattern of the LOCAL TERM-FREQUENCY "
               "FALLBACK, not genuine Gemini concept extraction.",
         result="PARTIAL", severity="Medium",
         notes="Confirmed via server log: \"WARNING:app.routers.mindmap:Gemini mindmap failed (Expecting value: "
               "line 1 column 798 char 797) — using local fallback\" — Gemini's response failed to parse as valid "
               "JSON (likely truncated by the prompt/response format), and the code correctly caught this and "
               "fell back as designed. The FALLBACK MECHANISM itself works correctly (no crash, no empty result), "
               "but (a) the primary/higher-quality Gemini path is currently unreliable, degrading output quality "
               "silently, and (b) unlike Module 1's other multi-path endpoints (citation lookup, proposal "
               "generation), this response has no `source` field, so the frontend/caller has no way to know "
               "whether a given mind map came from the LLM or the crude word-frequency fallback.")
]

ENV_NOTES = [
    "The Supabase instance used for this validation has `research_papers` (0 rows), `research_proposals` (0), "
    "`research_summaries` (0), and `plagiarism_trends` (0) — i.e. the live pgvector-backed corpus tables are "
    "empty. Features driven by the LOCAL pickled SBERT indices shipped with the service (gap analysis, proposal "
    "generation, similar-papers) were fully testable and returned real, evidenced results. The one feature that "
    "depends on the live Supabase `research_papers.embedding` column (Plagiarism Checker, /plagiarism/check) "
    "could not be meaningfully validated and is marked BLOCKED, not FAIL — its code path is sound on inspection, "
    "but there is no data to prove it against.",
    "GEMINI_API_KEY and SUPABASE credentials were present and working (confirmed live calls succeeding for "
    "CrossRef lookups, similar-papers, and gap analysis); Gemini itself intermittently returned malformed JSON "
    "for the mind-map endpoint during this session (see M1-15) — this is a live-call reliability observation, "
    "not a missing-credential issue.",
]

KEY_FINDINGS = [
    ("Medium", "Citation parser drops the first character of the journal/venue field when a citation follows "
     "the common \"Author (Year). Title. Journal, vol(issue), pages.\" shape — a regex boundary bug in "
     "citation_engine.py's title-extraction pattern (M1-01)."),
    ("Medium", "Citation parser produces badly garbled output (empty authors, wrong title, undetected year) when "
     "fed an already IEEE-formatted reference rather than raw/APA-shaped text (M1-02)."),
    ("Medium", "Research Gap Analysis has no \"no confident match\" response — for narrow or out-of-corpus "
     "topics it still returns top_k results down to the similarity floor, presented with the same formatting "
     "and confidence as strong matches (M1-08, M1-09)."),
    ("Medium", "Mind Map generation silently falls back from Gemini to a crude local word-frequency heuristic "
     "on Gemini JSON-parse failures, with no `source` field in the response to indicate this happened (M1-15)."),
    ("Low", "Plagiarism Checker cannot be validated end-to-end in the current environment because the backing "
     "`research_papers` table has no embedded rows (M1-13, M1-14) — an environment/data gap, not a code defect."),
]

NARRATIVE = (
    "Module 1's retrieval-based features that draw on the large, locally-shipped SBERT indices — Similar Papers "
    "(3,858/4,219-paper corpus) and Proposal Generation in particular — perform very well, returning genuinely "
    "relevant, well-grounded results with accurate similarity scoring. The Citation Formatter and CrossRef DOI "
    "lookup are both fully correct against real, independently-verifiable data. Two areas need attention before "
    "this module could be presented as production-ready: (1) the regex-based Citation Parser has two concrete, "
    "reproducible defects — a character-loss bug on the common APA journal shape, and a much larger breakdown "
    "when fed IEEE-formatted input rather than APA — and (2) Research Gap Analysis, which draws on a much "
    "smaller 553-statement index, shows materially weaker precision for narrow or poorly-covered topics because "
    "the system has no confidence gate and will always return top_k results regardless of match quality. The "
    "Plagiarism Checker's logic reads correctly on inspection but could not be exercised end-to-end because the "
    "Supabase research_papers table is currently empty in this environment — this needs re-validation once the "
    "corpus is populated with real embeddings before it can be signed off. None of the findings are architectural "
    "— all are localised, fixable issues in specific functions, and the overall retrieval-augmented design "
    "approach (grounding every output in real cited SLIIT papers rather than free LLM generation) is sound and "
    "clearly demonstrated by the evidence above."
)

if __name__ == "__main__":
    build_workbook(
        "Module1_Integrity_Validation_Report.xlsx",
        1, "Research Integrity & Compliance", "K. D. T. Kariyawasam",
        "services/module1-integrity (FastAPI, port 8001)",
        ROWS, ENV_NOTES, KEY_FINDINGS, NARRATIVE,
    )
