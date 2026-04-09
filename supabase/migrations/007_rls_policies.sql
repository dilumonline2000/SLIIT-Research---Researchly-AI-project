-- =====================================================================
-- Migration 007 — Row Level Security policies
-- =====================================================================

-- Helper: is current user supervisor or admin?
CREATE OR REPLACE FUNCTION public.is_staff()
RETURNS BOOLEAN LANGUAGE sql SECURITY DEFINER STABLE AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid()
          AND role IN ('supervisor', 'admin', 'coordinator')
    );
$$;

-- Enable RLS on all user-facing tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.plagiarism_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mind_maps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supervisor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supervisor_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.peer_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quality_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.success_predictions ENABLE ROW LEVEL SECURITY;

-- ---------- Profiles ----------
CREATE POLICY "Public profiles readable"
    ON public.profiles FOR SELECT
    USING (true);

CREATE POLICY "Users update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- ---------- Research proposals ----------
CREATE POLICY "Own proposals or staff"
    ON public.research_proposals FOR ALL
    USING (auth.uid() = user_id OR public.is_staff())
    WITH CHECK (auth.uid() = user_id OR public.is_staff());

-- ---------- Module 1 tables (user-owned) ----------
CREATE POLICY "Own citations" ON public.citations
    FOR ALL USING (auth.uid() = user_id OR public.is_staff());

CREATE POLICY "Own gaps" ON public.research_gaps
    FOR ALL USING (auth.uid() = user_id OR public.is_staff());

CREATE POLICY "Own generated proposals" ON public.generated_proposals
    FOR ALL USING (auth.uid() = user_id OR public.is_staff());

CREATE POLICY "Own plagiarism checks" ON public.plagiarism_checks
    FOR ALL USING (auth.uid() = user_id OR public.is_staff());

CREATE POLICY "Own mind maps" ON public.mind_maps
    FOR ALL USING (auth.uid() = user_id OR public.is_staff());

-- ---------- Module 2 ----------
CREATE POLICY "Supervisor profiles public read"
    ON public.supervisor_profiles FOR SELECT USING (true);

CREATE POLICY "Supervisor profiles self-update"
    ON public.supervisor_profiles FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Own supervisor matches"
    ON public.supervisor_matches FOR ALL
    USING (auth.uid() = student_id OR public.is_staff());

CREATE POLICY "Own peer connections"
    ON public.peer_connections FOR ALL
    USING (auth.uid() = student_a_id OR auth.uid() = student_b_id OR public.is_staff());

CREATE POLICY "Feedback visible to sender or recipient"
    ON public.feedback_entries FOR ALL
    USING (auth.uid() = from_user_id OR auth.uid() = to_user_id OR public.is_staff());

-- ---------- Module 4 ----------
CREATE POLICY "Own quality scores"
    ON public.quality_scores FOR ALL
    USING (auth.uid() = user_id OR public.is_staff());

CREATE POLICY "Own success predictions"
    ON public.success_predictions FOR ALL
    USING (auth.uid() = user_id OR public.is_staff());
