-- ============================================
-- 009 — Paper Upload & Processing
-- Adds user-uploaded research paper storage + chunked RAG retrieval.
-- All tables are additive — they do not modify existing module tables.
-- ============================================

-- Uploaded papers
CREATE TABLE IF NOT EXISTS public.uploaded_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- File info
    original_filename TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type TEXT DEFAULT 'application/pdf',
    page_count INTEGER,

    -- Extracted metadata
    title TEXT,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    publication_year INTEGER,
    venue TEXT,
    doi TEXT,
    references_list JSONB,

    -- Full extracted content as structured JSON
    extracted_data JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Processing status
    processing_status TEXT CHECK (processing_status IN (
        'uploading', 'extracting', 'chunking', 'embedding',
        'indexing', 'ready', 'failed'
    )) DEFAULT 'uploading',
    processing_error TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,

    -- Whole-paper embedding
    embedding VECTOR(768),

    -- Module associations
    used_by_modules TEXT[] DEFAULT '{}',
    is_training_data BOOLEAN DEFAULT TRUE,

    is_public BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Paper chunks (RAG retrieval)
CREATE TABLE IF NOT EXISTS public.paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.uploaded_papers(id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type TEXT CHECK (chunk_type IN (
        'abstract', 'introduction', 'methodology', 'results',
        'discussion', 'conclusion', 'references', 'other'
    )) DEFAULT 'other',

    page_start INTEGER,
    page_end INTEGER,
    section_heading TEXT,

    embedding VECTOR(768) NOT NULL,

    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_paper ON public.paper_chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON public.paper_chunks
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_user ON public.uploaded_papers(user_id);
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_embedding ON public.uploaded_papers
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_uploaded_papers_status ON public.uploaded_papers(processing_status);

-- RLS
ALTER TABLE public.uploaded_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.paper_chunks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own papers" ON public.uploaded_papers;
CREATE POLICY "Users manage own papers" ON public.uploaded_papers
    FOR ALL USING (auth.uid() = user_id OR is_public = TRUE);

DROP POLICY IF EXISTS "Users access own chunks" ON public.paper_chunks;
CREATE POLICY "Users access own chunks" ON public.paper_chunks
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.uploaded_papers
                WHERE id = paper_id AND (user_id = auth.uid() OR is_public = TRUE))
    );

-- Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.uploaded_papers;

-- Semantic search RPC across paper chunks
CREATE OR REPLACE FUNCTION search_paper_chunks(
    query_embedding VECTOR(768),
    target_paper_ids UUID[] DEFAULT NULL,
    match_threshold FLOAT DEFAULT 0.6,
    match_count INT DEFAULT 8
)
RETURNS TABLE (
    chunk_id UUID,
    paper_id UUID,
    chunk_text TEXT,
    section_heading TEXT,
    similarity FLOAT,
    paper_title TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        pc.id AS chunk_id,
        pc.paper_id,
        pc.chunk_text,
        pc.section_heading,
        1 - (pc.embedding <=> query_embedding) AS similarity,
        up.title AS paper_title
    FROM public.paper_chunks pc
    JOIN public.uploaded_papers up ON up.id = pc.paper_id
    WHERE
        up.processing_status = 'ready'
        AND 1 - (pc.embedding <=> query_embedding) > match_threshold
        AND (target_paper_ids IS NULL OR pc.paper_id = ANY(target_paper_ids))
    ORDER BY pc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
