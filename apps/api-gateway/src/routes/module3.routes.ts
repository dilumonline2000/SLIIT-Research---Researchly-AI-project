import { Router } from "express";
import { requireAuth, requireRole } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

// Scraping is a privileged operation — admin/coordinator only.
router.post("/data/scrape", requireRole("admin", "coordinator"), async (req, res, next) => {
  try {
    const data = await callMlService(3, "/data/scrape", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/data/scrape/:jobId", async (req, res, next) => {
  try {
    const data = await callMlService(3, `/data/scrape/${req.params.jobId}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/data/plagiarism-trends", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/data/plagiarism-trends?${qs}` : "/data/plagiarism-trends";
    const data = await callMlService(3, path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/data/categorize", async (req, res, next) => {
  try {
    const data = await callMlService(3, "/data/categorize", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/data/summarize", async (req, res, next) => {
  try {
    const data = await callMlService(3, "/data/summarize", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/data/quality", async (_req, res, next) => {
  try {
    const data = await callMlService(3, "/data/quality", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
