import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

// ── Supervisor matching ────────────────────────────────────────────────
router.post("/matching/supervisors", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/matching/supervisors", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/matching/supervisors/:id/papers", async (req, res, next) => {
  try {
    const data = await callMlService(2, `/matching/supervisors/${req.params.id}/papers`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// ── Peer matching (legacy SBERT) ───────────────────────────────────────
router.post("/matching/peers", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/matching/peers", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// ── Peer Connect: research groups + join requests ─────────────────────
router.post("/matching/groups", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/matching/groups", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/matching/groups", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/matching/groups?${qs}` : "/matching/groups";
    const data = await callMlService(2, path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/matching/groups/:groupId", async (req, res, next) => {
  try {
    const data = await callMlService(2, `/matching/groups/${req.params.groupId}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/matching/groups/:groupId/join-request", async (req, res, next) => {
  try {
    const data = await callMlService(
      2,
      `/matching/groups/${req.params.groupId}/join-request`,
      "POST",
      req.body,
    );
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// ── Feedback / sentiment / supervisor ratings ─────────────────────────
router.post("/feedback/analyze", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/analyze", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/feedback/supervisors", async (_req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/supervisors", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/feedback/submit", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/submit", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/feedback/request-otp", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/request-otp", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/feedback/verify-otp", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/verify-otp", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/feedback/by-supervisor", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/feedback/by-supervisor?${qs}` : "/feedback/by-supervisor";
    const data = await callMlService(2, path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

// ── Effectiveness ─────────────────────────────────────────────────────
router.get("/effectiveness", async (_req, res, next) => {
  try {
    const data = await callMlService(2, "/effectiveness", "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/effectiveness/by-key", async (req, res, next) => {
  try {
    const qs = new URLSearchParams(req.query as Record<string, string>).toString();
    const path = qs ? `/effectiveness/by-key?${qs}` : "/effectiveness/by-key";
    const data = await callMlService(2, path, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.get("/effectiveness/:id", async (req, res, next) => {
  try {
    const data = await callMlService(2, `/effectiveness/${req.params.id}`, "GET");
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
