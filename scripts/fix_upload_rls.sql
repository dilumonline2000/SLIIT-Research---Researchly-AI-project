-- ============================================================
-- FIX: Paper Upload RLS + Storage Policies
-- Paste this entire script into: Supabase Dashboard > SQL Editor
-- ============================================================

-- ── 1. Ensure uploaded_papers table exists (safe if already exists) ─────────
CREATE TABLE IF NOT EXISTS public.uploaded_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type TEXT DEFAULT 'application/pdf',
    page_count INTEGER,
    title TEXT,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    publication_year INTEGER,
    venue TEXT,
    doi TEXT,
    references_list JSONB,
    extracted_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    processing_status TEXT CHECK (processing_status IN (
        'uploading','extracting','chunking','embedding','indexing','ready','failed'
    )) DEFAULT 'uploading',
    processing_error TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    embedding VECTOR(768),
    used_by_modules TEXT[] DEFAULT '{}',
    is_training_data BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.uploaded_papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type TEXT DEFAULT 'other',
    page_start INTEGER,
    page_end INTEGER,
    section_heading TEXT,
    embedding VECTOR(768) NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── 2. Enable RLS ─────────────────────────────────────────────────────────────
ALTER TABLE public.uploaded_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_chunks    ENABLE ROW LEVEL SECURITY;

-- ── 3. Drop & recreate uploaded_papers policies (WITH CHECK for INSERT) ───────
DROP POLICY IF EXISTS "Users manage own papers"  ON public.uploaded_papers;
DROP POLICY IF EXISTS "uploaded_papers_select"   ON public.uploaded_papers;
DROP POLICY IF EXISTS "uploaded_papers_insert"   ON public.uploaded_papers;
DROP POLICY IF EXISTS "uploaded_papers_update"   ON public.uploaded_papers;
DROP POLICY IF EXISTS "uploaded_papers_delete"   ON public.uploaded_papers;

CREATE POLICY "uploaded_papers_select" ON public.uploaded_papers
    FOR SELECT USING (auth.uid() = user_id OR is_public = TRUE);

CREATE POLICY "uploaded_papers_insert" ON public.uploaded_papers
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "uploaded_papers_update" ON public.uploaded_papers
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "uploaded_papers_delete" ON public.uploaded_papers
    FOR DELETE USING (auth.uid() = user_id);

-- ── 4. Drop & recreate paper_chunks policies ──────────────────────────────────
DROP POLICY IF EXISTS "Users access own chunks" ON public.paper_chunks;
DROP POLICY IF EXISTS "paper_chunks_select"     ON public.paper_chunks;

CREATE POLICY "paper_chunks_select" ON public.paper_chunks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.uploaded_papers
            WHERE id = paper_id
              AND (user_id = auth.uid() OR is_public = TRUE)
        )
    );

-- Allow service_role to insert chunks (used by paper-chat backend)
CREATE POLICY "paper_chunks_insert" ON public.paper_chunks
    FOR INSERT WITH CHECK (true);

-- ── 5. Storage bucket policies for 'research-papers' ─────────────────────────
-- Create bucket if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'research-papers',
    'research-papers',
    false,
    52428800,  -- 50 MB
    ARRAY['application/pdf','application/octet-stream']
)
ON CONFLICT (id) DO NOTHING;

-- Drop old storage policies
DROP POLICY IF EXISTS "Users upload own papers"    ON storage.objects;
DROP POLICY IF EXISTS "Users read own papers"      ON storage.objects;
DROP POLICY IF EXISTS "Users delete own papers"    ON storage.objects;
DROP POLICY IF EXISTS "research_papers_upload"     ON storage.objects;
DROP POLICY IF EXISTS "research_papers_select"     ON storage.objects;
DROP POLICY IF EXISTS "research_papers_delete"     ON storage.objects;

-- Upload: authenticated users can upload to their own folder (user_id/filename)
CREATE POLICY "research_papers_upload" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'research-papers'
        AND auth.uid() IS NOT NULL
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Read: users can read their own files
CREATE POLICY "research_papers_select" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'research-papers'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Delete: users can delete their own files
CREATE POLICY "research_papers_delete" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'research-papers'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- ── 6. Auto-create profile row when a new user signs up ──────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email,'@',1)),
        COALESCE(NEW.raw_user_meta_data->>'role', 'student')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- ── 7. Backfill profiles for existing auth users that have no profile row ─────
INSERT INTO public.profiles (id, email, full_name, role)
SELECT
    au.id,
    au.email,
    COALESCE(au.raw_user_meta_data->>'full_name', split_part(au.email,'@',1)),
    COALESCE(au.raw_user_meta_data->>'role', 'student')
FROM auth.users au
WHERE NOT EXISTS (SELECT 1 FROM public.profiles p WHERE p.id = au.id)
ON CONFLICT (id) DO NOTHING;

-- ── Done ──────────────────────────────────────────────────────────────────────
SELECT 'RLS and storage policies fixed successfully.' AS result;
