import { test, expect } from "@playwright/test";

test("dashboard renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Space Debris Command Center")).toBeVisible();
});
