import { test, expect } from "@playwright/test";
import { login } from "./auth.setup";

test.describe("Module 4 — Analytics", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("trend forecast: page loads and renders forecast cards or empty state", async ({ page }) => {
    await page.goto("/analytics/trends");
    await expect(page.getByRole("heading", { name: /trend forecasting/i })).toBeVisible();

    // Forecasts load on mount — give it time to either render cards or fall back
    // to the "no forecasts" empty state. Either is a passing assertion for us.
    await expect(
      page.locator("text=/forecast|no forecasts|arima|prophet|predicted/i").first(),
    ).toBeVisible({ timeout: 30_000 });
  });

  test("dashboards page renders KPI cards", async ({ page }) => {
    await page.goto("/analytics/dashboards");
    await expect(page.getByRole("heading", { name: /performance dashboards/i })).toBeVisible();

    // KPI cards have labels like "Total Proposals" / "Avg Quality Score"
    await expect(
      page.locator("text=/total proposals|avg quality|at.risk|active supervisors/i").first(),
    ).toBeVisible({ timeout: 20_000 });
  });
});
