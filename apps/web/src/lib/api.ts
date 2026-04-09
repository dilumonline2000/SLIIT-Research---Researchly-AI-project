import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { createClient } from "./supabase/client";
import { API_GATEWAY_URL } from "./constants";

const api = axios.create({
  baseURL: API_GATEWAY_URL,
  timeout: 30_000,
});

// Attach Supabase JWT to every request from the browser
api.interceptors.request.use(async (config) => {
  if (typeof window !== "undefined") {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error: AxiosError<{ message?: string }>) => {
    const message = error.response?.data?.message ?? error.message;
    return Promise.reject(new Error(message));
  },
);

export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.get<T>(url, config);
  return data;
}

export async function apiPost<T, B = unknown>(
  url: string,
  body?: B,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await api.post<T>(url, body, config);
  return data;
}

export default api;
