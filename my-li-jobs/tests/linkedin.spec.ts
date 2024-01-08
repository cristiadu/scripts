import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('https://www.linkedin.com/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle("LinkedIn: Log In or Sign Up");
});

test('get login error when empty', async ({ page }) => {
  await page.goto('https://www.linkedin.com/');

  // Click the get started link.
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Expects page to have a heading with the name of Installation.
  await expect(page.getByText('Please enter an email address or phone number', { exact: true })).toBeVisible();
});
