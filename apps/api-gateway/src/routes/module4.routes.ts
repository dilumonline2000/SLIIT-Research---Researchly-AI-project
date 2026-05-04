import { Router } from "express";
import multer from "multer";
import axios from "axios";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";
import { env } from "../config/env";
import { ApiError } from "../middleware/errorHandler";

// form-data is available transitively via axios/multer dependencies
// eslint-disable-next-line @typescript-eslint/no-require-imports
const FormData = require("form-data");

const router = Router();
router.use(requireAuth, mlRateLimiter);

// In-memory upload (max 20MB)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 },
});

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

// Success prediction file upload
router.post("/analytics/predict/upload", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) throw new ApiError(400, "No file uploaded");
    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });
    if (req.body.title) formData.append("title", req.body.title);
    if (req.body.authors) formData.append("authors", req.body.authors);
    if (req.body.year) formData.append("year", req.body.year);

    const response = await axios.post(
      `${env.MODULE4_URL}/analytics/predict/upload`,
      formData,
      {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        timeout: 60_000,
      },
    );
    res.json(response.data);
  } catch (err) {
    if (axios.isAxiosError(err)) {
      next(new ApiError(err.response?.status ?? 502, err.response?.data?.detail ?? err.message));
    } else {
      next(err);
    }
  }
});

// New: Paper analysis endpoints (using trained models)
router.post("/analytics/papers/analyze-text", async (req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/papers/analyze-text", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// File upload endpoint - proxies multipart/form-data to Module 4
router.post("/analytics/papers/upload", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) {
      throw new ApiError(400, "No file uploaded");
    }

    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });
    if (req.body.title) formData.append("title", req.body.title);
    if (req.body.authors) formData.append("authors", req.body.authors);
    if (req.body.year) formData.append("year", req.body.year);

    const response = await axios.post(
      `${env.MODULE4_URL}/analytics/papers/upload`,
      formData,
      {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
        timeout: 60_000,
      },
    );
    res.json(response.data);
  } catch (err) {
    if (axios.isAxiosError(err)) {
      next(new ApiError(
        err.response?.status ?? 502,
        err.response?.data?.detail ?? err.message,
      ));
    } else {
      next(err);
    }
  }
});

router.get("/analytics/papers/health", async (_req, res, next) => {
  try {
    const data = await callMlService(4, "/analytics/papers/health", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
