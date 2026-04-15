import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { callPaperChat } from "../services/paperChatProxy.service";

const router = Router();
router.use(requireAuth);

router.get("/training/status", async (_req, res, next) => {
  try {
    const data = await callPaperChat("/training/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/training/queue", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/training/queue?${qs}` : "/training/queue";
    const data = await callPaperChat(path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/training/trigger", async (req, res, next) => {
  try {
    const qs = req.query.target_model
      ? `?target_model=${encodeURIComponent(String(req.query.target_model))}`
      : "";
    const data = await callPaperChat(`/training/trigger${qs}`, "POST");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/training/models", async (_req, res, next) => {
  try {
    const data = await callPaperChat("/training/models", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
