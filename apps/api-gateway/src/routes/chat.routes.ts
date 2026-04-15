import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callPaperChat } from "../services/paperChatProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

router.post("/chat/sessions", async (req, res, next) => {
  try {
    const userId = (req as { user?: { id?: string } }).user?.id;
    const qs = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    const data = await callPaperChat(`/chat/sessions${qs}`, "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/chat/sessions", async (req, res, next) => {
  try {
    const userId = (req as { user?: { id?: string } }).user?.id;
    const qs = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    const data = await callPaperChat(`/chat/sessions${qs}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/chat/sessions/:id", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/chat/sessions/${req.params.id}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.delete("/chat/sessions/:id", async (req, res, next) => {
  try {
    const data = await callPaperChat(`/chat/sessions/${req.params.id}`, "DELETE");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/chat/sessions/:id/message", async (req, res, next) => {
  try {
    const data = await callPaperChat(
      `/chat/sessions/${req.params.id}/message`,
      "POST",
      req.body,
    );
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/chat/sessions/:id/feedback", async (req, res, next) => {
  try {
    const data = await callPaperChat(
      `/chat/sessions/${req.params.id}/feedback`,
      "POST",
      req.body,
    );
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.patch("/chat/sessions/:id/papers", async (req, res, next) => {
  try {
    const data = await callPaperChat(
      `/chat/sessions/${req.params.id}/papers`,
      "PATCH",
      req.body,
    );
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
