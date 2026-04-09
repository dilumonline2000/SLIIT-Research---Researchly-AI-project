-- =====================================================================
-- Migration 008 — Helper functions + Realtime publication
-- =====================================================================

-- ---------- Similarity search: papers ----------
CREATE OR REPLACE FUNCTION public.match_papers(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (id UUID, title TEXT, abstract TEXT, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT rp.id, rp.title, rp.abstract,
           1 - (rp.embedding <=> query_embedding) AS similarity
    FROM public.research_papers rp
    WHERE rp.embedding IS NOT NULL
      AND 1 - (rp.embedding <=> query_embedding) > match_threshold
    ORDER BY rp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ---------- Similarity search: supervisors ----------
CREATE OR REPLACE FUNCTION public.match_supervisors(
    student_embedding VECTOR(768),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    similarity FLOAT,
    research_areas TEXT[],
    current_students INTEGER,
    max_students INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT sp.id, sp.user_id,
           1 - (sp.expertise_embedding <=> student_embedding) AS similarity,
           sp.research_areas, sp.current_students, sp.max_students
    FROM public.supervisor_profiles sp
    WHERE sp.availability = TRUE
      AND sp.expertise_embedding IS NOT NULL
    ORDER BY sp.expertise_embedding <=> student_embedding
    LIMIT match_count;
END;
$$;

-- ---------- Similarity search: peers ----------
CREATE OR REPLACE FUNCTION public.match_peers(
    student_id UUID,
    query_embedding VECTOR(768),
    match_count INT DEFAULT 10
)
RETURNS TABLE (peer_id UUID, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT rp.user_id AS peer_id,
           1 - (rp.embedding <=> query_embedding) AS similarity
    FROM public.research_proposals rp
    WHERE rp.user_id != student_id
      AND rp.embedding IS NOT NULL
    ORDER BY rp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ---------- Auto-create profile on signup ----------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'role', 'student')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ---------- Realtime publication for dashboards ----------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'quality_scores'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.quality_scores;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'success_predictions'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.success_predictions;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'trend_forecasts'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.trend_forecasts;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND tablename = 'feedback_entries'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.feedback_entries;
    END IF;
END $$;
