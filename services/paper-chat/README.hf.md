---
title: Researchly Paper Chat
emoji: 📄
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Researchly — Paper Chat & RAG Service

FastAPI service for PDF upload, multilingual RAG chat (Gemini), and continuous training.
Part of the **Researchly AI** platform (R26-IT-116 · SLIIT).

## Endpoints

| Route | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/papers/upload` | POST | Upload and chunk a PDF |
| `/chat/sessions` | POST | Create a chat session |
| `/chat/sessions/{id}/messages` | POST | Send a message (RAG) |
| `/language/detect` | POST | Detect language |
| `/training/queue` | POST | Queue a training sample |

## Environment Variables

Set these in the Space **Settings → Variables**:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `GEMINI_API_KEY` | Google Gemini API key |
