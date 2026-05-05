-- ============================================
-- 012 — Make paper_chunks.embedding nullable
-- The SBERT model (all-MiniLM-L6-v2) outputs 384-dim vectors but the DB
-- was created expecting 768-dim. Until the columns are migrated to 384-dim,
-- we store text chunks without vectors so papers can complete processing.
-- Gemini-based chat still works without embeddings; local RAG search requires them.
-- ============================================

-- Drop the HNSW index first (required before altering the column)
DROP INDEX IF EXISTS idx_chunks_embedding;

-- Make embedding nullable so chunks can be inserted without vectors
ALTER TABLE public.paper_chunks ALTER COLUMN embedding DROP NOT NULL;

-- Recreate HNSW index, but only on rows that actually have an embedding
-- (partial index — covers future use when we migrate to VECTOR(384))
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON public.paper_chunks
    USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;
