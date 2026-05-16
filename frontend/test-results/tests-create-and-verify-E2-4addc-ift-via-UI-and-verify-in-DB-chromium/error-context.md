# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/create-and-verify.test.ts >> E2E: Create & Verify DB Persistence >> Shift Creation >> should create shift via UI and verify in DB
- Location: frontend/e2e/tests/create-and-verify.test.ts:95:5

# Error details

```
Error: Channel closed
```

```
Error: locator.click: Target page, context or browser has been closed
Call log:
  - waiting for getByRole('button', { name: '+' })

```

```
Error: browserContext.close: Target page, context or browser has been closed
```