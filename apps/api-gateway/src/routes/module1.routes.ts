import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

// Citation parser + formatter
router.post("/citations/parse", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/parse", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/citations/format", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/format", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Gap analysis
router.post("/gaps/analyze", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/gaps/analyze", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Proposal generator
router.post("/proposals/generate", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/proposals/generate", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Plagiarism checker
router.post("/plagiarism/check", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/plagiarism/check", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Mind map builder
router.post("/mindmaps/generate", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/mindmaps/generate", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
