import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

router.get("/analytics/trends", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/analytics/trends?${qs}` : "/analytics/trends";
    const data = await callMlService(4, path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/analytics/quality-score", async (req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/quality-score", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/analytics/dashboard", async (_req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/dashboard", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/analytics/mindmap", async (req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/mindmap", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/analytics/predict", async (req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/predict", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
