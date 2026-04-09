-- =====================================================================
-- Migration 005 — Module 4: Performance Analytics & Visualization
-- Owner: H W S S Jayasundara
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.trend_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_value REAL,
    lower_bound REAL,
    upper_bound REAL,
    model_type TEXT CHECK (model_type IN ('arima', 'prophet', 'ensemble')),
    mape REAL,
    directional_accuracy REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.quality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES public.research_proposals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    overall_score REAL,
    originality_score REAL,
    citation_impact_score REAL,
    methodology_score REAL,
    clarity_score REAL,
    score_breakdown JSONB,
    expert_validated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.success_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES public.research_proposals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    success_probability REAL,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_factors JSONB[],
    recommendations TEXT[],
    model_type TEXT,
    f1_score REAL,
    roc_auc REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.concept_maps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    department TEXT,
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    gnn_embedding VECTOR(128),
    filter_params JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
