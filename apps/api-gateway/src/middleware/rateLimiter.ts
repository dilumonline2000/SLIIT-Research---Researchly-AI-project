import rateLimit from "express-rate-limit";

export const globalRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  limit: 600, // 10 req/sec — generous for active dev/use
  standardHeaders: "draft-7",
  legacyHeaders: false,
  message: { error: "Too many requests, please slow down" },
});

export const mlRateLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 200, // ~3 req/sec — covers chat, paper listing, health checks
  message: { error: "ML endpoint rate limit exceeded" },
});

// Lighter limit for fast endpoints (health, status)
export const fastRateLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 1000,
  message: { error: "Too many health checks" },
});
