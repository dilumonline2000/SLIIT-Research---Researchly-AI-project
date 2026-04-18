-- ============================================================
-- FIX: Enable RLS on ALL unrestricted tables
-- Paste in: Supabase Dashboard → SQL Editor → New query → Run
-- ============================================================
-- NOTE: Python backend services use the service_role key which
-- BYPASSES RLS automatically — these policies only restrict
-- direct anon/browser access.
-- ============================================================

-- ── 1. Enable RLS on every unrestricted table ─────────────────────────────────
ALTER TABLE public.concept_maps        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_runs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plagiarism_trends   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_papers     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_summaries  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_categories    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.training_data_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trend_forecasts     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages       ENABLE ROW LEVEL SECURITY;

-- ── 2. Drop any old/broken policies before recreating ─────────────────────────
DROP POLICY IF EXISTS "Staff full access concept_maps"                  ON public.concept_maps;
DROP POLICY IF EXISTS "Staff full access data_sources"                  ON public.data_sources;
DROP POLICY IF EXISTS "Model versions readable by all authenticated"    ON public.model_versions;
DROP POLICY IF EXISTS "Pipeline runs readable by staff"                 ON public.pipeline_runs;
DROP POLICY IF EXISTS "Plagiarism trends readable by all authenticated" ON public.plagiarism_trends;
DROP POLICY IF EXISTS "Research papers readable by all authenticated"   ON public.research_papers;
DROP POLICY IF EXISTS "Research summaries readable"                     ON public.research_summaries;
DROP POLICY IF EXISTS "Topic categories readable"                       ON public.topic_categories;

-- ── 3. concept_maps — staff read/write, users read own ────────────────────────
CREATE POLICY "concept_maps_select" ON public.concept_maps
    FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "concept_maps_insert" ON public.concept_maps
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "concept_maps_update" ON public.concept_maps
    FOR UPDATE USING (auth.uid() IS NOT NULL);

-- ── 4. data_sources — service-managed, users can read ─────────────────────────
CREATE POLICY "data_sources_select" ON public.data_sources
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 5. model_versions — service-managed, users can read ───────────────────────
CREATE POLICY "model_versions_select" ON public.model_versions
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 6. pipeline_runs — service-managed, users can read ────────────────────────
CREATE POLICY "pipeline_runs_select" ON public.pipeline_runs
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 7. plagiarism_trends — service-managed, users can read ────────────────────
CREATE POLICY "plagiarism_trends_select" ON public.plagiarism_trends
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 8. research_papers — service-managed public corpus, authenticated read ────
CREATE POLICY "research_papers_select" ON public.research_papers
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 9. research_summaries — users read summaries of their papers ──────────────
CREATE POLICY "research_summaries_select" ON public.research_summaries
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 10. topic_categories — lookup table, all authenticated can read ───────────
CREATE POLICY "topic_categories_select" ON public.topic_categories
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 11. training_data_queue — service-managed, users read own entries ─────────
CREATE POLICY "training_data_queue_select" ON public.training_data_queue
    FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY "training_data_queue_insert" ON public.training_data_queue
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- ── 12. trend_forecasts — analytics, all authenticated can read ───────────────
CREATE POLICY "trend_forecasts_select" ON public.trend_forecasts
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ── 13. chat_sessions — users manage only their own sessions ──────────────────
DROP POLICY IF EXISTS "chat_sessions_select" ON public.chat_sessions;
DROP POLICY IF EXISTS "chat_sessions_insert" ON public.chat_sessions;
DROP POLICY IF EXISTS "chat_sessions_update" ON public.chat_sessions;
DROP POLICY IF EXISTS "chat_sessions_delete" ON public.chat_sessions;

CREATE POLICY "chat_sessions_select" ON public.chat_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "chat_sessions_insert" ON public.chat_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "chat_sessions_update" ON public.chat_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "chat_sessions_delete" ON public.chat_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- ── 14. chat_messages — users access messages in their own sessions ───────────
DROP POLICY IF EXISTS "chat_messages_select" ON public.chat_messages;
DROP POLICY IF EXISTS "chat_messages_insert" ON public.chat_messages;

CREATE POLICY "chat_messages_select" ON public.chat_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.chat_sessions
            WHERE id = session_id AND user_id = auth.uid()
        )
    );

CREATE POLICY "chat_messages_insert" ON public.chat_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.chat_sessions
            WHERE id = session_id AND user_id = auth.uid()
        )
    );

-- ── Done ──────────────────────────────────────────────────────────────────────
SELECT 'All unrestricted tables now have RLS enabled.' AS result;
