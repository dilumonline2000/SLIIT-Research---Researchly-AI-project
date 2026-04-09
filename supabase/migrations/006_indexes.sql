-- =====================================================================
-- Migration 006 — Performance indexes (HNSW for vectors + B-tree)
-- =====================================================================

-- Vector similarity search (HNSW for fast ANN)
CREATE INDEX IF NOT EXISTS idx_proposals_embedding
    ON public.research_proposals
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_papers_embedding
    ON public.research_papers
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_supervisor_embedding
    ON public.supervisor_profiles
    USING hnsw (expertise_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_concept_maps_embedding
    ON public.concept_maps
    USING hnsw (gnn_embedding vector_cosine_ops);

-- Standard B-tree indexes
CREATE INDEX IF NOT EXISTS idx_proposals_user ON public.research_proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON public.research_proposals(status);
CREATE INDEX IF NOT EXISTS idx_papers_source ON public.research_papers(source);
CREATE INDEX IF NOT EXISTS idx_papers_year ON public.research_papers(publication_year);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON public.research_papers(doi);
CREATE INDEX IF NOT EXISTS idx_citations_user ON public.citations(user_id);
CREATE INDEX IF NOT EXISTS idx_citations_proposal ON public.citations(proposal_id);
CREATE INDEX IF NOT EXISTS idx_feedback_to ON public.feedback_entries(to_user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_from ON public.feedback_entries(from_user_id);
CREATE INDEX IF NOT EXISTS idx_matches_student ON public.supervisor_matches(student_id);
CREATE INDEX IF NOT EXISTS idx_matches_supervisor ON public.supervisor_matches(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_quality_proposal ON public.quality_scores(proposal_id);
CREATE INDEX IF NOT EXISTS idx_trends_topic ON public.trend_forecasts(topic);
CREATE INDEX IF NOT EXISTS idx_trends_date ON public.trend_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_predictions_proposal ON public.success_predictions(proposal_id);

-- Full-text search on titles/abstracts (trigram)
CREATE INDEX IF NOT EXISTS idx_papers_title_trgm
    ON public.research_papers
    USING gin (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_proposals_title_trgm
    ON public.research_proposals
    USING gin (title gin_trgm_ops);
