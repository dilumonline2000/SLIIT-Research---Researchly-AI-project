import { test, expect } from "@playwright/test";
import { login } from "./auth.setup";

test.describe("Module 1 — Research Integrity", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("citation parser: submit raw text and see a parsed result", async ({ page }) => {
    await page.goto("/citations/parser");
    await expect(page.getByRole("heading", { name: /citation parser/i })).toBeVisible();

    // Fill the raw citation input — the exact label may be "Raw citation" or similar
    const textarea = page.locator("textarea").first();
    await textarea.fill(
      "Smith J, Doe A. Deep Learning for Medical NLP. Nature. 2024;12(3):45-67.",
    );

    await page.getByRole("button", { name: /parse/i }).click();

    // A successful parse should produce either parsed fields or formatted output.
    // We assert that *some* result region renders within the timeout rather than
    // coupling the test to the exact DOM structure.
    await expect(
      page.locator("text=/apa|ieee|parsed|confidence/i").first(),
    ).toBeVisible({ timeout: 30_000 });
  });
});
