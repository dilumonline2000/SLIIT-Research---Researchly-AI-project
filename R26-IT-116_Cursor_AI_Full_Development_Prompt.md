# 🚀 CURSOR AI MASTER PROMPT — R26-IT-116
## AI-Powered Research Paper Assistant & Collaboration Platform

> **Model:** Claude Opus 4.6 | **Project ID:** R26-IT-116 | **University:** SLIIT
> **Team:** K D T Kariyawasam, S P U Gunathilaka, N V Hewamanne, H W S S Jayasundara

---

## 🎯 PROJECT OVERVIEW

You are building a **full-stack AI-Powered Research Paper Assistant and Collaboration Platform** for university students. The platform has **4 integrated modules**, each owned by a team member. The system uses NLP, ML, and deep learning to automate citation management, research collaboration, data collection, and performance analytics.

**Tech Stack:**
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend:** Node.js + Express.js (API Gateway) + Python 3.10+ (FastAPI for ML microservices)
- **Database:** Supabase (PostgreSQL + Auth + Storage + Realtime)
- **ML/NLP:** Hugging Face Transformers, SBERT, BERTopic, SciBERT, spaCy, PyTorch
- **Visualization:** D3.js, Recharts, NetworkX
- **Vector DB:** Supabase pgvector extension (replaces Pinecone/FAISS)
- **Deployment:** Vercel (Frontend) + Railway/Render (Backend) + Supabase Cloud

---

## 📁 FOLDER STRUCTURE (Clean & Modular)

```
research-platform/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                      # GitHub Actions CI/CD
│   │   └── deploy.yml
│   └── PULL_REQUEST_TEMPLATE.md
│
├── apps/
│   ├── web/                            # Next.js 14 Frontend (App Router)
│   │   ├── public/
│   │   │   ├── assets/
│   │   │   │   ├── images/
│   │   │   │   └── icons/
│   │   │   └── favicon.ico
│   │   ├── src/
│   │   │   ├── app/                    # Next.js App Router
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/page.tsx
│   │   │   │   │   ├── register/page.tsx
│   │   │   │   │   └── layout.tsx
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── layout.tsx
│   │   │   │   │   ├── page.tsx                    # Main Dashboard
│   │   │   │   │   ├── citations/                  # Module 1 Pages
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── parser/page.tsx
│   │   │   │   │   │   ├── gaps/page.tsx
│   │   │   │   │   │   ├── proposal/page.tsx
│   │   │   │   │   │   ├── plagiarism/page.tsx
│   │   │   │   │   │   └── mindmap/page.tsx
│   │   │   │   │   ├── collaboration/              # Module 2 Pages
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── supervisor-match/page.tsx
│   │   │   │   │   │   ├── peer-connect/page.tsx
│   │   │   │   │   │   ├── feedback/page.tsx
│   │   │   │   │   │   └── effectiveness/page.tsx
│   │   │   │   │   ├── data-management/            # Module 3 Pages
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── pipeline/page.tsx
│   │   │   │   │   │   ├── categorization/page.tsx
│   │   │   │   │   │   ├── plagiarism-trends/page.tsx
│   │   │   │   │   │   └── summarizer/page.tsx
│   │   │   │   │   ├── analytics/                  # Module 4 Pages
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── trends/page.tsx
│   │   │   │   │   │   ├── quality-scores/page.tsx
│   │   │   │   │   │   ├── dashboards/page.tsx
│   │   │   │   │   │   ├── mind-maps/page.tsx
│   │   │   │   │   │   └── predictions/page.tsx
│   │   │   │   │   ├── profile/page.tsx
│   │   │   │   │   └── settings/page.tsx
│   │   │   │   ├── api/                            # Next.js API Routes (BFF)
│   │   │   │   │   └── [...proxy]/route.ts
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx                        # Landing Page
│   │   │   │   └── globals.css
│   │   │   ├── components/
│   │   │   │   ├── ui/                             # shadcn/ui components
│   │   │   │   │   ├── button.tsx
│   │   │   │   │   ├── card.tsx
│   │   │   │   │   ├── dialog.tsx
│   │   │   │   │   ├── input.tsx
│   │   │   │   │   ├── table.tsx
│   │   │   │   │   ├── tabs.tsx
│   │   │   │   │   ├── toast.tsx
│   │   │   │   │   └── ...
│   │   │   │   ├── shared/                         # Shared components
│   │   │   │   │   ├── Navbar.tsx
│   │   │   │   │   ├── Sidebar.tsx
│   │   │   │   │   ├── Footer.tsx
│   │   │   │   │   ├── FileUploader.tsx
│   │   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   │   ├── SearchBar.tsx
│   │   │   │   │   └── DataTable.tsx
│   │   │   │   ├── module1/                        # Module 1 Components
│   │   │   │   │   ├── CitationParser.tsx
│   │   │   │   │   ├── CitationFormatter.tsx
│   │   │   │   │   ├── GapAnalysisCard.tsx
│   │   │   │   │   ├── ProposalGenerator.tsx
│   │   │   │   │   ├── PlagiarismChecker.tsx
│   │   │   │   │   └── MindMapViewer.tsx
│   │   │   │   ├── module2/                        # Module 2 Components
│   │   │   │   │   ├── SupervisorCard.tsx
│   │   │   │   │   ├── MatchScoreBar.tsx
│   │   │   │   │   ├── PeerRecommendation.tsx
│   │   │   │   │   ├── SentimentChart.tsx
│   │   │   │   │   └── EffectivenessScore.tsx
│   │   │   │   ├── module3/                        # Module 3 Components
│   │   │   │   │   ├── PipelineStatus.tsx
│   │   │   │   │   ├── TopicBadge.tsx
│   │   │   │   │   ├── TrendHeatmap.tsx
│   │   │   │   │   ├── SummaryViewer.tsx
│   │   │   │   │   └── DataQualityGauge.tsx
│   │   │   │   ├── module4/                        # Module 4 Components
│   │   │   │   │   ├── TrendForecastChart.tsx
│   │   │   │   │   ├── QualityScoreCard.tsx
│   │   │   │   │   ├── InteractiveDashboard.tsx
│   │   │   │   │   ├── ResearchMindMap.tsx
│   │   │   │   │   └── SuccessPredictionAlert.tsx
│   │   │   │   └── charts/                         # Reusable chart components
│   │   │   │       ├── LineChart.tsx
│   │   │   │       ├── BarChart.tsx
│   │   │   │       ├── HeatmapChart.tsx
│   │   │   │       ├── NetworkGraph.tsx
│   │   │   │       └── ForceDirectedGraph.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useSupabase.ts
│   │   │   │   ├── useRealtime.ts
│   │   │   │   ├── useFileUpload.ts
│   │   │   │   └── useDebounce.ts
│   │   │   ├── lib/
│   │   │   │   ├── supabase/
│   │   │   │   │   ├── client.ts
│   │   │   │   │   ├── server.ts
│   │   │   │   │   ├── middleware.ts
│   │   │   │   │   └── types.ts
│   │   │   │   ├── api.ts                          # Axios/fetch wrapper
│   │   │   │   ├── utils.ts
│   │   │   │   └── constants.ts
│   │   │   ├── stores/                             # Zustand state management
│   │   │   │   ├── authStore.ts
│   │   │   │   ├── citationStore.ts
│   │   │   │   ├── collaborationStore.ts
│   │   │   │   ├── dataStore.ts
│   │   │   │   └── analyticsStore.ts
│   │   │   └── types/
│   │   │       ├── index.ts
│   │   │       ├── citation.ts
│   │   │       ├── collaboration.ts
│   │   │       ├── data-management.ts
│   │   │       └── analytics.ts
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── package.json
│   │   └── .env.local.example
│   │
│   └── api-gateway/                    # Node.js + Express API Gateway
│       ├── src/
│       │   ├── index.ts
│       │   ├── config/
│       │   │   ├── supabase.ts
│       │   │   ├── cors.ts
│       │   │   └── env.ts
│       │   ├── middleware/
│       │   │   ├── auth.ts                         # Supabase JWT verification
│       │   │   ├── rateLimiter.ts
│       │   │   ├── errorHandler.ts
│       │   │   ├── validator.ts
│       │   │   └── logger.ts
│       │   ├── routes/
│       │   │   ├── index.ts
│       │   │   ├── auth.routes.ts
│       │   │   ├── module1.routes.ts               # Citation & Integrity routes
│       │   │   ├── module2.routes.ts               # Collaboration routes
│       │   │   ├── module3.routes.ts               # Data Management routes
│       │   │   ├── module4.routes.ts               # Analytics routes
│       │   │   └── common.routes.ts                # File upload, profile, etc.
│       │   ├── controllers/
│       │   │   ├── auth.controller.ts
│       │   │   ├── citation.controller.ts
│       │   │   ├── collaboration.controller.ts
│       │   │   ├── dataManagement.controller.ts
│       │   │   ├── analytics.controller.ts
│       │   │   └── upload.controller.ts
│       │   ├── services/
│       │   │   ├── supabase.service.ts
│       │   │   ├── mlProxy.service.ts              # Proxy to Python ML services
│       │   │   ├── storage.service.ts
│       │   │   └── notification.service.ts
│       │   └── utils/
│       │       ├── response.ts
│       │       └── validators.ts
│       ├── tsconfig.json
│       ├── package.json
│       └── .env.example
│
├── services/                           # Python ML Microservices
│   ├── shared/                         # Shared Python utilities
│   │   ├── __init__.py
│   │   ├── supabase_client.py
│   │   ├── embedding_utils.py
│   │   ├── preprocessing.py
│   │   └── config.py
│   │
│   ├── module1-integrity/              # Research Integrity & Compliance
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                             # FastAPI entrypoint
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── citation.py
│   │   │   │   ├── gap_analysis.py
│   │   │   │   ├── proposal.py
│   │   │   │   ├── plagiarism.py
│   │   │   │   └── mindmap.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── citation_parser.py              # NER-based citation extraction
│   │   │   │   ├── citation_formatter.py           # APA/IEEE formatting engine
│   │   │   │   ├── gap_identifier.py               # SBERT + BERTopic gap analysis
│   │   │   │   ├── proposal_generator.py           # RAG + LoRA fine-tuned LLM
│   │   │   │   ├── plagiarism_detector.py          # TF-IDF + SBERT similarity
│   │   │   │   └── mindmap_builder.py              # KeyBERT + NetworkX
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ner_model.py                    # spaCy NER for citations
│   │   │   │   ├── sbert_model.py                  # Sentence-BERT embeddings
│   │   │   │   └── lora_model.py                   # LoRA fine-tuned LLM
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── citation.py
│   │   │       ├── gap.py
│   │   │       ├── proposal.py
│   │   │       └── plagiarism.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   ├── module2-collaboration/          # Collaboration & Recommendation Engine
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── supervisor.py
│   │   │   │   ├── peer.py
│   │   │   │   ├── feedback.py
│   │   │   │   └── effectiveness.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── supervisor_matcher.py           # SBERT cosine similarity matching
│   │   │   │   ├── peer_recommender.py             # Hybrid CF + CBF recommendation
│   │   │   │   ├── sentiment_analyzer.py           # BERT aspect-based sentiment
│   │   │   │   ├── effectiveness_scorer.py         # Multi-dimensional scoring
│   │   │   │   └── explainer.py                    # Recommendation explanations
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sbert_matcher.py
│   │   │   │   ├── sentiment_model.py              # Fine-tuned BERT for feedback
│   │   │   │   └── collaborative_filter.py         # LightFM / Surprise models
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── supervisor.py
│   │   │       ├── peer.py
│   │   │       └── feedback.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   ├── module3-data/                   # Research Data Collection & Management
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pipeline.py
│   │   │   │   ├── categorization.py
│   │   │   │   ├── plagiarism_trends.py
│   │   │   │   ├── summarizer.py
│   │   │   │   └── quality.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── data_pipeline.py                # ETL from multiple sources
│   │   │   │   ├── topic_categorizer.py            # Fine-tuned SciBERT multi-label
│   │   │   │   ├── plagiarism_trend_analyzer.py    # SBERT pairwise similarity
│   │   │   │   ├── research_summarizer.py          # BART/T5 abstractive summary
│   │   │   │   └── quality_assurance.py            # Data completeness/consistency
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── scibert_classifier.py           # SciBERT multi-label head
│   │   │   │   ├── bertopic_model.py               # BERTopic exploratory discovery
│   │   │   │   └── summarization_model.py          # BART/T5 for summarization
│   │   │   ├── scrapers/                           # Web scraping for training data
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ieee_scraper.py                 # IEEE Xplore scraper
│   │   │   │   ├── arxiv_scraper.py                # arXiv API scraper
│   │   │   │   ├── acm_scraper.py                  # ACM Digital Library scraper
│   │   │   │   ├── sliit_scraper.py                # SLIIT repository scraper
│   │   │   │   ├── scholar_scraper.py              # Google Scholar scraper
│   │   │   │   └── base_scraper.py                 # Abstract base scraper class
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── pipeline.py
│   │   │       ├── category.py
│   │   │       └── summary.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   └── module4-analytics/              # Research Performance Analytics
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── routers/
│       │   │   ├── __init__.py
│       │   │   ├── trends.py
│       │   │   ├── quality.py
│       │   │   ├── dashboard.py
│       │   │   ├── mindmap.py
│       │   │   └── prediction.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── trend_forecaster.py             # ARIMA + Prophet ensemble
│       │   │   ├── quality_scorer.py               # Weighted multi-dimensional scoring
│       │   │   ├── dashboard_service.py            # Real-time data aggregation
│       │   │   ├── mindmap_generator.py            # GNN + KeyBERT concept maps
│       │   │   └── success_predictor.py            # RF + XGBoost risk classification
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── arima_model.py
│       │   │   ├── prophet_model.py
│       │   │   ├── gnn_model.py                    # Graph Neural Network for mind maps
│       │   │   ├── xgboost_model.py
│       │   │   └── random_forest_model.py
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── trend.py
│       │       ├── quality.py
│       │       └── prediction.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .env.example
│
├── ml/                                 # ML Training Pipelines & Data
│   ├── data/
│   │   ├── raw/                        # Raw scraped data (gitignored)
│   │   │   ├── ieee/
│   │   │   ├── arxiv/
│   │   │   ├── acm/
│   │   │   ├── sliit/
│   │   │   └── scholar/
│   │   ├── processed/                  # Cleaned & preprocessed data
│   │   │   ├── citations/
│   │   │   ├── proposals/
│   │   │   ├── feedback/
│   │   │   ├── topics/
│   │   │   └── performance/
│   │   └── embeddings/                 # Pre-computed embeddings (gitignored)
│   │
│   ├── notebooks/                      # Jupyter notebooks for exploration
│   │   ├── 01_data_exploration.ipynb
│   │   ├── 02_citation_ner_training.ipynb
│   │   ├── 03_sbert_finetuning.ipynb
│   │   ├── 04_scibert_classification.ipynb
│   │   ├── 05_sentiment_analysis.ipynb
│   │   ├── 06_trend_forecasting.ipynb
│   │   ├── 07_quality_scoring.ipynb
│   │   ├── 08_success_prediction.ipynb
│   │   ├── 09_gnn_mindmap.ipynb
│   │   └── 10_lora_finetuning.ipynb
│   │
│   ├── training/
│   │   ├── train_citation_ner.py       # spaCy NER training
│   │   ├── train_sbert.py              # SBERT fine-tuning
│   │   ├── train_scibert.py            # SciBERT multi-label classifier
│   │   ├── train_sentiment.py          # BERT sentiment fine-tuning
│   │   ├── train_summarizer.py         # BART/T5 fine-tuning
│   │   ├── train_lora_llm.py           # LoRA fine-tuning for proposals
│   │   ├── train_xgboost.py            # Success prediction model
│   │   └── train_gnn.py               # GNN for concept relationships
│   │
│   ├── evaluation/
│   │   ├── evaluate_citations.py
│   │   ├── evaluate_gaps.py
│   │   ├── evaluate_matching.py
│   │   ├── evaluate_sentiment.py
│   │   ├── evaluate_categorization.py
│   │   ├── evaluate_summarization.py
│   │   ├── evaluate_trends.py
│   │   └── evaluate_predictions.py
│   │
│   └── configs/
│       ├── citation_ner.yaml
│       ├── sbert_config.yaml
│       ├── scibert_config.yaml
│       ├── sentiment_config.yaml
│       ├── summarizer_config.yaml
│       ├── lora_config.yaml
│       ├── arima_config.yaml
│       ├── prophet_config.yaml
│       └── xgboost_config.yaml
│
├── supabase/                           # Supabase Configuration
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_module1_tables.sql
│   │   ├── 003_module2_tables.sql
│   │   ├── 004_module3_tables.sql
│   │   ├── 005_module4_tables.sql
│   │   ├── 006_vector_embeddings.sql
│   │   ├── 007_rls_policies.sql
│   │   └── 008_functions_triggers.sql
│   ├── seed.sql
│   └── config.toml
│
├── scripts/                            # Utility scripts
│   ├── scrape_research_papers.py       # Master scraping orchestrator
│   ├── preprocess_data.py
│   ├── generate_embeddings.py
│   ├── seed_database.py
│   └── setup_dev.sh
│
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── Dockerfile.gateway
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── DEPLOYMENT.md
│   └── MODULE_INTEGRATION.md
│
├── .gitignore
├── .env.example
├── turbo.json                          # Turborepo config
├── package.json                        # Root monorepo package.json
├── pnpm-workspace.yaml
└── README.md
```

---

## 🗄️ DATABASE SCHEMA (Supabase PostgreSQL)

### Enable pgvector Extension First:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Core Tables:

```sql
-- ============================================
-- CORE TABLES (Shared across all modules)
-- ============================================

-- Users & Authentication (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT CHECK (role IN ('student', 'supervisor', 'admin', 'coordinator')) DEFAULT 'student',
    department TEXT,
    faculty TEXT,
    student_id TEXT,
    bio TEXT,
    research_interests TEXT[],
    skills TEXT[],
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research Proposals
CREATE TABLE public.research_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT[],
    full_text TEXT,
    file_url TEXT,
    status TEXT CHECK (status IN ('draft', 'submitted', 'reviewed', 'approved', 'rejected')) DEFAULT 'draft',
    embedding VECTOR(768),  -- SBERT embedding for similarity search
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research Papers (scraped corpus)
CREATE TABLE public.research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    doi TEXT UNIQUE,
    source TEXT CHECK (source IN ('ieee', 'arxiv', 'acm', 'sliit', 'scholar', 'manual')),
    publication_year INTEGER,
    venue TEXT,
    citation_count INTEGER DEFAULT 0,
    full_text TEXT,
    pdf_url TEXT,
    embedding VECTOR(768),
    topic_labels TEXT[],
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MODULE 1: Research Integrity & Compliance
-- ============================================

CREATE TABLE public.citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    proposal_id UUID REFERENCES public.research_proposals(id),
    raw_text TEXT NOT NULL,
    parsed_entities JSONB,  -- {authors, title, journal, year, volume, pages, doi}
    formatted_apa TEXT,
    formatted_ieee TEXT,
    is_valid BOOLEAN DEFAULT FALSE,
    confidence_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.research_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    topic TEXT NOT NULL,
    description TEXT,
    gap_score REAL,
    supporting_papers UUID[],
    recency_score REAL,
    novelty_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.generated_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    topic TEXT NOT NULL,
    problem_statement TEXT,
    objectives TEXT[],
    methodology TEXT,
    expected_outcomes TEXT,
    full_outline JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.plagiarism_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    input_text TEXT NOT NULL,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    overall_score REAL,
    flagged_passages JSONB[],  -- [{text, matched_source, similarity_score}]
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.mind_maps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    title TEXT NOT NULL,
    nodes JSONB NOT NULL,     -- [{id, label, type, x, y}]
    edges JSONB NOT NULL,     -- [{source, target, weight, label}]
    export_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MODULE 2: Collaboration & Recommendation
-- ============================================

CREATE TABLE public.supervisor_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    publications JSONB[],
    h_index INTEGER,
    research_areas TEXT[],
    current_students INTEGER DEFAULT 0,
    max_students INTEGER DEFAULT 5,
    availability BOOLEAN DEFAULT TRUE,
    expertise_embedding VECTOR(768),
    effectiveness_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.supervisor_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES public.profiles(id),
    supervisor_id UUID REFERENCES public.supervisor_profiles(id),
    similarity_score REAL,
    multi_factor_score REAL,
    ranking INTEGER,
    match_factors JSONB,      -- {topic_sim, expertise_match, workload_factor, ...}
    explanation TEXT,
    status TEXT CHECK (status IN ('suggested', 'accepted', 'rejected')) DEFAULT 'suggested',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.peer_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_a_id UUID REFERENCES public.profiles(id),
    student_b_id UUID REFERENCES public.profiles(id),
    similarity_score REAL,
    shared_interests TEXT[],
    complementary_skills TEXT[],
    recommendation_type TEXT CHECK (recommendation_type IN ('content_based', 'collaborative', 'hybrid')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.feedback_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID REFERENCES public.profiles(id),
    to_user_id UUID REFERENCES public.profiles(id),
    proposal_id UUID REFERENCES public.research_proposals(id),
    feedback_text TEXT NOT NULL,
    overall_sentiment TEXT CHECK (overall_sentiment IN ('positive', 'neutral', 'negative')),
    sentiment_score REAL,
    aspect_sentiments JSONB,  -- {methodology, writing, originality, data_analysis}
    cycle_number INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MODULE 3: Data Collection & Management
-- ============================================

CREATE TABLE public.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    source_type TEXT CHECK (source_type IN ('api', 'scraper', 'manual', 'database')),
    base_url TEXT,
    last_sync TIMESTAMPTZ,
    records_count INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('active', 'inactive', 'error')) DEFAULT 'active',
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.topic_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.research_papers(id),
    categories TEXT[] NOT NULL,
    confidence_scores JSONB,   -- {category: score}
    model_version TEXT,
    needs_review BOOLEAN DEFAULT FALSE,
    reviewed_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.plagiarism_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_year INTEGER NOT NULL,
    topic_area TEXT,
    avg_similarity REAL,
    max_similarity REAL,
    flagged_pairs JSONB[],    -- [{paper_a, paper_b, similarity}]
    trend_direction TEXT CHECK (trend_direction IN ('increasing', 'stable', 'decreasing')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.research_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES public.research_papers(id),
    user_id UUID REFERENCES public.profiles(id),
    summary_short TEXT,
    summary_medium TEXT,
    summary_detailed TEXT,
    rouge_scores JSONB,       -- {rouge1, rouge2, rougeL}
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- MODULE 4: Performance Analytics & Visualization
-- ============================================

CREATE TABLE public.trend_forecasts (
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

CREATE TABLE public.quality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES public.research_proposals(id),
    user_id UUID REFERENCES public.profiles(id),
    overall_score REAL,
    originality_score REAL,        -- 30% weight
    citation_impact_score REAL,    -- 25% weight
    methodology_score REAL,        -- 25% weight
    clarity_score REAL,            -- 20% weight
    score_breakdown JSONB,
    expert_validated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.success_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES public.research_proposals(id),
    user_id UUID REFERENCES public.profiles(id),
    success_probability REAL,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_factors JSONB[],         -- [{factor, severity, description}]
    recommendations TEXT[],
    model_type TEXT,
    f1_score REAL,
    roc_auc REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.concept_maps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    department TEXT,
    nodes JSONB NOT NULL,         -- [{id, concept, importance, domain_cluster}]
    edges JSONB NOT NULL,         -- [{source, target, relationship_strength}]
    gnn_embedding VECTOR(128),
    filter_params JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Vector similarity search indexes (HNSW for fast ANN search)
CREATE INDEX idx_proposals_embedding ON public.research_proposals 
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_papers_embedding ON public.research_papers 
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_supervisor_embedding ON public.supervisor_profiles 
    USING hnsw (expertise_embedding vector_cosine_ops);

-- Standard indexes
CREATE INDEX idx_proposals_user ON public.research_proposals(user_id);
CREATE INDEX idx_papers_source ON public.research_papers(source);
CREATE INDEX idx_papers_year ON public.research_papers(publication_year);
CREATE INDEX idx_citations_user ON public.citations(user_id);
CREATE INDEX idx_feedback_to ON public.feedback_entries(to_user_id);
CREATE INDEX idx_matches_student ON public.supervisor_matches(student_id);
CREATE INDEX idx_quality_proposal ON public.quality_scores(proposal_id);
CREATE INDEX idx_trends_topic ON public.trend_forecasts(topic);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback_entries ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile and public profiles
CREATE POLICY "Public profiles readable" ON public.profiles
    FOR SELECT USING (true);
CREATE POLICY "Users update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Students access own proposals; supervisors/admins access all
CREATE POLICY "Own proposals" ON public.research_proposals
    FOR ALL USING (
        auth.uid() = user_id 
        OR EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('supervisor', 'admin'))
    );

-- ============================================
-- SUPABASE REALTIME (for dashboards)
-- ============================================

ALTER PUBLICATION supabase_realtime ADD TABLE public.quality_scores;
ALTER PUBLICATION supabase_realtime ADD TABLE public.success_predictions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.trend_forecasts;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Vector similarity search function
CREATE OR REPLACE FUNCTION match_papers(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (id UUID, title TEXT, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT rp.id, rp.title, 
           1 - (rp.embedding <=> query_embedding) AS similarity
    FROM public.research_papers rp
    WHERE 1 - (rp.embedding <=> query_embedding) > match_threshold
    ORDER BY rp.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Match supervisors by embedding similarity
CREATE OR REPLACE FUNCTION match_supervisors(
    student_embedding VECTOR(768),
    match_count INT DEFAULT 5
)
RETURNS TABLE (id UUID, user_id UUID, similarity FLOAT)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT sp.id, sp.user_id,
           1 - (sp.expertise_embedding <=> student_embedding) AS similarity
    FROM public.supervisor_profiles sp
    WHERE sp.availability = TRUE
    ORDER BY sp.expertise_embedding <=> student_embedding
    LIMIT match_count;
END;
$$;
```

---

## 🕷️ WEB SCRAPING — DATA COLLECTION FOR MODEL TRAINING

### Master Scraper Orchestrator (`scripts/scrape_research_papers.py`):

```
SCRAPING STRATEGY:
1. IEEE Xplore → Use ieee-xplore-api (official API, needs API key)
   - Target: 5000+ papers in CS/IT domains
   - Fields: title, authors, abstract, keywords, doi, citation_count, year
   
2. arXiv → Use arxiv Python API (free, no key needed)
   - Target: 10,000+ papers (cs.AI, cs.CL, cs.IR, cs.LG, cs.SE)
   - Fields: title, authors, abstract, categories, doi, pdf_url
   
3. ACM Digital Library → Scrape with Selenium + BeautifulSoup
   - Target: 3000+ papers
   - Fields: title, authors, abstract, keywords, doi, citation_count
   
4. SLIIT Repository → Scrape sliit.lk/research or institutional repo
   - Target: All available research proposals/theses
   - Fields: title, student, supervisor, abstract, year, department
   
5. Google Scholar → Use scholarly Python library
   - Target: Supervisor publication profiles
   - Fields: publications, h_index, citations, research_areas
   
6. Semantic Scholar → Use S2 API (free tier)
   - Target: Citation graphs and related papers
   - Fields: title, abstract, references, citations, embedding

SCRAPING RULES:
- Respect robots.txt and rate limits (1-2 req/sec)
- Use rotating user agents
- Store raw data in ml/data/raw/{source}/
- Deduplicate by DOI across sources
- Generate SBERT embeddings for all abstracts
- Store processed data + embeddings in Supabase
```

### Scraper Implementation Pattern:

Each scraper in `services/module3-data/app/scrapers/` should follow:
```python
class BaseScraper(ABC):
    def __init__(self, config):
        self.rate_limit = config.get('rate_limit', 1.0)
        self.max_papers = config.get('max_papers', 1000)
    
    @abstractmethod
    async def scrape(self, query: str, max_results: int) -> List[Paper]: ...
    
    @abstractmethod
    async def scrape_batch(self, queries: List[str]) -> List[Paper]: ...
    
    def preprocess(self, paper: Paper) -> ProcessedPaper: ...
    def generate_embedding(self, text: str) -> np.ndarray: ...
    def save_to_supabase(self, papers: List[ProcessedPaper]): ...
```

---

## 🧠 ML MODEL TRAINING INSTRUCTIONS

### MODEL 1: Citation NER (Module 1 — Kariyawasam)
```
TASK: Named Entity Recognition for bibliographic entities
BASE MODEL: spaCy en_core_web_trf (transformer-based)
TRAINING DATA: Annotated citation strings (author, title, journal, year, volume, pages, doi)
DATA SOURCE: Scraped papers formatted as citation strings + manual annotation
TRAINING:
  - Label entities in IOB format
  - Fine-tune spaCy NER pipeline
  - Train/Val/Test split: 70/15/15
TARGET METRICS:
  - Entity extraction F1-score ≥ 0.85
  - Format accuracy ≥ 90%
OUTPUT: Trained spaCy model saved to services/module1-integrity/models/
```

### MODEL 2: SBERT Fine-tuning (Shared — Modules 1,2,3)
```
TASK: Sentence embeddings for academic text similarity
BASE MODEL: sentence-transformers/all-MiniLM-L6-v2 OR allenai/scibert_scivocab_uncased
TRAINING DATA: Pairs of similar/dissimilar paper abstracts from scraped corpus
TRAINING METHOD: Contrastive learning with triplet loss
  - Anchor: paper abstract
  - Positive: paper from same topic cluster
  - Negative: paper from different topic
FINE-TUNING:
  - epochs: 10
  - batch_size: 32
  - learning_rate: 2e-5
  - warmup_steps: 100
TARGET: Improved cosine similarity correlation for academic texts
OUTPUT: Fine-tuned model for embeddings stored in Supabase pgvector
```

### MODEL 3: SciBERT Multi-label Classifier (Module 3 — Hewamanne)
```
TASK: Multi-label topic classification of research proposals
BASE MODEL: allenai/scibert_scivocab_uncased
CATEGORIES: AI, IoT, Networking, Cybersecurity, Data Science, ML, 
            Mobile Computing, Cloud Computing, Software Engineering, etc.
TRAINING DATA: Scraped papers with topic labels
ARCHITECTURE:
  - SciBERT encoder → Mean pooling → Dense(768, 512) → ReLU → Dropout(0.3) 
  - → Dense(512, num_labels) → Sigmoid (multi-label)
TRAINING:
  - epochs: 15
  - batch_size: 16
  - optimizer: AdamW
  - learning_rate: 3e-5
  - loss: BCEWithLogitsLoss
  - threshold: 0.5 for label assignment
TARGET METRICS:
  - Macro F1 ≥ 0.80
  - Precision ≥ 0.82
```

### MODEL 4: Sentiment Analysis (Module 2 — Gunathilaka)
```
TASK: Aspect-based sentiment on academic feedback
BASE MODEL: bert-base-uncased
ASPECTS: methodology, writing, originality, data_analysis
TRAINING DATA: Annotated academic feedback (real + simulated)
ARCHITECTURE:
  - BERT encoder → [CLS] token → Dense layers per aspect
  - Each aspect: 3-class (positive, neutral, negative)
TRAINING:
  - epochs: 10
  - batch_size: 16
  - learning_rate: 2e-5
TARGET METRICS:
  - Accuracy ≥ 93% (following literature benchmarks)
  - Per-aspect F1 ≥ 0.85
```

### MODEL 5: Research Summarizer (Module 3 — Hewamanne)
```
TASK: Abstractive summarization of research papers
BASE MODEL: facebook/bart-large-cnn OR google/flan-t5-base
FINE-TUNING DATA: Paper-abstract pairs from scraped corpus
TRAINING:
  - Use LoRA (rank=16, alpha=32) for parameter-efficient fine-tuning
  - epochs: 5
  - batch_size: 8
  - max_input_length: 1024
  - max_output_length: 256
TARGET METRICS:
  - ROUGE-1 ≥ 0.45
  - ROUGE-2 ≥ 0.20
  - ROUGE-L ≥ 0.35
```

### MODEL 6: Proposal Generator LLM (Module 1 — Kariyawasam)
```
TASK: Generate structured research proposal outlines
BASE MODEL: mistralai/Mistral-7B-Instruct-v0.2 OR meta-llama/Llama-2-7b-chat-hf
APPROACH: RAG (Retrieval-Augmented Generation) + LoRA fine-tuning
TRAINING DATA: Curated research proposals from SLIIT and public repos
RAG SETUP:
  - Retriever: SBERT embeddings → pgvector similarity search → Top-5 relevant papers
  - Generator: LoRA fine-tuned LLM with retrieved context
LoRA CONFIG:
  - r (rank): 16
  - lora_alpha: 32
  - target_modules: ["q_proj", "v_proj"]
  - lora_dropout: 0.05
OUTPUT FORMAT: JSON with {problem_statement, objectives[], methodology, expected_outcomes}
```

### MODEL 7: ARIMA + Prophet Ensemble (Module 4 — Jayasundara)
```
TASK: Forecast research trend popularity 6-12 months ahead
DATA: Monthly/quarterly time-series of topic frequencies from scraped papers
ARIMA:
  - Auto-parameter selection using AIC
  - Stationarity check with Augmented Dickey-Fuller test
  - Seasonal ARIMA (SARIMA) for annual patterns
PROPHET:
  - Additive model with trend + seasonality
  - Custom seasonality for academic cycles (semester-based)
ENSEMBLE:
  - Weighted average: weights determined by validation MAPE
  - Final prediction = w1*ARIMA + w2*Prophet
TARGET METRICS:
  - MAPE < 22% (78%+ accuracy)
  - Directional accuracy > 75%
```

### MODEL 8: Success Prediction (Module 4 — Jayasundara)
```
TASK: Predict research project success likelihood
MODELS: Random Forest + XGBoost (ensemble)
FEATURES:
  - Milestone completion rate
  - Engagement metrics (login frequency, submission frequency)
  - Quality score trajectory
  - Supervisor interaction frequency
  - Topic trend alignment
  - Peer collaboration score
TRAINING:
  - XGBoost: n_estimators=200, max_depth=6, learning_rate=0.1
  - Random Forest: n_estimators=300, max_depth=8
  - Ensemble: Soft voting
TARGET METRICS:
  - F1-score > 0.75
  - ROC-AUC > 0.80
```

### MODEL 9: GNN Mind Map Generator (Module 4 — Jayasundara)
```
TASK: Generate concept relationship graphs from research domains
BASE: PyTorch Geometric / DGL
ARCHITECTURE:
  - Concept extraction: KeyBERT + spaCy NER
  - Graph construction: Concepts as nodes, co-occurrence as edges
  - GCN (Graph Convolutional Network): 2-layer GCN for embedding learning
  - Visualization: D3.js force-directed layout
TRAINING:
  - Node features: SBERT embeddings of concept descriptions
  - Edge prediction: Link prediction task on knowledge graph
  - Loss: Binary cross-entropy for edge prediction
TARGET: Concept coverage > 80%, User satisfaction > 4.0/5.0
```

### MODEL 10: BERTopic (Module 3 — Hewamanne)
```
TASK: Exploratory topic discovery for emerging research themes
SETUP:
  - Embedding: SBERT
  - Dimensionality reduction: UMAP (n_neighbors=15, n_components=5)
  - Clustering: HDBSCAN (min_cluster_size=10)
  - Tokenizer: CountVectorizer with academic stop words
  - Representation: c-TF-IDF
USE: Discover new topic categories that SciBERT classifier doesn't cover
```

---

## 🔗 MODULE INTEGRATION & API CONTRACTS

```
INTEGRATION PATTERN:
- All modules communicate via REST APIs through the API Gateway
- API Gateway (Express.js) routes requests to Python ML services
- Supabase handles auth, storage, realtime subscriptions
- Frontend uses Zustand for local state + Supabase client for realtime

INTER-MODULE DATA FLOW:
1. Module 3 (Data) → feeds processed papers/embeddings to → Modules 1, 2, 4
2. Module 1 (Integrity) → sends quality metrics to → Module 4 (Analytics)
3. Module 2 (Collaboration) → sends interaction data to → Module 4 (Analytics)
4. Module 4 (Analytics) → provides trend/quality data to → Module 2 (for recommendations)
5. Module 3 (Data) → provides categorized data to → Module 4 (for mind maps)

API GATEWAY ROUTES:
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  GET    /api/v1/auth/me
  
  # Module 1
  POST   /api/v1/citations/parse          → Python module1-integrity
  POST   /api/v1/citations/format         → Python module1-integrity
  POST   /api/v1/gaps/analyze             → Python module1-integrity
  POST   /api/v1/proposals/generate       → Python module1-integrity
  POST   /api/v1/plagiarism/check         → Python module1-integrity
  POST   /api/v1/mindmaps/generate        → Python module1-integrity
  
  # Module 2
  POST   /api/v1/matching/supervisors     → Python module2-collaboration
  POST   /api/v1/matching/peers           → Python module2-collaboration
  POST   /api/v1/feedback/analyze         → Python module2-collaboration
  GET    /api/v1/effectiveness/:id        → Python module2-collaboration
  
  # Module 3
  POST   /api/v1/data/scrape             → Python module3-data
  POST   /api/v1/data/categorize         → Python module3-data
  GET    /api/v1/data/trends             → Python module3-data
  POST   /api/v1/data/summarize          → Python module3-data
  GET    /api/v1/data/quality            → Python module3-data
  
  # Module 4
  GET    /api/v1/analytics/trends         → Python module4-analytics
  POST   /api/v1/analytics/quality-score  → Python module4-analytics
  GET    /api/v1/analytics/dashboard      → Python module4-analytics
  POST   /api/v1/analytics/mindmap        → Python module4-analytics
  POST   /api/v1/analytics/predict        → Python module4-analytics
```

---

## 🛠️ DEVELOPMENT INSTRUCTIONS FOR CURSOR AI

### PHASE 1: Foundation Setup
```
1. Initialize monorepo with pnpm + Turborepo
2. Set up Next.js 14 frontend with App Router, Tailwind, shadcn/ui
3. Set up Express.js API Gateway with TypeScript
4. Configure Supabase project (create all tables, enable pgvector, set up RLS)
5. Create shared Python utilities (supabase_client.py, embedding_utils.py)
6. Set up Docker Compose for local development
7. Implement authentication flow (Supabase Auth → JWT → API Gateway middleware)
8. Build landing page + auth pages + dashboard layout with sidebar navigation
```

### PHASE 2: Data Collection & Scraping
```
1. Build all scrapers (IEEE, arXiv, ACM, SLIIT repo, Google Scholar)
2. Run scraping pipeline to collect 15,000+ research papers
3. Preprocess and clean all scraped data
4. Generate SBERT embeddings for all paper abstracts
5. Store everything in Supabase (papers table + pgvector embeddings)
6. Build Module 3 data pipeline service
```

### PHASE 3: ML Model Training
```
1. Prepare training datasets from scraped data
2. Train all 10 models (see training specs above)
3. Evaluate against target metrics
4. Save trained models and create inference endpoints in FastAPI
5. Write evaluation scripts for each model
```

### PHASE 4: Module Development (Parallel)
```
Module 1 (Kariyawasam):
  - Citation parser + formatter endpoints
  - Gap analysis with SBERT + BERTopic
  - Proposal generator with RAG pipeline
  - Plagiarism checker with TF-IDF + SBERT
  - Mind map builder with KeyBERT + NetworkX
  - Frontend pages: parser, gaps, proposal, plagiarism, mindmap

Module 2 (Gunathilaka):
  - Supervisor matching with SBERT cosine similarity
  - Peer recommendation with hybrid CF+CBF
  - Feedback sentiment analysis with fine-tuned BERT
  - Effectiveness scoring engine
  - Frontend pages: supervisor-match, peer-connect, feedback, effectiveness

Module 3 (Hewamanne):
  - Data pipeline orchestration
  - SciBERT topic categorization
  - BERTopic exploratory discovery
  - Plagiarism trend analyzer
  - Research summarizer (BART/T5)
  - Frontend pages: pipeline, categorization, plagiarism-trends, summarizer

Module 4 (Jayasundara):
  - ARIMA + Prophet trend forecasting
  - Quality scoring engine (weighted multi-dimensional)
  - D3.js interactive dashboards with WebSocket realtime
  - GNN mind map generator
  - Success prediction with RF + XGBoost
  - Frontend pages: trends, quality-scores, dashboards, mind-maps, predictions
```

### PHASE 5: Integration & Testing
```
1. Connect all modules through API Gateway
2. End-to-end testing of all workflows
3. Performance optimization (caching, lazy loading, code splitting)
4. User evaluation surveys
5. Final deployment (Vercel + Railway + Supabase Cloud)
```

---

## ⚙️ ENVIRONMENT VARIABLES TEMPLATE

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# API Gateway
API_GATEWAY_PORT=3001
JWT_SECRET=your-jwt-secret
CORS_ORIGIN=http://localhost:3000

# Python ML Services
MODULE1_URL=http://localhost:8001
MODULE2_URL=http://localhost:8002
MODULE3_URL=http://localhost:8003
MODULE4_URL=http://localhost:8004

# External APIs
IEEE_API_KEY=your-ieee-api-key
SEMANTIC_SCHOLAR_API_KEY=your-s2-key

# ML Model Paths
MODEL_CACHE_DIR=./models
SBERT_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
SCIBERT_MODEL_NAME=allenai/scibert_scivocab_uncased

# Hugging Face
HF_TOKEN=your-hugging-face-token
```

---

## 📋 IMPORTANT RULES FOR DEVELOPMENT

1. **TypeScript everywhere** — strict mode in frontend and API gateway
2. **Python type hints** — use Pydantic models for all API schemas
3. **Error handling** — never let errors crash; use try/catch with proper HTTP status codes
4. **Supabase RLS** — every table must have Row Level Security policies
5. **API validation** — use Zod (frontend), express-validator (gateway), Pydantic (Python)
6. **Git conventions** — feature branches per module: `feature/module1-citation-parser`
7. **Responsive design** — all pages must work on mobile, tablet, desktop
8. **Loading states** — every async operation must show loading indicators
9. **Dark mode** — support light/dark theme via Tailwind/shadcn
10. **Documentation** — JSDoc/docstrings on all exported functions
11. **Test coverage** — unit tests for ML services (pytest), integration tests for APIs
12. **Model versioning** — track model versions in database for reproducibility

---

## 🎨 UI/UX GUIDELINES

- **Design system:** shadcn/ui + Tailwind CSS custom theme
- **Color palette:** Professional academic theme — deep blue primary, warm accents
- **Typography:** Inter for UI, JetBrains Mono for code
- **Dashboard layout:** Collapsible sidebar + top nav + main content area
- **Charts:** Recharts for standard charts, D3.js for custom visualizations
- **Animations:** Framer Motion for page transitions and micro-interactions
- **Role-based views:** Student dashboard ≠ Supervisor dashboard ≠ Admin dashboard

---

> **START BUILDING NOW.** Follow the phases in order. Begin with Phase 1 foundation setup. Ask me if you need clarification on any module-specific implementation details.
