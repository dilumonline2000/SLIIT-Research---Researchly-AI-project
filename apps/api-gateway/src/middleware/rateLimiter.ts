import rateLimit from "express-rate-limit";

export const globalRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  limit: 120,
  standardHeaders: "draft-7",
  legacyHeaders: false,
  message: { error: "Too many requests, please slow down" },
});

export const mlRateLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 30,
  message: { error: "ML endpoint rate limit exceeded" },
});
