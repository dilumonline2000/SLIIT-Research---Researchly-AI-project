# Researchly AI — Deployment Guide

Target architecture for the live demo URL:

```
┌──────────────────┐      ┌─────────────────┐      ┌──────────────────────────┐
│  Vercel          │──────│  Railway         │──────│  Railway (5 services)    │
│  apps/web        │      │  api-gateway     │      │  module1-integrity       │
│  (Next.js)       │      │  (Express)       │      │  module2-collaboration   │
└──────────────────┘      └─────────────────┘      │  module3-data            │
                                                    │  module4-analytics       │
                                                    │  paper-chat              │
                                                    └──────────────────────────┘
         │                          │                         │
         └──────────────────────────┴─────────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │  Supabase Cloud    │
                          │  (Postgres +       │
                          │   pgvector + Auth) │
                          └────────────────────┘
```

---

## 1. Supabase Cloud (one-time)

The project already uses a live Supabase instance. If you need to set up a fresh one:

1. Create a project at [supabase.com](https://supabase.com), pick the closest region (e.g. `ap-south-1` for Sri Lanka).
2. Under **Database → Extensions**, enable `vector` and `pg_trgm`.
3. Run the migrations in order via the SQL editor:
   ```
   supabase/migrations/001_initial_schema.sql
   supabase/migrations/002_module1_tables.sql
   supabase/migrations/003_module2_tables.sql
   supabase/migrations/004_module3_tables.sql
   supabase/migrations/005_module4_tables.sql
   supabase/migrations/006_indexes.sql
   supabase/migrations/007_rls_policies.sql
   supabase/migrations/008_functions_realtime.sql
   supabase/migrations/009_paper_uploads.sql
   supabase/migrations/010_chat_tables.sql
   supabase/migrations/011_training_data.sql
   supabase/migrations/012_fix_chunk_embedding_nullable.sql
   supabase/migrations/013_peer_groups_and_supervisor_ratings.sql
   ```
4. Copy **Project URL**, **anon key**, **service_role key**, and **JWT secret** from Settings → API.
5. Seed the database once:
   ```bash
   export SUPABASE_URL=https://xxx.supabase.co
   export SUPABASE_SERVICE_ROLE_KEY=ey...
   python scripts/seed_supabase.py
   ```
   This creates ~10 supervisors, ~10 students, 200 papers (with SBERT embeddings), feedback, quality scores, trend forecasts.

---

## 2. Railway — API Gateway + ML services

Railway deploys each service as a separate app wired together with a private network.

### Create 6 services

In a single Railway **project**, create 6 services, each pointing at the same GitHub repo:

| Service name            | Root directory | Dockerfile path                              | Internal port |
|-------------------------|----------------|----------------------------------------------|---------------|
| `api-gateway`           | `.` (repo root)| `docker/Dockerfile.gateway`                  | 3001          |
| `module1-integrity`     | `.`            | `services/module1-integrity/Dockerfile`      | 8001          |
| `module2-collaboration` | `.`            | `services/module2-collaboration/Dockerfile`  | 8002          |
| `module3-data`          | `.`            | `services/module3-data/Dockerfile`           | 8003          |
| `module4-analytics`     | `.`            | `services/module4-analytics/Dockerfile`      | 8004          |
| `paper-chat`            | `.`            | `services/paper-chat/Dockerfile`             | 8005          |

> **Why root directory = repo root:** The Dockerfiles need access to `services/shared/` and monorepo manifests. Each service's `railway.toml` specifies the correct Dockerfile path.

### Environment variables — ALL 6 services

Paste these under **Variables** on every Railway service:

```
SUPABASE_URL=https://ecnourpfvuljdlmddfdq.supabase.co
SUPABASE_ANON_KEY=sb_publishable_846OGND_ugHXnefzWbBbsQ_eiAcPpnm
SUPABASE_SERVICE_ROLE_KEY=sb_secret_F5ZQEa1zIykd2ppC3t8p5Q_WoNPYIyx
GEMINI_API_KEY=AIzaSyCitz_J2zlu_7rgSGPxWZwaTUKEcKhJfts
GEMINI_MODEL=gemini-2.5-flash
```

### Environment variables — `api-gateway` only

```
NODE_ENV=production
API_GATEWAY_PORT=3001
LOG_LEVEL=info
SUPABASE_JWT_SECRET=98b5b2f8-604c-4f4e-9578-2838885c6b38

# Set this AFTER you get the Vercel domain
CORS_ORIGIN=https://<your-vercel-domain>.vercel.app

# Railway private network references (auto-resolved within the project)
MODULE1_URL=http://${{module1-integrity.RAILWAY_PRIVATE_DOMAIN}}:8001
MODULE2_URL=http://${{module2-collaboration.RAILWAY_PRIVATE_DOMAIN}}:8002
MODULE3_URL=http://${{module3-data.RAILWAY_PRIVATE_DOMAIN}}:8003
MODULE4_URL=http://${{module4-analytics.RAILWAY_PRIVATE_DOMAIN}}:8004
PAPER_CHAT_URL=http://${{paper-chat.RAILWAY_PRIVATE_DOMAIN}}:8005
```

### Environment variables — ML services (module1-4 + paper-chat)

```
MODEL_CACHE_DIR=/app/models
SBERT_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO

# paper-chat specific
MAX_UPLOAD_SIZE_MB=50
CHUNK_SIZE_TOKENS=512
CHUNK_OVERLAP_TOKENS=64
RAG_SIMILARITY_THRESHOLD=0.6
RAG_TOP_K_CHUNKS=8
```

### Make the gateway public

Only `api-gateway` needs a public domain. In the Railway UI for that service:
- **Settings → Networking → Generate Domain** → e.g. `researchly-gateway.up.railway.app`

### Deploy order

1. Push to the `main` branch → Railway auto-deploys all 6 services.
2. The first run pulls ML models (~420MB–1GB per service) — cold boot is slow (5-10 min).
3. Once all 6 show `Running`, verify: `https://<gateway-domain>/api/v1/health`

### Known Railway gotchas

- **Build size**: Each FastAPI service with torch + transformers is a ~3-5GB image. Upgrade to Hobby ($5/mo) if the free tier rejects large images.
- **Memory**: Module 1 and Module 4 may OOM at 512MB. Set **Resource Limits** to 1-2GB.
- **Cold starts**: Railway sleeps services after inactivity on the free tier. First request after wake-up takes 30-60s while models reload.
- **module3-data**: Installs chromium for Selenium scraping — largest build (~5GB). Consider disabling the scraping endpoints if Railway rejects it.

---

## 3. Vercel — Next.js web

### Import project

1. [vercel.com/new](https://vercel.com/new) → import the GitHub repo.
2. **Root directory**: `apps/web`
3. **Framework preset**: Next.js (auto-detected)
4. **Build command**: leave default (Vercel reads `apps/web/vercel.json`)

### Environment variables (Vercel → Settings → Environment Variables)

```
NEXT_PUBLIC_SUPABASE_URL=https://ecnourpfvuljdlmddfdq.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_846OGND_ugHXnefzWbBbsQ_eiAcPpnm
NEXT_PUBLIC_API_GATEWAY_URL=https://researchly-gateway.up.railway.app
NEXT_PUBLIC_API_URL=https://researchly-gateway.up.railway.app/api/v1
NEXT_PUBLIC_GEMINI_API_KEY=AIzaSyCitz_J2zlu_7rgSGPxWZwaTUKEcKhJfts
```

> Replace `researchly-gateway.up.railway.app` with the actual domain Railway generates for `api-gateway`.

### Deploy

Vercel auto-deploys on every push to `main`. Once deployed you get a domain like `researchly-ai.vercel.app`.

After you get the Vercel domain, go back to Railway → `api-gateway` → Variables and set:
```
CORS_ORIGIN=https://researchly-ai.vercel.app
```
Then redeploy the gateway.

---

## 4. Smoke test the live stack

```bash
# Health check
curl https://researchly-gateway.up.railway.app/api/v1/health

# Module endpoints
curl https://researchly-gateway.up.railway.app/api/v1/module1/health
curl https://researchly-gateway.up.railway.app/api/v1/module2/health
curl https://researchly-gateway.up.railway.app/api/v1/module3/health
curl https://researchly-gateway.up.railway.app/api/v1/module4/health
curl https://researchly-gateway.up.railway.app/api/v1/papers/health
```

---

## 5. Post-deploy checklist

- [ ] Visit `https://researchly-ai.vercel.app/login` and log in with a seeded user
- [ ] Every sidebar link clicks through to a real page
- [ ] Dashboard KPIs show non-zero numbers (seed script ran successfully)
- [ ] Supervisor matching returns real names (embeddings are populated)
- [ ] Paper chat: upload a PDF and ask a question — gets a real Gemini answer
- [ ] Trend forecasts render at least one topic card
- [ ] Sinhala/Tamil/Singlish chat queries return translated responses
- [ ] Sign-out redirects to `/login`

---

## Alternative: local demo with ngrok

If Railway's free tier cannot hold all 6 services:

1. Deploy `web` to Vercel as above.
2. Run services locally: `start_services.bat` (Windows) or `docker compose -f docker/docker-compose.dev.yml up`
3. Expose the gateway: `ngrok http 3001`
4. Set Vercel's `NEXT_PUBLIC_API_GATEWAY_URL` to the ngrok URL.

This lets judges browse the live Vercel frontend while compute runs on your laptop.
