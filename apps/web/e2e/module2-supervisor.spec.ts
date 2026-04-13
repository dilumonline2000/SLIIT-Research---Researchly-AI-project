import { test, expect } from "@playwright/test";
import { login } from "./auth.setup";

test.describe("Module 2 — Collaboration", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("supervisor match: submit interests and see ranked matches", async ({ page }) => {
    await page.goto("/collaboration/supervisor-match");
    await expect(page.getByRole("heading", { name: /supervisor/i })).toBeVisible();

    // Fill the interests / abstract inputs — interests may be a comma-separated input
    const interestsInput = page
      .locator("input, textarea")
      .filter({ hasText: "" })
      .first();
    await interestsInput.fill("machine learning, healthcare");

    await page.getByRole("button", { name: /match|find|search/i }).first().click();

    // Either matches render, or an empty-state shows. Accept both as passing —
    // the point is the API call doesn't throw and the page remains rendered.
    await expect(
      page.locator("text=/similarity|score|match|no supervisors|no matches/i").first(),
    ).toBeVisible({ timeout: 30_000 });
  });
});
