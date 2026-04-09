-- =====================================================================
-- Migration 004 — Module 3: Data Collection & Management
-- Owner: N V Hewamanne
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    source_type TEXT CHECK (source_type IN ('api', 'scraper', 'manual', 'database')),
    base_url TEXT,
    last_sync TIMESTAMPTZ,
    records_count INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('active', 'inactive', 'error')) DEFAULT 'active',
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.topic_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.research_papers(id) ON DELETE CASCADE,
    categories TEXT[] NOT NULL,
    confidence_scores JSONB,
    model_version TEXT,
    needs_review BOOLEAN DEFAULT FALSE,
    reviewed_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.plagiarism_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_year INTEGER NOT NULL,
    topic_area TEXT,
    avg_similarity REAL,
    max_similarity REAL,
    flagged_pairs JSONB[],
    trend_direction TEXT CHECK (trend_direction IN ('increasing', 'stable', 'decreasing')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.research_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.research_papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    summary_short TEXT,
    summary_medium TEXT,
    summary_detailed TEXT,
    rouge_scores JSONB,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES public.data_sources(id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('queued', 'running', 'success', 'failed')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    records_ingested INTEGER DEFAULT 0,
    error_message TEXT,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
