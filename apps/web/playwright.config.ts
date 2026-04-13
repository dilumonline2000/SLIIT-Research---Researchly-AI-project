import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E config for Researchly AI.
 *
 * Prereqs before running:
 *   1. `pnpm --filter web dev` running on :3000  (or set BASE_URL)
 *   2. `pnpm --filter api-gateway dev` on :3001
 *   3. All 4 FastAPI services on 8001-8004 (or smoke tests will fail gracefully)
 *   4. A seeded Supabase with the test user (see scripts/seed_supabase.py)
 *   5. E2E_TEST_EMAIL / E2E_TEST_PASSWORD env vars pointing to that user
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // shared auth state — keep sequential
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
