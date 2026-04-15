-- Paste this in Supabase SQL Editor to fix UNRESTRICTED tables.
-- These tables need RLS enabled — they are safe to restrict because
-- the services use the service_role key which bypasses RLS anyway.

ALTER TABLE public.concept_maps        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_runs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plagiarism_trends   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_papers     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_summaries  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_categories    ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access, users read-only for public analytics tables
CREATE POLICY IF NOT EXISTS "Staff full access concept_maps"
    ON public.concept_maps FOR ALL USING (public.is_staff());

CREATE POLICY IF NOT EXISTS "Staff full access data_sources"
    ON public.data_sources FOR ALL USING (public.is_staff());

CREATE POLICY IF NOT EXISTS "Model versions readable by all authenticated"
    ON public.model_versions FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY IF NOT EXISTS "Pipeline runs readable by staff"
    ON public.pipeline_runs FOR ALL USING (public.is_staff());

CREATE POLICY IF NOT EXISTS "Plagiarism trends readable by all authenticated"
    ON public.plagiarism_trends FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY IF NOT EXISTS "Research papers readable by all authenticated"
    ON public.research_papers FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY IF NOT EXISTS "Research summaries readable"
    ON public.research_summaries FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY IF NOT EXISTS "Topic categories readable"
    ON public.topic_categories FOR SELECT USING (auth.uid() IS NOT NULL);
