# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/auth.setup.ts >> authenticate
- Location: e2e/tests/auth.setup.ts:4:1

# Error details

```
Error: Channel closed
```

```
Error: page.goto: net::ERR_ABORTED at https://dev.oblak24.org/
Call log:
  - navigating to "https://dev.oblak24.org/", waiting until "load"

```

# Test source

```ts
  1  | import { Page, expect } from '@playwright/test';
  2  | 
  3  | const TEST_USER_EMAIL = process.env.TEST_USER_EMAIL || 'admin@example.com';
  4  | const TEST_USER_PASSWORD = process.env.TEST_USER_PASSWORD || 'admin1234';
  5  | 
  6  | export async function login(page: Page, email?: string, password?: string): Promise<void> {
  7  |   const userEmail = email || TEST_USER_EMAIL;
  8  |   const userPassword = password || TEST_USER_PASSWORD;
  9  | 
> 10 |   await page.goto('/');
     |              ^ Error: page.goto: net::ERR_ABORTED at https://dev.oblak24.org/
  11 |   
  12 |   const currentUrl = page.url();
  13 |   if (!currentUrl.includes('/login')) {
  14 |     await page.goto('/login');
  15 |   }
  16 | 
  17 |   await page.waitForSelector('input[name="identifier"], input[id="identifier"]', { timeout: 10000 });
  18 |   
  19 |   const identifierField = page.getByLabel('Имейл или потребителско име');
  20 |   await identifierField.fill(userEmail);
  21 |   await page.getByLabel('Парола').fill(userPassword);
  22 |   await page.getByRole('button', { name: 'Влез в системата' }).click();
  23 | 
  24 |   await expect(page).not.toHaveURL(/\/login/, { timeout: 15000 });
  25 | }
  26 | 
  27 | export async function navigateTo(page: Page, path: string): Promise<void> {
  28 |   await page.goto(path);
  29 |   await page.waitForLoadState('networkidle');
  30 | }
  31 | 
```