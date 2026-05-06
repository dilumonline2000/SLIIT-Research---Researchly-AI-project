import { Router } from "express";
import multer from "multer";
import axios from "axios";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";
import { env } from "../config/env";
import { ApiError } from "../middleware/errorHandler";

// eslint-disable-next-line @typescript-eslint/no-require-imports
const FormData = require("form-data");

const router = Router();
router.use(requireAuth, mlRateLimiter);

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 },
});

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

router.post("/citations/lookup-doi", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/lookup-doi", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/citations/lookup-title", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/lookup-title", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/citations/in-text", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/in-text", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/citations/reference-list", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/reference-list", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/citations/similar-papers", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/citations/similar-papers", "POST", req.body);
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

router.post("/gaps/analyze-full-paper", async (req, res, next) => {
  try {
    const data = await callMlService(1, "/gaps/analyze-full-paper", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// PDF upload → gap analysis (multipart/form-data passthrough)
router.post("/gaps/analyze-pdf", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) throw new ApiError(400, "No file uploaded");
    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname || "paper.pdf",
      contentType: req.file.mimetype || "application/pdf",
    });
    if (req.body.top_k) formData.append("top_k", String(req.body.top_k));
    if (req.body.min_similarity) formData.append("min_similarity", String(req.body.min_similarity));
    if (req.body.year_from) formData.append("year_from", String(req.body.year_from));
    if (req.body.year_to) formData.append("year_to", String(req.body.year_to));

    const response = await axios.post(
      `${env.MODULE1_URL}/gaps/analyze-pdf`,
      formData,
      {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        timeout: 120_000,
      },
    );
    res.json(response.data);
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : (Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg ?? "invalid").join("; ")
        : err.message);
      next(new ApiError(err.response?.status ?? 502, msg, err.response?.data));
    } else {
      next(err);
    }
  }
});

router.post("/gaps/report", async (req, res, next) => {
  try {
    const response = await axios.post(
      `${env.MODULE1_URL}/gaps/report`,
      req.body,
      { responseType: "text", timeout: 30_000 },
    );
    res.setHeader("Content-Type", "text/html");
    res.send(response.data);
  } catch (err) {
    if (axios.isAxiosError(err)) {
      next(new ApiError(err.response?.status ?? 502, err.message));
    } else {
      next(err);
    }
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

// Local-model status endpoints (used by settings/model-status grid)
router.get("/gaps/status", async (_req, res, next) => {
  try {
    const data = await callMlService(1, "/gaps/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/proposals/status", async (_req, res, next) => {
  try {
    const data = await callMlService(1, "/proposals/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
