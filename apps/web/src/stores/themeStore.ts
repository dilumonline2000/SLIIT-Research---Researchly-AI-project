"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  /** Apply the current theme to <html>. Safe to call any time on the client. */
  applyTheme: () => void;
}

const STORAGE_KEY = "r26-theme";

function resolve(theme: Theme): "light" | "dark" {
  if (theme === "system") {
    if (typeof window === "undefined") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return theme;
}

function applyDocClass(theme: Theme) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", resolve(theme) === "dark");
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "system",
      setTheme: (theme) => {
        set({ theme });
        applyDocClass(theme);
      },
      toggleTheme: () => {
        // Cycle: light → dark → system → light
        const cur = get().theme;
        const next: Theme = cur === "light" ? "dark" : cur === "dark" ? "system" : "light";
        set({ theme: next });
        applyDocClass(next);
      },
      applyTheme: () => applyDocClass(get().theme),
    }),
    {
      name: STORAGE_KEY,
      partialize: (s) => ({ theme: s.theme }),
    },
  ),
);

// Re-apply when the OS preference changes (only matters when theme === 'system')
if (typeof window !== "undefined") {
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener?.("change", () => {
    const t = useThemeStore.getState().theme;
    if (t === "system") applyDocClass(t);
  });
}
