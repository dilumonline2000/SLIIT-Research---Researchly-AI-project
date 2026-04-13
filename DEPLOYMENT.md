# Researchly AI — Deployment Guide

Target architecture for the live demo URL:

```
┌──────────────────┐      ┌─────────────────┐      ┌─────────────────────┐
│  Vercel          │──────│  Railway         │──────│  Railway             │
│  apps/web        │      │  api-gateway     │      │  4× FastAPI services │
│  (Next.js)       │      │  (Express)       │      │  (Module 1-4)        │
└──────────────────┘      └─────────────────┘      └─────────────────────┘
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
   ```
4. Copy **Project URL**, **anon key**, **service_role key**, and **JWT secret** from Settings → API. You'll paste these into Vercel and Railway below.
5. Seed the database once:
   ```bash
   export SUPABASE_URL=https://xxx.supabase.co
   export SUPABASE_SERVICE_ROLE_KEY=ey...
   python scripts/seed_supabase.py
   ```
   This creates ~10 supervisors, ~10 students, 200 papers (with SBERT embeddings), feedback, quality scores, trend forecasts.

---

## 2. Railway — API Gateway + ML services

Railway deploys each service as a separate app, wired together with a private network.

### Create 5 services

In a single Railway **project**, create 5 services, each pointing at the same GitHub repo:

| Service name          | Root directory | Dockerfile                              | Exposed port (internal) |
|-----------------------|----------------|-----------------------------------------|-------------------------|
| `api-gateway`         | `.` (repo root)| `docker/Dockerfile.gateway`             | 3001                    |
| `module1-integrity`   | `.`            | `services/module1-integrity/Dockerfile` | 8001                    |
| `module2-collaboration` | `.`          | `services/module2-collaboration/Dockerfile` | 8002                  |
| `module3-data`        | `.`            | `services/module3-data/Dockerfile`      | 8003                    |
| `module4-analytics`   | `.`            | `services/module4-analytics/Dockerfile` | 8004                    |

> **Why root directory = repo root:** the Dockerfiles need access to `services/shared` and monorepo manifests, so the build context must be the repository root.

### Shared env vars (all services)

Paste these under **Variables** on every Railway service:

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=ey...
SUPABASE_SERVICE_ROLE_KEY=ey...
SUPABASE_JWT_SECRET=...
SBERT_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

### Gateway-only env vars

On the `api-gateway` service add:

```
NODE_ENV=production
API_GATEWAY_PORT=3001
CORS_ORIGIN=https://<your-vercel-domain>.vercel.app
LOG_LEVEL=info

MODULE1_URL=http://${{module1-integrity.RAILWAY_PRIVATE_DOMAIN}}:8001
MODULE2_URL=http://${{module2-collaboration.RAILWAY_PRIVATE_DOMAIN}}:8002
MODULE3_URL=http://${{module3-data.RAILWAY_PRIVATE_DOMAIN}}:8003
MODULE4_URL=http://${{module4-analytics.RAILWAY_PRIVATE_DOMAIN}}:8004
```

Railway's variable reference syntax (`${{...}}`) automatically resolves to the private service hostnames, so traffic stays on the internal network — no public exposure for the ML services.

### Make the gateway public

Only `api-gateway` needs a public domain. In the Railway UI for that service:
- **Settings → Networking → Generate Domain** → something like `researchly-gateway.up.railway.app`

### Deploy order

1. Push to the `main` branch → Railway auto-deploys all 5.
2. Watch the logs for `module1-integrity` — the first run pulls `sentence-transformers/all-mpnet-base-v2` (~420MB) so cold-boot is slow.
3. Once all 5 show `Running`, hit `https://<gateway-domain>/api/v1/health` to confirm.

### Known Railway gotchas

- **Build size**: Each FastAPI service with torch + transformers is a ~3-5GB image. Railway free tier may reject; upgrade to Hobby ($5/mo) or consolidate Modules 1+3 together (both use SBERT + BERTopic).
- **Memory**: Module 1 (LLM proposal generator) may OOM at 512MB. Set **Resource Limits** to 2GB+ or start with `--skip proposal_generator` in training and rely on the GPT-2 fallback at runtime.
- **Cold starts**: Railway puts services to sleep after inactivity on free tier. First request after wake-up is slow (30-60s while SBERT loads).

---

## 3. Vercel — Next.js web

### Import project

1. [vercel.com/new](https://vercel.com/new) → import your GitHub repo.
2. **Root directory**: `apps/web`
3. **Framework preset**: Next.js (auto-detected)
4. **Build command**: leave default (Vercel reads `apps/web/vercel.json`)

### Env vars (Vercel → Settings → Environment Variables)

```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=ey...
NEXT_PUBLIC_API_GATEWAY_URL=https://researchly-gateway.up.railway.app
```

### Deploy

Vercel auto-deploys on every push to `main`. Once deployed you get a domain like `researchly-ai.vercel.app` — that's the URL to send judges.

---

## 4. Smoke test the live stack

From your laptop, point the smoke test at the deployed gateway:

```bash
export GATEWAY_URL=https://researchly-gateway.up.railway.app
export SUPABASE_URL=https://xxx.supabase.co
export SUPABASE_ANON_KEY=ey...
export SMOKE_TEST_EMAIL=amaya@student.sliit.lk
export SMOKE_TEST_PASSWORD=Seeded!2026

python scripts/smoke_test.py
```

Expect ~19 test cases. A few Module 1 endpoints (proposal generator, gap analysis) may time out on first hit while models load — re-run once warm.

---

## 5. Post-deploy checklist

- [ ] Visit `https://researchly-ai.vercel.app/login` and log in with a seeded user
- [ ] Every sidebar link clicks through to a real page
- [ ] Dashboard KPIs show non-zero numbers (seed script ran successfully)
- [ ] Supervisor matching returns real names, not empty array (embeddings are populated)
- [ ] Trend forecasts render at least one topic card
- [ ] Sign-out redirects to `/login`

---

## Alternative: local demo only

If Railway's free tier can't hold all 4 services, scale back:

1. Deploy `web` + `api-gateway` to Vercel + Railway as above
2. Keep the 4 FastAPI services on your laptop: `docker compose -f docker/docker-compose.dev.yml up`
3. Use [ngrok](https://ngrok.com) to expose your gateway: `ngrok http 3001`
4. Set Vercel's `NEXT_PUBLIC_API_GATEWAY_URL` to the ngrok URL

This lets you demo the live site from judges' browsers while all compute runs on your GPU laptop.
