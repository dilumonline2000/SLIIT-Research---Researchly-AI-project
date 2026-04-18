import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { createClient } from "./supabase/client";
import { API_GATEWAY_URL } from "./constants";

const api = axios.create({
  baseURL: API_GATEWAY_URL,
  timeout: 60_000,
});

// Cache token in memory — updated by auth state listener, never blocks requests
let _cachedToken: string | null = null;

if (typeof window !== "undefined") {
  const supabase = createClient();
  // Seed from existing session immediately (synchronous read from localStorage)
  supabase.auth.getSession().then(({ data: { session } }) => {
    _cachedToken = session?.access_token ?? null;
  });
  // Keep cache fresh on sign-in / sign-out / token refresh
  supabase.auth.onAuthStateChange((_event, session) => {
    _cachedToken = session?.access_token ?? null;
  });
}

// Attach cached JWT synchronously — no async hang possible
api.interceptors.request.use((config) => {
  if (_cachedToken) {
    config.headers.Authorization = `Bearer ${_cachedToken}`;
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

export async function apiPatch<T, B = unknown>(
  url: string,
  body?: B,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await api.patch<T>(url, body, config);
  return data;
}

export async function apiDelete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await api.delete<T>(url, config);
  return data;
}

export default api;
