-- =====================================================================
-- Migration 003 — Module 2: Collaboration & Recommendation
-- Owner: S P U Gunathilaka
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.supervisor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    publications JSONB[],
    h_index INTEGER,
    research_areas TEXT[],
    current_students INTEGER DEFAULT 0,
    max_students INTEGER DEFAULT 5,
    availability BOOLEAN DEFAULT TRUE,
    expertise_embedding VECTOR(768),
    effectiveness_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.supervisor_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    supervisor_id UUID REFERENCES public.supervisor_profiles(id) ON DELETE CASCADE,
    similarity_score REAL,
    multi_factor_score REAL,
    ranking INTEGER,
    match_factors JSONB,
    explanation TEXT,
    status TEXT CHECK (status IN ('suggested', 'accepted', 'rejected')) DEFAULT 'suggested',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.peer_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_a_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    student_b_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    similarity_score REAL,
    shared_interests TEXT[],
    complementary_skills TEXT[],
    recommendation_type TEXT CHECK (recommendation_type IN ('content_based', 'collaborative', 'hybrid')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_peer_pair UNIQUE (student_a_id, student_b_id)
);

CREATE TABLE IF NOT EXISTS public.feedback_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    to_user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    proposal_id UUID REFERENCES public.research_proposals(id) ON DELETE SET NULL,
    feedback_text TEXT NOT NULL,
    overall_sentiment TEXT CHECK (overall_sentiment IN ('positive', 'neutral', 'negative')),
    sentiment_score REAL,
    aspect_sentiments JSONB,
    cycle_number INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER trg_supervisor_profiles_updated_at
    BEFORE UPDATE ON public.supervisor_profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
