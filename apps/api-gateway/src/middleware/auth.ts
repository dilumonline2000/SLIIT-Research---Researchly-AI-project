import type { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role?: string;
  };
}

/**
 * Verifies the Supabase-issued JWT in the Authorization header.
 * Attaches decoded user info to req.user.
 */
export function requireAuth(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction,
) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing or malformed Authorization header" });
  }

  const token = authHeader.slice(7);

  try {
    const decoded = jwt.verify(token, env.SUPABASE_JWT_SECRET) as {
      sub: string;
      email: string;
      role?: string;
      user_metadata?: { role?: string };
    };

    req.user = {
      id: decoded.sub,
      email: decoded.email,
      role: decoded.user_metadata?.role ?? decoded.role,
    };
    next();
  } catch (err) {
    return res.status(401).json({
      error: "Invalid or expired token",
      detail: err instanceof Error ? err.message : "unknown",
    });
  }
}

/**
 * Allows only users whose role is in the given set.
 */
export function requireRole(...roles: string[]) {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) return res.status(401).json({ error: "Not authenticated" });
    if (!req.user.role || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: "Insufficient permissions" });
    }
    next();
  };
}
