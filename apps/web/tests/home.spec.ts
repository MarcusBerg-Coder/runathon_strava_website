import { expect, test } from "@playwright/test";

test("home page shows the live runathon surfaces", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Every donation adds miles." })).toBeVisible();
  await expect(page.getByText("Remaining miles")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Add the next mile." })).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin page renders control room", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto("/admin");

  await expect(page.getByRole("heading", { name: "Runathon control room" })).toBeVisible();
  await expect(page.getByText("Manual adjustment")).toBeVisible();
  expect(errors).toEqual([]);
});
