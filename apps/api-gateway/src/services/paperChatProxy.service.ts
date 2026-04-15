import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { env } from "../config/env";
import { ApiError } from "../middleware/errorHandler";
import { logger } from "../middleware/logger";

const client = axios.create({
  baseURL: env.PAPER_CHAT_URL,
  timeout: 120_000,
  headers: { "Content-Type": "application/json" },
});

/**
 * Forward a request to the paper-chat FastAPI service (port 8005).
 * Used by the papers/chat/language/training routes — completely separate
 * from the 4 module ML services.
 */
export async function callPaperChat<T>(
  path: string,
  method: "GET" | "POST" | "DELETE" | "PATCH" = "GET",
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  try {
    const { data } = await client.request<T>({
      url: path,
      method,
      data: body,
      ...config,
    });
    return data;
  } catch (err) {
    if (err instanceof AxiosError) {
      logger.error(
        { path, status: err.response?.status, data: err.response?.data },
        "paper-chat service call failed",
      );
      throw new ApiError(
        err.response?.status ?? 502,
        `paper-chat service error: ${err.message}`,
        err.response?.data,
      );
    }
    throw err;
  }
}
