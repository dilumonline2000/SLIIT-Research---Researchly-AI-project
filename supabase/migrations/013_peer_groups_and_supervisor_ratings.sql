-- =====================================================================
-- Migration 013 — Module 2: Peer groups + supervisor ratings
-- Adds three things needed by the redesigned Collaboration module:
--   1) peer_groups            : student-formed research groups with open slots
--   2) peer_group_join_requests: students expressing interest in joining
--   3) supervisor_ratings      : star rating + feedback per supervisor (system OR SLIIT)
-- All policies are permissive enough for authenticated users to read public
-- data and manage their own rows. Service role bypasses RLS as usual.
-- =====================================================================

-- ── 1. Peer groups ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.peer_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leader_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    project_title TEXT NOT NULL,
    project_description TEXT,
    research_area TEXT,
    current_members TEXT[] DEFAULT '{}',           -- free-text names
    current_member_count INTEGER NOT NULL DEFAULT 1,
    slots_needed INTEGER NOT NULL DEFAULT 1,        -- additional members wanted
    contact_email TEXT NOT NULL,
    status TEXT CHECK (status IN ('open', 'closed', 'full')) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_peer_groups_status ON public.peer_groups(status);
CREATE INDEX IF NOT EXISTS idx_peer_groups_leader ON public.peer_groups(leader_id);

ALTER TABLE public.peer_groups ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "peer_groups_select" ON public.peer_groups;
CREATE POLICY "peer_groups_select" ON public.peer_groups
    FOR SELECT USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "peer_groups_insert" ON public.peer_groups;
CREATE POLICY "peer_groups_insert" ON public.peer_groups
    FOR INSERT WITH CHECK (auth.uid() = leader_id);

DROP POLICY IF EXISTS "peer_groups_update_own" ON public.peer_groups;
CREATE POLICY "peer_groups_update_own" ON public.peer_groups
    FOR UPDATE USING (auth.uid() = leader_id);

DROP POLICY IF EXISTS "peer_groups_delete_own" ON public.peer_groups;
CREATE POLICY "peer_groups_delete_own" ON public.peer_groups
    FOR DELETE USING (auth.uid() = leader_id);


-- ── 2. Join requests ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.peer_group_join_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES public.peer_groups(id) ON DELETE CASCADE,
    requester_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    requester_name TEXT,
    requester_email TEXT NOT NULL,
    message TEXT,
    status TEXT CHECK (status IN ('pending', 'accepted', 'declined')) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_join_requests_group ON public.peer_group_join_requests(group_id);

ALTER TABLE public.peer_group_join_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "join_requests_select" ON public.peer_group_join_requests;
CREATE POLICY "join_requests_select" ON public.peer_group_join_requests
    FOR SELECT USING (
        auth.uid() = requester_id
        OR EXISTS (
            SELECT 1 FROM public.peer_groups g
            WHERE g.id = group_id AND g.leader_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "join_requests_insert" ON public.peer_group_join_requests;
CREATE POLICY "join_requests_insert" ON public.peer_group_join_requests
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);


-- ── 3. Supervisor ratings ────────────────────────────────────────────
-- Targets EITHER a system supervisor (system_supervisor_id, references profiles)
-- OR a SLIIT-dataset supervisor (sliit_supervisor_id INT). Exactly one of the
-- two columns must be non-null (enforced by CHECK).
CREATE TABLE IF NOT EXISTS public.supervisor_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Identity of the rated supervisor
    system_supervisor_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    sliit_supervisor_id INTEGER,                          -- id from sliit_supervisors.json
    sliit_supervisor_name TEXT,                           -- denormalised for ease of display
    sliit_supervisor_email TEXT,
    -- Identity of the rater
    rater_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    rater_name TEXT,
    -- The rating itself
    stars INTEGER NOT NULL CHECK (stars BETWEEN 1 AND 5),
    feedback_text TEXT,
    overall_sentiment TEXT,                               -- positive | neutral | negative
    sentiment_score REAL,                                 -- -1..1
    aspect_sentiments JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_one_supervisor CHECK (
        (system_supervisor_id IS NOT NULL AND sliit_supervisor_id IS NULL)
        OR (system_supervisor_id IS NULL AND sliit_supervisor_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_ratings_system ON public.supervisor_ratings(system_supervisor_id);
CREATE INDEX IF NOT EXISTS idx_ratings_sliit ON public.supervisor_ratings(sliit_supervisor_id);

ALTER TABLE public.supervisor_ratings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "supervisor_ratings_select" ON public.supervisor_ratings;
CREATE POLICY "supervisor_ratings_select" ON public.supervisor_ratings
    FOR SELECT USING (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "supervisor_ratings_insert" ON public.supervisor_ratings;
CREATE POLICY "supervisor_ratings_insert" ON public.supervisor_ratings
    FOR INSERT WITH CHECK (auth.uid() = rater_id);
