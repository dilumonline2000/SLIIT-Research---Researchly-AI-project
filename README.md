<div align="center">

# Researchly AI

### AI-Powered Research Assistant & Collaboration Platform

**R26-IT-116 · SLIIT Final Year Research Project**

[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-4_services-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?style=flat-square&logo=supabase)](https://supabase.com)
[![Railway](https://img.shields.io/badge/Railway-deployed-0B0D0E?style=flat-square&logo=railway)](https://railway.app)
[![Vercel](https://img.shields.io/badge/Vercel-live-000000?style=flat-square&logo=vercel)](https://web-eight-lake-39.vercel.app)

**[Live Demo](https://web-eight-lake-39.vercel.app)** · **[API Gateway](https://api-gateway-production-56f2.up.railway.app/api/v1/health)**

</div>

---

## What is Researchly AI?

Researchly AI is a full-stack, AI-powered research platform built for SLIIT students and academics. It combines **natural language processing**, **machine learning**, and **vector search** to help researchers find supervisors, analyse papers, detect plagiarism trends, predict publication success, and generate research proposals — all in one place.

Trained on **3,860+ SLIIT research papers** with models fine-tuned for the academic domain.

---

## Features

### Papers & Chat
| Feature | Description |
|---|---|
| **PDF Upload & Parsing** | Upload any research paper; full text extracted and embedded |
| **Research Chat** | Gemini-powered chat grounded in your uploaded papers |
| **Chat History** | Persistent, searchable conversation history |
| **Continuous Training** | Submit corrections to improve the AI over time |

### Module 1 — Research Integrity
| Feature | Description |
|---|---|
| **Citation Parser** | Extract and validate citations from raw text or PDFs |
| **Gap Analysis** | Identify under-researched areas using corpus-wide NLP |
| **Proposal Generator** | Auto-generate structured research proposals |
| **Mind Map** | Visualise concept relationships across your papers |

### Module 2 — Collaboration
| Feature | Description |
|---|---|
| **Supervisor Matching** | SBERT semantic matching against 80+ supervisor profiles |
| **Peer Connect** | Find peers working on related research topics |
| **Feedback Sentiment** | Analyse supervisor/peer feedback tone and intent |
| **Effectiveness Score** | Measure research collaboration effectiveness |

### Module 3 — Data Management
| Feature | Description |
|---|---|
| **Topic Categorization** | Classify papers into 7 domain buckets using SBERT |
| **Plagiarism Trends** | Cross-paper similarity trends over the SLIIT corpus |
| **Extractive Summarizer** | Point-wise summaries grouped by Background / Method / Results / Conclusion |
| **PDF Comparison** | Side-by-side semantic similarity analysis of two papers |

### Module 4 — Performance Analytics
| Feature | Description |
|---|---|
| **Paper Quality Scoring** | 4-dimensional quality score (Originality · Citations · Methodology · Clarity) |
| **Success Prediction** | XGBoost classifier — 98% accuracy, ROC-AUC 0.9994 |
| **Trend Forecasting** | ARIMA forecasts with 95% CI across 7 research domains |
| **Research Insights** | Emerging topics + recommended research directions |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Vercel (Frontend)                       │
│                    Next.js 14 App Router                     │
│              Mobile-responsive · Dark mode · SSR             │
└──────────────────────────┬───────────────────────────────────┘
                           │  HTTPS
┌──────────────────────────▼───────────────────────────────────┐
│                  Railway — API Gateway                       │
│              Express.js + TypeScript                         │
│      Auth middleware · Rate limiting · ML proxy              │
└──────┬──────────┬──────────┬──────────┬───────────────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
  │ Mod. 1 │ │ Mod. 2 │ │ Mod. 3 │ │ Mod. 4 │   Railway
  │FastAPI │ │FastAPI │ │FastAPI │ │FastAPI │   (4 services)
  │SBERT · │ │SBERT · │ │SBERT · │ │XGBoost │
  │spaCy   │ │matcher │ │ARIMA   │ │ARIMA   │
  └────┬───┘ └───┬────┘ └───┬────┘ └───┬────┘
       └─────────┴──────────┴──────────┘
                           │
              ┌────────────▼────────────┐
              │        Supabase         │
              │  PostgreSQL + pgvector  │
              │  Auth · Storage · RLS   │
              └─────────────────────────┘
```

---

## Tech Stack

**Frontend**
- Next.js 14 (App Router, RSC, SSR)
- TypeScript · Tailwind CSS · shadcn/ui
- Recharts · Zustand · React Hook Form
- Fully mobile-responsive with slide-in sidebar

**API Layer**
- Express.js + TypeScript API Gateway
- JWT auth via Supabase · CORS · rate limiting
- Per-module request proxying with configurable timeouts

**ML Services (Python)**
- FastAPI · sentence-transformers (SBERT)
- XGBoost · statsmodels (ARIMA) · scikit-learn
- PyMuPDF · spaCy · NLTK
- Pre-computed embeddings (3,860 × 384 float32) — no OOM at startup

**Database & Storage**
- Supabase PostgreSQL + pgvector (vector similarity search)
- Row-Level Security (RLS) policies
- Supabase Storage for PDF files

**Infrastructure**
- Railway (5 backend services, Dockerised)
- Vercel (Next.js frontend, edge network)
- GitHub Actions (auto-deploy on push to main)
- Docker multi-stage builds with SBERT pre-baked in image

---

## Repository Layout

```
researchly-ai/
├── apps/
│   ├── web/                  # Next.js 14 frontend
│   └── api-gateway/          # Express.js API Gateway
├── services/
│   ├── shared/               # Shared Python utilities
│   ├── module1-integrity/    # Citations · Gaps · Proposals · Plagiarism
│   ├── module2-collaboration/# Supervisor match · Peer connect · Sentiment
│   ├── module3-data/         # Categorization · Trends · Summarizer
│   └── module4-analytics/    # Quality · Predictions · Trend forecasting
├── ml/
│   ├── notebooks/            # Jupyter training experiments
│   ├── training/             # Model training scripts
│   └── evaluation/           # Evaluation & benchmarks
├── supabase/
│   └── migrations/           # SQL schema + pgvector + RLS
├── docker/                   # Compose files + gateway Dockerfile
├── scripts/                  # Data scraping & preprocessing
└── .github/workflows/        # CI/CD — auto-deploy to Vercel + Railway
```

---

## ML Models

| Model | Task | Accuracy |
|---|---|---|
| SBERT (fine-tuned) | Supervisor & paper similarity | — |
| XGBoost Classifier | Research success prediction | 98% · AUC 0.9994 |
| ARIMA (×7 topics) | Research trend forecasting | RMSE < 5 |
| SBERT Topic Classifier | 7-class domain classification | — |
| Extractive Summarizer | Point-wise paper summarization | Grounded |
| Plagiarism Analyzer | Cross-paper similarity trends | — |
| Gap Detector | Research gap identification | — |
| Proposal Generator | Structured proposal synthesis | — |

---

## Team

| Member | Module | Responsibility |
|---|---|---|
| **K D T Kariyawasam** | Module 1 — Research Integrity | Citations · Gap Analysis · Proposals · Mind Maps |
| **S P U Gunathilaka** | Module 2 — Collaboration | Supervisor Matching · Peer Connect · Sentiment |
| **N V Hewamanne** | Module 3 — Data Management | Categorization · Trends · Summarizer · PDF Compare |
| **H W S S Jayasundara** | Module 4 — Analytics | Quality Scoring · Success Prediction · Forecasting |

---

## Getting Started (Local)

**Prerequisites:** Node ≥ 18.17, pnpm ≥ 9, Python ≥ 3.10, Docker Desktop, Supabase account

```bash
# 1. Clone and install JS dependencies
git clone https://github.com/dilumonline2000/SLIIT-Research---Researchly-AI-project.git
cd SLIIT-Research---Researchly-AI-project
pnpm install

# 2. Set up environment variables
cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

# 3. Apply database migrations
pnpm db:migrate

# 4. Start frontend + API gateway
pnpm dev
# → http://localhost:3000 (frontend)
# → http://localhost:3001 (API gateway)

# 5. Start Python ML services (new terminal)
pnpm dev:ml
# → Module 1: http://localhost:8001
# → Module 2: http://localhost:8002
# → Module 3: http://localhost:8003
# → Module 4: http://localhost:8004
```

---

## Deployment

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | [web-eight-lake-39.vercel.app](https://web-eight-lake-39.vercel.app) |
| API Gateway | Railway | api-gateway-production-56f2.up.railway.app |
| Module 1 — Integrity | Railway | module1-integrity-production.up.railway.app |
| Module 2 — Collaboration | Railway | module2-collaboration-production.up.railway.app |
| Module 3 — Data | Railway | module3-data-production.up.railway.app |
| Module 4 — Analytics | Railway | module4-analytics-production.up.railway.app |

Auto-deploy is configured via **GitHub Actions** — every push to `main` deploys all services automatically.

```bash
# Manual deploy (if needed)
cd apps/web && npx vercel --prod        # frontend
railway up --service <name> --detach   # any backend service
```

---

## License

Academic use only — SLIIT R26-IT-116 Research Project · 2025–2026
