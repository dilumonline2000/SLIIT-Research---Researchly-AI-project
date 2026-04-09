import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { mlRateLimiter } from "../middleware/rateLimiter";
import { callMlService } from "../services/mlProxy.service";

const router = Router();
router.use(requireAuth, mlRateLimiter);

router.post("/matching/supervisors", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/matching/supervisors", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/matching/peers", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/matching/peers", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/feedback/analyze", async (req, res, next) => {
  try {
    const data = await callMlService(2, "/feedback/analyze", "POST", req.body);
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
