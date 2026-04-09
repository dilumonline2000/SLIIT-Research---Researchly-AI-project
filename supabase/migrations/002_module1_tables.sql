-- =====================================================================
-- Migration 002 — Module 1: Research Integrity & Compliance
-- Owner: K D T Kariyawasam
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    proposal_id UUID REFERENCES public.research_proposals(id) ON DELETE SET NULL,
    raw_text TEXT NOT NULL,
    parsed_entities JSONB,
    formatted_apa TEXT,
    formatted_ieee TEXT,
    is_valid BOOLEAN DEFAULT FALSE,
    confidence_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.research_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    description TEXT,
    gap_score REAL,
    supporting_papers UUID[],
    recency_score REAL,
    novelty_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.generated_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    problem_statement TEXT,
    objectives TEXT[],
    methodology TEXT,
    expected_outcomes TEXT,
    full_outline JSONB,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.plagiarism_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    overall_score REAL,
    flagged_passages JSONB[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.mind_maps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    export_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
