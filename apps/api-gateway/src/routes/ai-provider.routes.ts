import { Router } from 'express';
import axios from 'axios';
import { env } from '../config/env';

const router = Router();

// ── helpers ──────────────────────────────────────────────────────────────────

async function safeGet(url: string, timeout = 4000): Promise<unknown> {
  try {
    const { data } = await axios.get(url, { timeout });
    return data;
  } catch {
    return null;
  }
}

function modelEntry(loaded: boolean, version = 'v1.0', description = ''): object {
  return { loaded, version: loaded ? version : 'not trained', description };
}

// ── Aggregate real model status from deployed ML services ─────────────────────
// This replaces the paper-chat proxy so the Settings page shows accurate status.
router.get('/local/health', async (_req, res) => {
  const [m1Health, m2Health, m3Health, m4Health] = await Promise.all([
    safeGet(`${env.MODULE1_URL}/health`),
    safeGet(`${env.MODULE2_URL}/health`),
    safeGet(`${env.MODULE3_URL}/health`),
    safeGet(`${env.MODULE4_URL}/health`),
  ]);

  // Module 4 embeds full model status in its /health response
  const m4 = (m4Health as { models?: Record<string, { loaded?: boolean; version?: string }> } | null);
  const m4models = m4?.models ?? {};

  const m4Loaded = (key: string) => m4models[key]?.loaded ?? false;
  const m4Ver = (key: string) => m4models[key]?.version ?? 'v1.0';

  // Also check module1 gap / proposal index status
  const [gapStatus, propStatus] = await Promise.all([
    safeGet(`${env.MODULE1_URL}/gaps/status`),
    safeGet(`${env.MODULE1_URL}/proposals/status`),
  ]);

  const gapLoaded   = (gapStatus as { loaded?: boolean } | null)?.loaded ?? false;
  const propLoaded  = (propStatus as { loaded?: boolean } | null)?.loaded ?? false;
  const m1Up = m1Health !== null;
  const m2Up = m2Health !== null;
  const m3Up = m3Health !== null;

  const models: Record<string, object> = {
    // Module 1
    citation_ner:    modelEntry(m1Up, 'sliit-v1', 'spaCy NER for citation entity extraction'),
    sbert_plagiarism: modelEntry(m1Up && gapLoaded, 'all-MiniLM-L6-v2', 'SBERT for plagiarism & gap analysis'),
    proposal_llm:    modelEntry(m1Up && propLoaded, 'v1.0', 'Proposal retrieval index'),

    // Module 2
    supervisor_matcher: modelEntry(m2Up, 'all-MiniLM-L6-v2', 'SBERT for supervisor-student matching'),
    sentiment_bert:     modelEntry(false, 'not trained', 'BERT aspect-based sentiment (pending)'),

    // Module 3
    scibert_classifier: modelEntry(m3Up, 'v1.0', 'Topic classifier for research papers'),
    summarizer:         modelEntry(false, 'not trained', 'BART summarizer (pending)'),

    // Module 4 — live status from service
    quality_scorer:    modelEntry(m4Loaded('quality_predictor'), m4Ver('quality_predictor'), 'XGBoost quality predictor'),
    topic_classifier:  modelEntry(m4Loaded('topic_classifier'),  m4Ver('topic_classifier'),  'SBERT topic classifier'),
    trend_forecaster:  modelEntry(m4Loaded('trend_forecaster'),  m4Ver('trend_forecaster'),  'ARIMA trend forecaster'),
    success_predictor: modelEntry(m4Loaded('success_predictor'), m4Ver('success_predictor'), 'XGBoost success predictor'),

    // Shared (paper-chat RAG — not yet deployed)
    sbert:      modelEntry(false, 'not trained', 'SBERT embeddings (paper-chat)'),
    rag_engine: modelEntry(false, 'not trained', 'RAG engine (paper-chat)'),
  };

  const loadedCount = Object.values(models).filter((m) => (m as { loaded: boolean }).loaded).length;

  res.json({
    available: loadedCount > 0,
    models,
  });
});

// Chat endpoint — proxies SSE stream to paper-chat service
router.post('/local/chat', async (req, res) => {
  const PAPER_CHAT_SERVICE = env.PAPER_CHAT_URL ?? 'http://localhost:8005';
  try {
    const response = await axios.post(
      `${PAPER_CHAT_SERVICE}/local/chat`,
      req.body,
      {
        responseType: 'stream',
        headers: { 'Content-Type': 'application/json' },
        timeout: 60000,
      }
    );

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('X-Accel-Buffering', 'no');
    response.data.pipe(res);
  } catch (_err) {
    res.status(500).json({ error: 'Local model inference failed' });
  }
});

export default router;
