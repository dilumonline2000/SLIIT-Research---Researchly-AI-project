-- =====================================================================
-- Migration 001 — Initial schema: extensions + core shared tables
-- =====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------
-- Profiles (extends auth.users)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT CHECK (role IN ('student', 'supervisor', 'admin', 'coordinator')) DEFAULT 'student',
    department TEXT,
    faculty TEXT,
    student_id TEXT,
    bio TEXT,
    research_interests TEXT[],
    skills TEXT[],
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- Research proposals (owned by students)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.research_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT[],
    full_text TEXT,
    file_url TEXT,
    status TEXT CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')) DEFAULT 'draft',
    embedding VECTOR(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------
-- Research papers (scraped corpus used for training + retrieval)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    doi TEXT UNIQUE,
    source TEXT CHECK (source IN ('ieee', 'arxiv', 'acm', 'sliit', 'scholar', 'semantic_scholar', 'manual')),
    publication_year INTEGER,
    venue TEXT,
    citation_count INTEGER DEFAULT 0,
    full_text TEXT,
    pdf_url TEXT,
    embedding VECTOR(768),
    topic_labels TEXT[],
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER trg_proposals_updated_at
    BEFORE UPDATE ON public.research_proposals
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
