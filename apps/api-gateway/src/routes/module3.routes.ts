import { Router } from "express";
import multer from "multer";
import axios from "axios";
import { requireAuth, requireRole } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";
import { env } from "../config/env";
import { ApiError } from "../middleware/errorHandler";

// eslint-disable-next-line @typescript-eslint/no-require-imports
const FormData = require("form-data");

const router = Router();
router.use(requireAuth, mlRateLimiter);

// In-memory PDF upload (max 25MB) for /summarize/upload
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 },
});

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

// PDF upload → text extraction → summarization (multipart/form-data passthrough)
router.post("/data/summarize/upload", upload.single("file"), async (req, res, next) => {
  try {
    if (!req.file) throw new ApiError(400, "No file uploaded — the 'file' field is missing.");
    if (req.file.size === 0) throw new ApiError(400, "Uploaded file is empty.");

    const formData = new FormData();
    formData.append("file", req.file.buffer, {
      filename: req.file.originalname || "paper.pdf",
      contentType: req.file.mimetype || "application/pdf",
    });
    formData.append("length", String(req.body.length || "standard"));
    if (req.body.paper_id) formData.append("paper_id", String(req.body.paper_id));

    const response = await axios.post(
      `${env.MODULE3_URL}/data/summarize/upload`,
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
      // FastAPI 422 returns { detail: [{loc, msg, type}, ...] } — flatten for the user
      let message: string;
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        message = detail.map((d: { loc?: string[]; msg?: string }) =>
          `${(d.loc || []).slice(-1)[0] || "field"}: ${d.msg}`,
        ).join("; ");
      } else if (typeof detail === "string") {
        message = detail;
      } else {
        message = err.message;
      }
      next(new ApiError(err.response?.status ?? 502, message, err.response?.data));
    } else {
      next(err);
    }
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

// ── New local-model endpoints ────────────────────────────────────────────
router.post("/data/plagiarism-trends/search", async (req, res, next) => {
  try {
    const data = await callMlService(3, "/data/plagiarism-trends/search", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/data/plagiarism-trends/compare", async (req, res, next) => {
  try {
    const data = await callMlService(3, "/data/plagiarism-trends/compare", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// Status endpoints (for Settings → Model Status grid)
router.get("/data/categorize/status", async (_req, res, next) => {
  try {
    const data = await callMlService(3, "/data/categorize/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/data/summarize/status", async (_req, res, next) => {
  try {
    const data = await callMlService(3, "/data/summarize/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/data/plagiarism-trends/status", async (_req, res, next) => {
  try {
    const data = await callMlService(3, "/data/plagiarism-trends/status", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
