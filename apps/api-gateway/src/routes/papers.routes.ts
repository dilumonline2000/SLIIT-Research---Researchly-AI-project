import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callPaperChat } from "../services/paperChatProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

/**
 * The frontend uploads PDFs directly to Supabase Storage and inserts the
 * uploaded_papers row using the user's session — that path does not pass
 * through this gateway. These routes cover everything that needs the
 * backend ML service: processing pipeline, retrieval, listing, deletion.
 */

router.post("/papers/process", async (req, res, next) => {
  try {
    const data = await callPaperChat("/papers/process", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/papers", async (req, res, next) => {
  try {
    const userId = (req as { user?: { id?: string } }).user?.id;
    const params = new URLSearchParams(req.query as Record<string, string>);
    if (userId && !params.has("user_id")) params.set("user_id", userId);
    const qs = params.toString();
    const path = qs ? `/papers?${qs}` : "/papers";
    const data = await callPaperChat(path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/papers/:id", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/papers/${req.params.id}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/papers/:id/chunks", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/papers/${req.params.id}/chunks`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/papers/:id/training-data", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/papers/${req.params.id}/training-data`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/papers/:id/reprocess", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/papers/${req.params.id}/reprocess`, "POST");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.delete("/papers/:id", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/papers/${req.params.id}`, "DELETE");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
