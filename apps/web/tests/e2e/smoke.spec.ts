import { expect, test } from "@playwright/test";

test("overview states the question and that models are unmeasured", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Authority changed");
  await expect(page.getByText("Trust the action, not the answer.")).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Not yet measured");
  await page.getByRole("link", { name: "Read the tasks" }).click();
  await expect(page).toHaveURL(/\/benchmarks/);
});

test("benchmarks lists the tasks and opens a simulated timeline", async ({ page }) => {
  await page.goto("/benchmarks");
  await expect(page.getByRole("link", { name: "Reschedule the launch patient's slot" })).toBeVisible();
  await expect(page.getByText("not measured").first()).toBeVisible();
  await page.getByRole("link", { name: "Stop when research consent is revoked" }).click();
  await expect(page.getByText("SIMULATED DEMO")).toBeVisible();
  await page.getByRole("button", { name: "Next step" }).click();
  await expect(page.getByText("Step 2 of")).toBeVisible();
});

test("models page does not invent a leaderboard", async ({ page }) => {
  await page.goto("/models");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("No model has been scored");
  await expect(page.getByRole("status")).toContainText("NOT_MEASURED");
  await expect(page.getByRole("heading", { name: "oracle_agent" })).toBeVisible();
});

test("mobile overview does not overflow the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
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
