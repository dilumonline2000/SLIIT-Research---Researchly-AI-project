# Module 2 — Collaboration & Recommendation

Locally-trained supervisor matching plus three new student-facing flows:
**Peer Connect** (research groups), **Feedback** (supervisor ratings), and
**Effectiveness** (rated supervisor directory).

All flows run fully offline except the optional aspect-based sentiment
analysis on free-text feedback (Gemini, with a star-based heuristic fallback).

---

## Folder layout

```
services/module2-collaboration/
├── README.md                          ← you are here
├── README_TRAINING.md                 ← supervisor-matcher training pipeline
│
├── app/                               ← FastAPI runtime
│   ├── main.py
│   ├── routers/
│   │   ├── supervisor.py              /matching/supervisors  (SBERT)
│   │   ├── peer.py                    /matching/peers (legacy)
│   │   │                              /matching/groups (NEW: form + dashboard)
│   │   │                              /matching/groups/{id}/join-request (NEW)
│   │   ├── feedback.py                /feedback/analyze
│   │   │                              /feedback/supervisors    (NEW: dropdown source)
│   │   │                              /feedback/submit         (NEW: stars + text)
│   │   │                              /feedback/by-supervisor  (NEW)
│   │   └── effectiveness.py           /effectiveness            (NEW: list)
│   │                                  /effectiveness/by-key     (NEW: detail)
│   │                                  /effectiveness/{id}       (legacy)
│   └── services/
│       ├── supervisor_matcher.py       fine-tuned SBERT inference
│       └── supervisor_directory.py     unified SLIIT + system supervisor list (NEW)
│
├── data/                              ← training data + sample queries
│   ├── sliit_supervisors.json         74 SLIIT supervisors
│   ├── supervisors_with_embeddings.json  pre-encoded (training output)
│   ├── training_pairs.json
│   └── evaluation_results.json
│
├── training/                          ← reproducible training pipeline
│   └── train_supervisor_matcher.py
│
├── models/
│   └── supervisor_matcher/            fine-tuned SBERT weights
│
├── checkpoints/                       intermediate training artefacts
├── requirements.txt
├── Dockerfile
└── railway.toml
```

---

## What's where in the database

Stored in Supabase. New tables added in
[supabase/migrations/013_peer_groups_and_supervisor_ratings.sql](../../supabase/migrations/013_peer_groups_and_supervisor_ratings.sql):

| Table | Purpose |
|---|---|
| `supervisor_profiles` | System users acting as supervisors (existing) |
| `supervisor_matches` | Per-student supervisor recommendations (existing) |
| `peer_connections` | SBERT peer-similarity rows (existing) |
| `feedback_entries` | Free-text feedback w/ aspect sentiment (existing) |
| **`peer_groups`** | Student-formed research groups w/ open slots |
| **`peer_group_join_requests`** | Students expressing interest in a group |
| **`supervisor_ratings`** | Star + text feedback on a supervisor (system or SLIIT) |

Run the new migration in Supabase SQL Editor before using the new endpoints.

---

## Flows

### 1 · Peer Connect (research groups)
Frontend: [`apps/web/src/app/(dashboard)/collaboration/peer-connect/page.tsx`](../../apps/web/src/app/(dashboard)/collaboration/peer-connect/page.tsx)

- **Browse tab** — `GET /matching/groups?status=open` lists every open group.
- **Create tab** — `POST /matching/groups` saves a new group: project title,
  description, research area, current members, slots needed, contact email.
- **Express interest** — `POST /matching/groups/{id}/join-request` records the
  request and returns a pre-filled `mailto:` URL. The frontend opens the user's
  default mail client so the email goes from their actual mailbox to the group
  leader's contact email — **no SMTP server required**.

### 2 · Feedback (supervisor ratings)
Frontend: [`apps/web/src/app/(dashboard)/collaboration/feedback/page.tsx`](../../apps/web/src/app/(dashboard)/collaboration/feedback/page.tsx)

- **Supervisor dropdown** — `GET /feedback/supervisors` returns 74 SLIIT
  supervisors + any system users with `role='supervisor'`. Each entry has a
  composite `key` like `sliit:1` or `system:<uuid>` so the frontend can target
  either source uniformly.
- **Submit** — `POST /feedback/submit` saves `{stars: 1-5, feedback_text?}`
  under that key. If text is provided we run aspect-based sentiment analysis;
  otherwise we infer sentiment from the star rating.

### 3 · Effectiveness (rated supervisor directory)
Frontend: [`apps/web/src/app/(dashboard)/collaboration/effectiveness/page.tsx`](../../apps/web/src/app/(dashboard)/collaboration/effectiveness/page.tsx)

- **List** — `GET /effectiveness` returns every supervisor with aggregate
  stats (avg stars, n_ratings, blended effectiveness score).
- **Detail** — `GET /effectiveness/by-key?supervisor_key=sliit:1` returns the
  full effectiveness profile + recent feedback comments.
- **Contact** — every entry includes the supervisor's email, surfaced as a
  one-click `mailto:` button on the detail view AND on each list row.

The effectiveness score is a weighted blend:

```
0.40 · star_score   +
0.25 · sentiment    +
0.15 · satisfaction +
0.20 · completion_rate
```

Components are normalised to 0..1; weights re-distribute among whichever
components have data.

---

## Models at a glance

| Capability | Backing | Status |
|---|---|---|
| Supervisor matching | Fine-tuned SBERT (74 SLIIT supervisors + 65 student proposal pairs) | ✅ trained |
| Peer Connect | CRUD over Supabase + mailto URL builder | ✅ functional |
| Feedback aspect sentiment | Gemini prompt + star-based heuristic fallback | ✅ functional |
| Effectiveness scoring | SQL aggregation + weighted blend | ✅ functional |

---

## Running the service

```bash
cd services/module2-collaboration
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload
```

Health endpoint: `GET /health`

---

## Viva talking points

- **Why mailto: instead of SMTP?** Sending email from our backend would
  require a transactional-email provider (SendGrid/Resend/SES) and DNS setup
  for SPF/DKIM. The mailto: pattern lets the *user's own mail client* send
  the message — the request is still recorded server-side for audit.
- **Why a composite `supervisor_key`?** SLIIT supervisors come from a JSON
  file (id is an integer); system supervisors come from `profiles` (id is a
  UUID). The composite `<source>:<id>` key lets one frontend dropdown and one
  ratings table address both cleanly. The DB has a CHECK constraint enforcing
  exactly one of `sliit_supervisor_id` / `system_supervisor_id` is set.
- **Why blend stars + sentiment + satisfaction + completion?** Stars are a
  fast, easy signal but coarse. Sentiment captures nuance from written
  feedback. Completion rate is a behavioural signal independent of self-report.
  Blending three independent sources reduces gaming.
- **Why is feedback persisted before the email is sent?** If the user's mail
  client fails to open we still have a record of intent in
  `peer_group_join_requests`, so leaders can be alerted via a future polling
  job or in-app notification.
