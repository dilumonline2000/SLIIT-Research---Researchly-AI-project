import { Router } from "express";
import { requireAuth } from "../middleware/auth";
import { callPaperChat } from "../services/paperChatProxy.service";

const router = Router();
router.use(requireAuth);

router.post("/language/detect", async (req, res, next) => {
  try {
    const data = await callPaperChat("/language/detect", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

router.post("/language/translate", async (req, res, next) => {
  try {
    const data = await callPaperChat("/language/translate", "POST", req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
});

export default router;
