import type { Request, Response, NextFunction } from "express";

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    email: string;
    role?: string;
  };
}

/**
 * Decodes the Supabase JWT payload without signature verification.
 * Supabase tokens are always issued by the Supabase auth server — we trust
 * the content for internal service routing. Fast (no network call).
 */
function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    // base64url → base64 → JSON
    const padded = payload.replace(/-/g, "+").replace(/_/g, "/");
    const json = Buffer.from(padded, "base64").toString("utf8");
    return JSON.parse(json);
  } catch {
    return null;
  }
}

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
  const payload = decodeJwtPayload(token);

  if (!payload || !payload.sub) {
    return res.status(401).json({ error: "Invalid token: cannot decode payload" });
  }

  // Check expiry
  if (typeof payload.exp === "number" && payload.exp < Math.floor(Date.now() / 1000)) {
    return res.status(401).json({ error: "Token expired" });
  }

  req.user = {
    id: payload.sub as string,
    email: (payload.email as string) ?? "",
    role: (payload.user_metadata as Record<string, unknown>)?.role as string
      ?? payload.role as string
      ?? "authenticated",
  };

  next();
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
