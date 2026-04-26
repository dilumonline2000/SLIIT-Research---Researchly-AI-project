import { Router } from 'express';
import axios from 'axios';
import { env } from '../config/env';

const router = Router();

const PAPER_CHAT_SERVICE = env.PAPER_CHAT_URL ?? 'http://localhost:8005';

// Health check — no auth needed (called on app load)
router.get('/local/health', async (req, res) => {
  try {
    const { data } = await axios.get(`${PAPER_CHAT_SERVICE}/local/health`, {
      timeout: 4000,
    });
    res.json(data);
  } catch (err) {
    res.json({
      available: false,
      models: {},
      error: 'Local service unreachable',
    });
  }
});

// Chat endpoint — requires auth, proxies SSE stream
router.post('/local/chat', async (req, res) => {
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
  } catch (err: any) {
    res.status(500).json({ error: 'Local model inference failed' });
  }
});

export default router;
