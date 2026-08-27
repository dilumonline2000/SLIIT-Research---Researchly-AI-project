# -*- coding: utf-8 -*-
from _build_excel import build_workbook

ROWS = [
    dict(id="M3-01", feature="Topic Categorization (CS/ML abstract)", endpoint="POST /data/categorize",
         input="Abstract about a CNN architecture for medical image classification. threshold=0.2, top_k=5",
         criteria="Top categories and related papers should be genuinely relevant to deep learning / medical "
                  "imaging.",
         actual="categories=[\"deep learning\"] (0.28 confidence); top_categories also surface machine learning "
               "(0.14), image processing (0.06), AI (0.04), classification (0.03) — all correct and relevant. 6 "
               "related papers returned, ALL genuinely on-topic (pneumonia X-ray detection, retinal disease "
               "detection, medical-image explainability, mosquito classification, facial/verbal disease "
               "detection, diabetic retinopathy) with similarity 0.49-0.65.",
         result="PASS", severity="",
         notes="Strong result for a CS/technical-domain input — both the classifier and the SBERT related-paper "
               "retrieval performed well.")
    ,
    dict(id="M3-02", feature="Topic Categorization (business abstract)", endpoint="POST /data/categorize",
         input="Abstract about digital marketing strategy impact on SME growth. threshold=0.2, top_k=5",
         criteria="Should identify business/marketing-relevant categories at reasonable confidence.",
         actual="categories=[] — EMPTY, nothing cleared the 0.2 threshold. Highest top_category confidence is only "
               "0.11 (\"sri lanka\"), with no business/marketing/management label appearing despite \"management\" "
               "existing in the 80-label vocabulary. Related papers, however, are excellent and clearly on-topic "
               "(SME IT management, digital marketing for hotels, SME marketing strategy via data analysis).",
         result="PARTIAL", severity="Medium",
         notes="The TF-IDF+LogReg classifier produces essentially no usable signal for this genuinely "
               "business-domain text, even though the corpus clearly contains matching content (proven by the "
               "strong related-paper results, which use a separate SBERT retrieval path, not the classifier). "
               "Suggests the 80-label vocabulary and/or its training data skews toward CS/technical topics.")
    ,
    dict(id="M3-03", feature="Topic Categorization (health abstract)", endpoint="POST /data/categorize",
         input="Abstract about a physiotherapy intervention for post-surgical knee rehabilitation in elderly "
               "patients. threshold=0.2, top_k=5",
         criteria="Should identify health/medical-relevant categories at reasonable confidence.",
         actual="categories=[] — again EMPTY, top confidence only 0.10 (\"sri lanka\"), no health-specific label "
               "surfaced. Related papers are again excellent and clearly on-topic (VirtualPT home physiotherapy, "
               "knee exoskeleton design, robot-assisted hand rehabilitation) with similarity up to 0.46.",
         result="PARTIAL", severity="Medium",
         notes="Reproduces the exact same pattern as M3-02 on an independent, unrelated domain (health rather "
               "than business) — this is a consistent, reproducible finding, not a one-off: the classifier's 80 "
               "labels are heavily CS/tech-weighted (confirmed by the label list itself in M3-04: labels like "
               "\"cnn\", \"iot\", \"neural network\", \"blockchain\" vs. only a handful of generic non-CS terms "
               "like \"mental health\", \"job satisfaction\", \"poverty\"), so genuinely non-CS content gets weak "
               "or empty classification even when the underlying SBERT retrieval proves the content IS well "
               "represented in the corpus.")
    ,
    dict(id="M3-04", feature="Topic Classifier status/health", endpoint="GET /data/categorize/status",
         input="—",
         criteria="Should accurately report the label set and version.",
         actual="loaded=true, 80 labels. Label list confirmed CS/tech-dominated (machine learning, deep learning, "
               "cnn, iot, blockchain, computer vision... vs. very few non-CS terms).",
         result="PASS", severity="",
         notes="Metadata accurate; corroborates the M3-02/M3-03 finding by exposing the actual label vocabulary.")
    ,
    dict(id="M3-05", feature="Summarizer (standard length)", endpoint="POST /data/summarize",
         input="~250-word structured research abstract (background/methodology/results/limitations/conclusion), "
               "length=standard (target 9 points)",
         criteria="Should select ~9 of the most salient sentences and correctly categorise each into its section.",
         actual="Selected 9/10 input sentences (compression_ratio 0.904, appropriate for an already-short/dense "
               "input). 8 of 9 category assignments are correct (background/methodology×2/results×2/"
               "limitations/conclusion×2); one opening sentence (\"This paper presents a novel deep learning "
               "approach...\") was tagged \"conclusion\" instead of \"objective\".",
         result="PASS", severity="Low",
         notes="~89% correct categorisation in this test. Root cause of the one miscategorisation: the "
               "\"conclusion\" regex pattern matches \"this (paper|study|work) (has shown|demonstrates|"
               "presents)\", and the opening sentence's verb \"presents\" happens to match that pattern even "
               "though it's semantically an OPENING/framing sentence, not a concluding one. Minor, low-severity "
               "categorisation nuance rather than a functional failure — the overall summary quality remains "
               "high.")
    ,
    dict(id="M3-06", feature="Summarizer (quick length)", endpoint="POST /data/summarize",
         input="Same abstract as M3-05, length=quick (target 5 points)",
         criteria="Should compress further than \"standard\", keeping the most salient background/methodology/"
                  "conclusion content.",
         actual="Selected 5/10 sentences (compression_ratio 0.585), correctly dropped the detailed "
               "results/limitations sentences while keeping background, both methodology sentences, and both "
               "conclusion sentences.",
         result="PASS", severity="",
         notes="Length scaling behaves exactly as documented — fewer, higher-priority points for \"quick\".")
    ,
    dict(id="M3-07", feature="Summarizer (extensive length)", endpoint="POST /data/summarize",
         input="Same abstract as M3-05, length=extensive (target 18 points, capped by input size)",
         criteria="Should return effectively the full input when the target exceeds available sentences.",
         actual="Selected all 10/10 input sentences (compression_ratio 1.0 exactly, target_n correctly capped at "
               "min(18, n=10)). Full 6-category breakdown produced.",
         result="PASS", severity="",
         notes="Correctly handles the target > input-length edge case.")
    ,
    dict(id="M3-08", feature="Summarizer status/health", endpoint="GET /data/summarize/status",
         input="—",
         criteria="Should accurately report algorithm description and supported lengths.",
         actual="loaded=true, algorithm=\"extractive (centroid + lead-bias + MMR + categorisation)\", all 6 length "
               "presets and 6 categories listed correctly.",
         result="PASS", severity="",
         notes="Accurate metadata.")
    ,
    dict(id="M3-09", feature="Plagiarism Trend Search (topic-aware)", endpoint="POST /data/plagiarism-trends/search",
         input="Topic: \"machine learning crop disease detection\", top_k=5, min_topic_similarity=0.15",
         criteria="Should surface relevant pre-computed topic buckets with sensible yearly similarity trends and "
                  "specific evidence (flagged paper pairs).",
         actual="Matched the \"machine learning\" topic bucket (similarity 0.43) with a detailed 2019-2022 yearly "
               "breakdown (avg/max/p95 similarity, trend direction per year) and specific named flagged pairs "
               "(e.g. two ML-based fraud/vulnerability-detection papers at 0.40 similarity).",
         result="PASS", severity="",
         notes="Behaves as designed — this is deliberately a topic-level trend view, not a direct plagiarism "
               "accusation between specific papers, and the output correctly reflects that framing.")
    ,
    dict(id="M3-10", feature="Plagiarism Trends (legacy Supabase endpoint, empty-table fallback)", endpoint="GET /data/plagiarism-trends",
         input="year_from=2018, year_to=2026",
         criteria="Should gracefully fall back to synthesising from the local corpus when the Supabase "
                  "`plagiarism_trends` table is empty, rather than returning an error or silently empty result.",
         actual="source=\"local-corpus\" — correctly detected the empty table and synthesised 14 trend rows from "
               "the local trend_index.pkl exactly as designed.",
         result="PASS", severity="Low",
         notes="Graceful degradation confirmed working correctly. Separately notable: several buckets report "
               "max_similarity=1.0 between DIFFERENT paper IDs (\"innovation performance\" 2019, \"business "
               "intelligence\" 2021, \"artificial intelligence\" 2024) — a near-certain sign of duplicate paper "
               "records in the corpus. This is independently corroborated by Module 2's validation (supervisor "
               "profile test M2-05/06 observed the exact same paper title \"VirtualPT: Virtual Reality based Home "
               "Care Physiotherapy...\" appearing twice under two different paper_ids with matching abstracts). "
               "Recommend a deduplication pass on the scraped corpus — duplicate records would inflate false "
               "\"high similarity\" plagiarism signals between what is really the same paper counted twice.")
    ,
    dict(id="M3-11", feature="Plagiarism Compare (near-identical / lightly paraphrased pair)", endpoint="POST /data/plagiarism-trends/compare",
         input="Two versions of the same ~250-word abstract, ~90% of wording unchanged (only country name and "
               "one model name swapped).",
         criteria="Should report very high document similarity and \"high\" risk, with the unmodified sentences "
                  "flagged as exact matches.",
         actual="document_similarity=0.987, ngram_jaccard=0.937, risk_score=0.975, risk_level=\"high\". All 5 "
               "unmodified sentences correctly flagged at similarity=1.0.",
         result="PASS", severity="",
         notes="Accurate, precise result at the high-similarity end of the spectrum.")
    ,
    dict(id="M3-12", feature="Plagiarism Compare (completely unrelated pair)", endpoint="POST /data/plagiarism-trends/compare",
         input="The same plant-disease abstract vs. an unrelated paragraph about stock-market volatility and "
               "investment portfolios.",
         criteria="Should report near-zero similarity and \"minimal\" risk with no flagged pairs.",
         actual="document_similarity=-0.009 (~0), ngram_jaccard=0.0, risk_score≈-0.006, risk_level=\"minimal\", "
               "zero flagged pairs.",
         result="PASS", severity="",
         notes="Accurate result at the low-similarity end. Together, M3-11 and M3-12 give strong confidence the "
               "compare_papers pipeline is correctly calibrated across the full similarity range.")
    ,
    dict(id="M3-13", feature="Plagiarism Analyzer status/health", endpoint="GET /data/plagiarism-trends/status",
         input="—",
         criteria="Should accurately report index/model load state.",
         actual="sbert_loaded=true, trend_index_loaded=true, n_topics=17.",
         result="PASS", severity="",
         notes="Accurate metadata.")
    ,
    dict(id="M3-14", feature="Data Quality Metrics", endpoint="GET /data/quality",
         input="—",
         criteria="Should compute completeness/consistency/duplicate-rate from real research_papers rows.",
         actual="total_papers=0, all scores 0.0, sources={} — correctly reflects that `research_papers` is empty "
               "in this environment (verified by direct DB query: 0 rows).",
         result="BLOCKED", severity="N/A",
         notes="The code path itself is correct (accurately reports \"no data\" rather than crashing or "
               "fabricating a score), and the completeness/consistency formulas were independently checked "
               "against the source and found to be simple, sound arithmetic. However this endpoint cannot be "
               "validated end-to-end for correctness on real data until `research_papers` is populated in this "
               "environment.")
]

ENV_NOTES = [
    "This module's summarizer, plagiarism-compare, and topic-categorisation features operate on caller-supplied "
    "text directly and on locally-shipped pickled indices (models/trained_topic_classifier, "
    "models/trained_plagiarism_analyzer, data/papers_raw_sliit.json + paper_embeddings.npy for the 4,219-paper "
    "SLIIT index) — none of these depend on the live Supabase corpus tables, so they were all fully testable "
    "with genuine evidence.",
    "The two endpoints that DO depend on live Supabase tables — the legacy /data/plagiarism-trends (table "
    "`plagiarism_trends`) and /data/quality (table `research_papers`) — found those tables empty (0 rows each) "
    "in this environment. The former has a documented, verified-working local-corpus fallback (M3-10); the "
    "latter (M3-14) has no such fallback and is marked BLOCKED pending real corpus data.",
    "Per team decision, the /data/scrape pipeline-trigger endpoint (which kicks off a real external scraping job "
    "against arXiv/Semantic Scholar) was not exercised live in this session, since running it would write real "
    "scraped rows into the database and consume external API quota outside the scope of a read-only validation "
    "pass.",
]

KEY_FINDINGS = [
    ("Medium", "The topic classifier (TF-IDF + One-vs-Rest LogReg, 80 labels) shows a clear, reproducible bias "
     "toward CS/technical topics — genuinely on-topic business and health abstracts both returned empty category "
     "lists at the default 0.2 threshold, even though the SBERT-based related-paper retrieval for the same input "
     "correctly surfaced highly relevant corpus papers (M3-02, M3-03)."),
    ("Medium", "Cross-module-corroborated evidence of duplicate paper records in the underlying SLIIT corpus "
     "(exact-1.0 self-similarity in plagiarism trend buckets, M3-10; the same paper title/abstract appearing "
     "under two different IDs in Module 2's Semantic Scholar profile test) — a data-quality issue that could "
     "inflate false plagiarism signals."),
    ("Low", "One sentence categorisation nuance in the summarizer (an opening \"this paper presents...\" sentence "
     "tagged \"conclusion\" via a regex keyword collision) — minor, doesn't materially affect summary quality "
     "(M3-05)."),
    ("Low", "Data Quality Metrics endpoint cannot be validated end-to-end because its backing table is empty in "
     "this environment — code logic verified sound by inspection only (M3-14)."),
]

NARRATIVE = (
    "Module 3's two most heavily-used features — the extractive Summarizer and the Plagiarism Compare pipeline — "
    "are both strongly validated: the summarizer correctly scales output length and categorises content into "
    "sections with high accuracy, and plagiarism comparison was tested and confirmed accurate at both extremes of "
    "the similarity spectrum (near-identical text scoring 0.987/\"high\", unrelated text scoring ~0/\"minimal\"). "
    "The SBERT-based related-paper retrieval used across categorisation and plagiarism-trend search is "
    "consistently excellent regardless of domain. The one clear weakness found is the topic classifier itself: "
    "it has strong precision for CS/technical content but produces empty or near-empty category lists for "
    "genuinely relevant business and health-domain text, a pattern that reproduced identically across two "
    "independent test cases and is corroborated by the classifier's own 80-label vocabulary being visibly "
    "CS-dominated. A secondary, cross-module-corroborated finding — apparent duplicate paper records in the "
    "underlying corpus — is worth a dedicated deduplication pass, since it could distort both plagiarism-trend "
    "statistics and any downstream analytics that count papers per topic. The Data Quality endpoint could not be "
    "validated against real data in this environment and should be re-run once the corpus is populated."
)

if __name__ == "__main__":
    build_workbook(
        "Module3_Data_Validation_Report.xlsx",
        3, "Research Data Collection & Management", "N. V. Hewamanne",
        "services/module3-data (FastAPI, port 8003)",
        ROWS, ENV_NOTES, KEY_FINDINGS, NARRATIVE,
    )
