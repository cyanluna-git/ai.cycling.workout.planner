import { test, expect } from '@playwright/test';

// Note: Chromium's default navigator.language is 'en-US',
// so i18next detects English by default (detection order: localStorage, navigator).
// fallbackLng is 'ko' but navigator detection takes priority.

test.describe('i18n - Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('default language is English (navigator detection)', async ({ page }) => {
    await expect(page.getByText(/Get Started for Free/)).toBeVisible();
    await expect(page.getByText('Sound familiar?')).toBeVisible();
  });

  test('language switcher changes to Korean', async ({ page }) => {
    // In English mode, button shows KO
    await page.getByRole('button', { name: /KO/ }).click();
    await expect(page.getByText(/그냥 시작하기/)).toBeVisible();
    await expect(page.getByText('혹시 이런 고민 있으신가요?')).toBeVisible();
  });

  test('language persists in localStorage', async ({ page }) => {
    // Switch to Korean
    await page.getByRole('button', { name: /KO/ }).click();
    await expect(page.getByText(/그냥 시작하기/)).toBeVisible();
    await page.reload();
    await page.waitForLoadState('networkidle');
    // Should still be Korean (persisted in localStorage)
    await expect(page.getByText(/그냥 시작하기/)).toBeVisible();
  });
});

test.describe('i18n - Auth Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('auth page shows English by default', async ({ page }) => {
    // Click Get Started to go to auth page
    await page.getByText(/Get Started for Free/).click();
    await expect(page.getByText('Log in to get started')).toBeVisible();
    await expect(page.getByText('Email')).toBeVisible();
    await expect(page.getByText('Password', { exact: true })).toBeVisible();
  });

  test('auth page switches to Korean', async ({ page }) => {
    await page.getByText(/Get Started for Free/).click();
    await page.getByRole('button', { name: /KO/ }).click();
    await expect(page.getByText('로그인하여 시작하세요')).toBeVisible();
    await expect(page.getByText('이메일')).toBeVisible();
    await expect(page.getByText('비밀번호', { exact: true })).toBeVisible();
  });
});

test.describe('i18n - Language Switcher', () => {
  test('language switcher is visible on landing page', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('networkidle');
    // In English mode, shows KO button
    await expect(page.getByRole('button', { name: /KO/ })).toBeVisible();
  });

  test('can toggle between languages', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should start in English
    await expect(page.getByText(/Get Started for Free/)).toBeVisible();

    // Switch to Korean
    await page.getByRole('button', { name: /KO/ }).click();
    await expect(page.getByText(/그냥 시작하기/)).toBeVisible();

    // Switch back to English
    await page.getByRole('button', { name: /EN/ }).click();
    await expect(page.getByText(/Get Started for Free/)).toBeVisible();
  });
});
