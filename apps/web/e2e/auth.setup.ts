import { expect, type Page } from "@playwright/test";

/**
 * Shared login helper used by every spec file.
 *
 * Navigates to /login, submits credentials, waits for the dashboard to render.
 * Requires a seeded Supabase user — see scripts/seed_supabase.py.
 */
export async function login(page: Page) {
  const email = process.env.E2E_TEST_EMAIL ?? "amaya@student.sliit.lk";
  const password = process.env.E2E_TEST_PASSWORD ?? "Seeded!2026";

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();

  // Dashboard layout redirects unauthed users to /login, so landing on
  // /dashboard is proof of a successful auth handshake.
  await page.waitForURL("**/dashboard", { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
}
