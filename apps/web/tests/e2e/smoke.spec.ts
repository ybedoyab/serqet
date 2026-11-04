import { expect, test } from "@playwright/test";

test("overview states the question and that models are unmeasured", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Authority changed");
  await expect(page.getByText("Trust the action, not the answer.")).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Measured.");
  await page.getByRole("link", { name: "Read the tasks" }).click();
  await expect(page).toHaveURL(/\/benchmarks/);
});

test("benchmarks lists the tasks and opens a simulated timeline", async ({ page }) => {
  await page.goto("/benchmarks");
  await expect(page.getByRole("link", { name: "Reschedule the launch patient's slot" })).toBeVisible();
  await expect(page.getByText("measured model result").first()).toBeVisible();
  await page.getByRole("link", { name: "Stop when research consent is revoked" }).click();
  const demo = page.getByText("SIMULATED DEMO", { exact: true }).locator("..");
  await demo.getByRole("button", { name: "Next step" }).click();
  await expect(demo.getByText("Step 2 of")).toBeVisible();
  const measured = page.getByText("MEASURED MODEL RESULT", { exact: true }).first().locator("..");
  await measured.getByRole("button", { name: "Next step" }).click();
  await expect(measured.getByText("Step 2 of")).toBeVisible();
});

test("models page does not invent a leaderboard", async ({ page }) => {
  await page.goto("/models");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Measured model results");
  await expect(page.getByRole("status")).toContainText("MEASURED MODEL RESULT");
  await expect(page.getByRole("heading", { name: "openrouter/openai/gpt-6-sol" }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "oracle_agent" })).toBeVisible();
});

test("mobile overview does not overflow the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
});

test("keyboard focus is visible on the overview", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});

test("tablet overview does not overflow the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
});

test("health route reports the service", async ({ request }) => {
  const response = await request.get("/api/health");
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  expect(body.service).toBe("serqet");
  expect(body.ok).toBe(true);
});
