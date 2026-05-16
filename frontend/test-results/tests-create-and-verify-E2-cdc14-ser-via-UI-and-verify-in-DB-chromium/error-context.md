# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/create-and-verify.test.ts >> E2E: Create & Verify DB Persistence >> User Creation >> should create user via UI and verify in DB
- Location: frontend/e2e/tests/create-and-verify.test.ts:33:5

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.fill: Test timeout of 120000ms exceeded.
Call log:
  - waiting for getByLabel('Имейл или потребителско име')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - heading "Connection timed out Error code 522" [level=1] [ref=e5]:
      - generic [ref=e6]: Connection timed out
      - text: Error code 522
    - generic [ref=e7]:
      - text: Visit
      - link "cloudflare.com" [ref=e8] [cursor=pointer]:
        - /url: https://www.cloudflare.com/5xx-error-landing?utm_source=errorcode_522&utm_campaign=dev.oblak24.org
      - text: for more information.
    - generic [ref=e9]: 2026-05-16 09:54:23 UTC
  - generic [ref=e12]:
    - generic [ref=e13]:
      - text: You
      - heading "Browser" [level=3] [ref=e17]
      - text: Working
    - generic [ref=e18]:
      - link [ref=e20] [cursor=pointer]:
        - /url: https://www.cloudflare.com/5xx-error-landing?utm_source=errorcode_522&utm_campaign=dev.oblak24.org
      - text: Sofia
      - heading "Cloudflare" [level=3] [ref=e23]:
        - link "Cloudflare" [ref=e24] [cursor=pointer]:
          - /url: https://www.cloudflare.com/5xx-error-landing?utm_source=errorcode_522&utm_campaign=dev.oblak24.org
      - text: Working
    - generic [ref=e25]:
      - text: dev.oblak24.org
      - heading "Host" [level=3] [ref=e29]
      - text: Error
  - generic [ref=e31]:
    - generic [ref=e32]:
      - heading "What happened?" [level=2] [ref=e33]
      - paragraph [ref=e34]: The initial connection between Cloudflare's network and the origin web server timed out. As a result, the web page can not be displayed.
    - generic [ref=e35]:
      - heading "What can I do?" [level=2] [ref=e36]
      - heading "If you're a visitor of this website:" [level=3] [ref=e37]
      - paragraph [ref=e38]: Please try again in a few minutes.
      - heading "If you're the owner of this website:" [level=3] [ref=e39]
      - paragraph [ref=e40]:
        - text: Contact your hosting provider letting them know your web server is not completing requests. An Error 522 means that the request was able to connect to your web server, but that the request didn't finish. The most likely cause is that something on your server is hogging resources.
        - link "Additional troubleshooting information here." [ref=e41] [cursor=pointer]:
          - /url: https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-522/
  - paragraph [ref=e43]:
    - generic [ref=e44]:
      - text: "Cloudflare Ray ID:"
      - strong [ref=e45]: 9fc97fb8cc5dd0dc
    - text: •
    - generic [ref=e46]:
      - text: "Your IP:"
      - button "Click to reveal" [ref=e47] [cursor=pointer]
      - text: •
    - generic [ref=e48]:
      - text: Performance & security by
      - link "Cloudflare" [ref=e49] [cursor=pointer]:
        - /url: https://www.cloudflare.com/5xx-error-landing?utm_source=errorcode_522&utm_campaign=dev.oblak24.org
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
  10 |   await page.goto('/login');
> 11 |   await page.getByLabel('Имейл или потребителско име').fill(userEmail);
     |                                                        ^ Error: locator.fill: Test timeout of 120000ms exceeded.
  12 |   await page.getByLabel('Парола').fill(userPassword);
  13 |   await page.getByRole('button', { name: 'Влез в системата' }).click();
  14 | 
  15 |   await expect(page).toHaveURL(/\/(dashboard|admin|home|presence)/i, { timeout: 15000 });
  16 | }
  17 | 
  18 | export async function navigateTo(page: Page, path: string): Promise<void> {
  19 |   await page.goto(path);
  20 |   await page.waitForLoadState('networkidle');
  21 | }
  22 | 
```