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

// Module 3 encodes 4k papers on first request (~90s); others are fast
const MODULE_TIMEOUTS: Record<ModuleId, number> = { 1: 60_000, 2: 60_000, 3: 150_000, 4: 60_000 };

function buildClient(moduleId: ModuleId) {
  return axios.create({
    baseURL: moduleUrls[moduleId],
    timeout: MODULE_TIMEOUTS[moduleId],
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
      // FastAPI returns { detail: string | [{loc, msg, type}, ...] }; flatten it.
      const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
      let humanMsg: string;
      if (Array.isArray(detail)) {
        humanMsg = detail
          .map((d: { loc?: unknown[]; msg?: string }) => {
            const field = Array.isArray(d.loc) ? d.loc.slice(-1)[0] : "field";
            return `${String(field)}: ${d.msg ?? "invalid"}`;
          })
          .join("; ");
      } else if (typeof detail === "string") {
        humanMsg = detail;
      } else {
        humanMsg = err.message;
      }
      throw new ApiError(
        err.response?.status ?? 502,
        `ML service (module ${moduleId}) error: ${humanMsg}`,
        err.response?.data,
      );
    }
    throw err;
  }
}
