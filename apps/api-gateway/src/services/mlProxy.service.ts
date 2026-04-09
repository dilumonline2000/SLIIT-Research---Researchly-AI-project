import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { env } from "../config/env";
import { ApiError } from "../middleware/errorHandler";
import { logger } from "../middleware/logger";

export type ModuleId = 1 | 2 | 3 | 4;

const moduleUrls: Record<ModuleId, string> = {
  1: env.MODULE1_URL,
  2: env.MODULE2_URL,
  3: env.MODULE3_URL,
  4: env.MODULE4_URL,
};

function buildClient(moduleId: ModuleId) {
  return axios.create({
    baseURL: moduleUrls[moduleId],
    timeout: 60_000,
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * Forward a request to one of the Python ML microservices.
 * Wraps errors in ApiError so the central error handler can respond.
 */
export async function callMlService<T>(
  moduleId: ModuleId,
  path: string,
  method: "GET" | "POST" = "POST",
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const client = buildClient(moduleId);
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
        { moduleId, path, status: err.response?.status, data: err.response?.data },
        "ML service call failed",
      );
      throw new ApiError(
        err.response?.status ?? 502,
        `ML service (module ${moduleId}) error: ${err.message}`,
        err.response?.data,
      );
    }
    throw err;
  }
}
