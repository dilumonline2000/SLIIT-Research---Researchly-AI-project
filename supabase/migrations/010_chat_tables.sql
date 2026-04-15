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
