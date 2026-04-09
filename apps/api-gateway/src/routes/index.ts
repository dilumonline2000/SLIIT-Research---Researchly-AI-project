import { Router } from "express";
import authRoutes from "./auth.routes";
import module1Routes from "./module1.routes";
import module2Routes from "./module2.routes";
import module3Routes from "./module3.routes";
import module4Routes from "./module4.routes";

const router = Router();

router.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "api-gateway", ts: new Date().toISOString() });
});

router.use("/auth", authRoutes);
router.use(module1Routes);
router.use(module2Routes);
router.use(module3Routes);
router.use(module4Routes);

export default router;
