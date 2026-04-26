-- Supabase migration for SBERT supervisor matching embeddings
-- Run this in the Supabase SQL Editor before uploading embeddings
-- Creates VECTOR columns, HNSW index, and RPC function for pgvector search

-- Step 1: Add embedding-related columns to supervisor_profiles table if they don't exist
ALTER TABLE public.supervisor_profiles
  ADD COLUMN IF NOT EXISTS expertise_embedding VECTOR(384),
  ADD COLUMN IF NOT EXISTS embedding_text TEXT,
  ADD COLUMN IF NOT EXISTS model_version TEXT DEFAULT 'sbert-v1-finetuned-r26it116';

-- Step 2: Create HNSW index for fast cosine similarity search
-- This enables O(1) lookup time instead of O(n) for matching queries
CREATE INDEX IF NOT EXISTS idx_supervisor_expertise_embedding
  ON public.supervisor_profiles
  USING hnsw (expertise_embedding vector_cosine_ops)
  WITH (m=16, ef_construction=64);

-- Step 3: RPC function to match supervisors by proposal embedding
-- Called by the backend to find top-K similar supervisors
-- Drop ALL old match_supervisors functions first
DROP FUNCTION IF EXISTS match_supervisors(vector(384), integer, real) CASCADE;
DROP FUNCTION IF EXISTS match_supervisors(vector, integer, real) CASCADE;
DROP FUNCTION IF EXISTS match_supervisors(vector(384), int, float) CASCADE;

CREATE OR REPLACE FUNCTION public.match_supervisors(
    student_embedding vector(384),
    match_count integer DEFAULT 5,
    match_threshold real DEFAULT 0.30
)
RETURNS TABLE (
    id bigint,
    name text,
    email text,
    department text,
    research_cluster text,
    research_interests text[],
    availability boolean,
    current_students integer,
    max_students integer,
    similarity real
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sp.id,
        sp.name,
        sp.email,
        sp.department,
        sp.research_cluster,
        sp.research_interests,
        sp.availability,
        sp.current_students,
        sp.max_students,
        1 - (sp.expertise_embedding <=> student_embedding) AS similarity
    FROM public.supervisor_profiles sp
    WHERE
        sp.availability = TRUE
        AND sp.expertise_embedding IS NOT NULL
        AND (1 - (sp.expertise_embedding <=> student_embedding)) >= match_threshold
    ORDER BY sp.expertise_embedding <=> student_embedding
    LIMIT match_count;
END;
$$;

-- Step 4: Grant execute permission on RPC function to authenticated users
GRANT EXECUTE ON FUNCTION public.match_supervisors(vector(384), integer, real) TO authenticated;
GRANT EXECUTE ON FUNCTION public.match_supervisors(vector(384), integer, real) TO anon;

-- Done! Next step:
-- Run: python training/upload_to_supabase.py
