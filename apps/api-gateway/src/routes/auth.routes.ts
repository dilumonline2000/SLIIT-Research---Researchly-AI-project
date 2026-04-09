import { Router, type Response } from "express";
import { requireAuth, type AuthenticatedRequest } from "../middleware/auth";
import { supabaseAdmin } from "../config/supabase";

const router = Router();

/**
 * GET /api/v1/auth/me — return current user + profile
 * Auth is primarily handled by Supabase directly from the frontend;
 * this endpoint is for server-to-server profile lookups.
 */
router.get("/me", requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  if (!req.user) return res.status(401).json({ error: "Not authenticated" });

  const { data, error } = await supabaseAdmin
    .from("profiles")
    .select("*")
    .eq("id", req.user.id)
    .single();

  if (error) return res.status(404).json({ error: error.message });
  res.json({ user: req.user, profile: data });
});

export default router;
