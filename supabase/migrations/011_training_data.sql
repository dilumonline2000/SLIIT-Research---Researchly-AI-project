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
