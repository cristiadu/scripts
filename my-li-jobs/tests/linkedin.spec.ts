import { test, expect } from '@playwright/test';
import dotenv from 'dotenv';

test.describe('Get new jobs from LinkedIn', () => {
  dotenv.config();
  const searchTerms = process.env.SEARCH_TERMS?.split(',') || ['software'];

  test.beforeAll(async ({ page }) => {
    await page.goto('https://www.linkedin.com/');
  
    await expect(page).toHaveTitle("LinkedIn: Log In or Sign Up");
  
    // Log in into LinkedIn
    await page.getByLabel('Email or phone').fill(process.env.USERNAME || 'unset');
    await page.getByLabel('Password').first().fill(process.env.PASSWORD || 'unset');
    await page.getByRole('button', { name: 'Sign In' }).click();
  
    // Wait until "Jobs" link appear on header
    await expect(page.getByTitle('Jobs', { exact: true })).toBeVisible();
  });

  // For each searchTerm, check all jobs.
  for(const searchTerm of searchTerms) {
    test(`fetch jobs matching term: ${searchTerm}`, async ({ page }) => {
      await page.getByTitle('Jobs', { exact: true }).click();

       // Wait until "Search" placeholder changes to Job specific one.
      const searchBoxElement = page.getByRole('combobox', {name: 'Search by title, skill, or company', exact: true });
      await expect(searchBoxElement).toBeVisible();

      await searchBoxElement.click().then(() => searchBoxElement.fill(searchTerm));
      await page.getByRole('button', {name: 'Search', exact: true}).click();
      await expect(page.getByTitle(`${searchTerm} in Canada`)).toBeVisible();
    });
  }
})


