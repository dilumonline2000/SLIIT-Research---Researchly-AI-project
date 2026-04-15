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
-- ============================================
-- 010 — Chat & Conversations
-- RAG chatbot sessions and messages, multilingual aware.
-- ============================================

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,

    title TEXT,
    session_type TEXT CHECK (session_type IN (
        'paper_specific', 'corpus_wide', 'module_specific'
    )) DEFAULT 'paper_specific',

    paper_ids UUID[] DEFAULT '{}',
    module_context TEXT,

    preferred_language TEXT CHECK (preferred_language IN (
        'en', 'si', 'ta', 'singlish', 'auto'
    )) DEFAULT 'auto',

    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,

    role TEXT CHECK (role IN ('user', 'assistant', 'system')) NOT NULL,
    content TEXT NOT NULL,

    detected_language TEXT,
    original_content TEXT,
    response_language TEXT,

    retrieved_chunks JSONB,
    retrieval_scores JSONB,

    citations JSONB,

    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    is_helpful BOOLEAN,

    used_for_training BOOLEAN DEFAULT FALSE,
    training_batch_id TEXT,

    prompt_tokens INTEGER,
    completion_tokens INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON public.chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_training ON public.chat_messages(used_for_training)
    WHERE used_for_training = FALSE;

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own chats" ON public.chat_sessions;
CREATE POLICY "Users manage own chats" ON public.chat_sessions
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users access own messages" ON public.chat_messages;
CREATE POLICY "Users access own messages" ON public.chat_messages
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.chat_sessions
                WHERE id = session_id AND user_id = auth.uid())
    );

ALTER PUBLICATION supabase_realtime ADD TABLE public.chat_messages;
-- ============================================
-- 011 — Continuous Training Data Queue
-- Append-only queue of training samples + model version registry.
-- ============================================

CREATE TABLE IF NOT EXISTS public.training_data_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_type TEXT CHECK (source_type IN (
        'uploaded_paper', 'chat_qa', 'user_feedback',
        'paper_annotation', 'scraped_paper'
    )) NOT NULL,
    source_id UUID,

    training_data JSONB NOT NULL,

    target_models TEXT[] NOT NULL,

    status TEXT CHECK (status IN (
        'pending', 'preprocessing', 'queued', 'training',
        'completed', 'failed', 'skipped'
    )) DEFAULT 'pending',

    quality_score REAL,
    is_approved BOOLEAN DEFAULT NULL,

    batch_id TEXT,
    processed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,

    training_data_count INTEGER,
    training_started_at TIMESTAMPTZ,
    training_completed_at TIMESTAMPTZ,
    training_duration_seconds INTEGER,

    metrics JSONB,

    model_path TEXT,
    config JSONB,

    is_active BOOLEAN DEFAULT FALSE,
    is_baseline BOOLEAN DEFAULT FALSE,

    improvement_over_baseline JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_training_queue_status ON public.training_data_queue(status);
CREATE INDEX IF NOT EXISTS idx_training_queue_models ON public.training_data_queue USING GIN(target_models);
CREATE INDEX IF NOT EXISTS idx_model_versions_name ON public.model_versions(model_name);
CREATE INDEX IF NOT EXISTS idx_model_versions_active ON public.model_versions(model_name, is_active)
    WHERE is_active = TRUE;

-- Helper RPC: fetch pending data per model
CREATE OR REPLACE FUNCTION get_pending_training_data(
    target_model TEXT,
    batch_size INT DEFAULT 100
)
RETURNS TABLE (id UUID, training_data JSONB, source_type TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT tdq.id, tdq.training_data, tdq.source_type
    FROM public.training_data_queue tdq
    WHERE tdq.status = 'pending'
        AND target_model = ANY(tdq.target_models)
        AND (tdq.is_approved IS NULL OR tdq.is_approved = TRUE)
        AND (tdq.quality_score IS NULL OR tdq.quality_score > 0.3)
    ORDER BY tdq.created_at
    LIMIT batch_size;
END;
$$;
