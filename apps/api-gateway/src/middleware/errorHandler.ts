import type { Request, Response, NextFunction } from "express";
import { logger } from "./logger";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function notFoundHandler(_req: Request, res: Response) {
  res.status(404).json({ error: "Not found" });
}

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction,
) {
  if (err instanceof ApiError) {
    return res.status(err.status).json({
      error: err.message,
      details: err.details,
    });
  }

  logger.error({ err }, "Unhandled error");
  res.status(500).json({
    error: "Internal server error",
    message: err.message,
  });
}
