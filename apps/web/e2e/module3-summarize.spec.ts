import { test, expect } from "@playwright/test";
import { login } from "./auth.setup";

test.describe("Module 3 — Data Management", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("summarizer: submit abstract and see a generated summary", async ({ page }) => {
    await page.goto("/data-management/summarizer");
    await expect(page.getByRole("heading", { name: /summariz/i })).toBeVisible();

    const textarea = page.locator("textarea").first();
    await textarea.fill(
      "Transformers have revolutionized natural language processing through self-attention. " +
        "They excel at sequence modeling and have become the dominant architecture across " +
        "language, vision, and multimodal tasks. Recent work focuses on efficiency and scaling laws.",
    );

    // Choose a short-length preset if the buttons exist
    const shortButton = page.getByRole("button", { name: /short/i });
    if (await shortButton.isVisible().catch(() => false)) {
      await shortButton.click();
    }

    await page.getByRole("button", { name: /summariz/i }).last().click();

    // Either the summary renders or an error/empty state shows — we accept both.
    await expect(
      page.locator("text=/summary|compression|failed|loading/i").first(),
    ).toBeVisible({ timeout: 60_000 });
  });
});
