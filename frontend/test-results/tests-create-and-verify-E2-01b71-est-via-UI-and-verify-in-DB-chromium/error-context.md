# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/create-and-verify.test.ts >> E2E: Create & Verify DB Persistence >> Leave Request Creation >> should create leave request via UI and verify in DB
- Location: frontend/e2e/tests/create-and-verify.test.ts:61:5

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.click: Test timeout of 120000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'НОВА ЗАЯВКА' })

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - generic [ref=e6]: Отпуски > Моите заявки
      - generic [ref=e7]:
        - button "0" [ref=e8] [cursor=pointer]:
          - generic [ref=e9]:
            - img [ref=e10]
            - generic: "0"
        - generic [ref=e12]:
          - paragraph [ref=e13]: Системен Администратор
          - text: super_admin
        - button "Изход" [ref=e14] [cursor=pointer]:
          - img [ref=e15]
  - navigation [ref=e17]:
    - generic [ref=e19]:
      - generic [ref=e20]:
        - generic [ref=e21]: Работно Време
        - button [ref=e22] [cursor=pointer]:
          - img [ref=e23]
      - separator [ref=e25]
      - list [ref=e26]:
        - listitem [ref=e28]:
          - link "Табло" [ref=e29] [cursor=pointer]:
            - /url: /
            - img [ref=e31]
            - paragraph [ref=e34]: Табло
        - listitem [ref=e36]:
          - link "Профил" [ref=e37] [cursor=pointer]:
            - /url: /profile
            - img [ref=e39]
            - paragraph [ref=e42]: Профил
        - listitem [ref=e44]:
          - link "Моят поведенчески профил" [ref=e45] [cursor=pointer]:
            - /url: /my-behavioral-profile
            - img [ref=e47]
            - paragraph [ref=e51]: Моят поведенчески профил
        - listitem [ref=e53]:
          - link "Моят график" [ref=e54] [cursor=pointer]:
            - /url: /my-schedule
            - img [ref=e56]
            - paragraph [ref=e59]: Моят график
        - generic [ref=e60]:
          - listitem [ref=e61]:
            - button "Отпуски" [ref=e62] [cursor=pointer]:
              - img [ref=e64]
              - paragraph [ref=e67]: Отпуски
              - img [ref=e68]
          - list [ref=e73]:
            - listitem [ref=e74]:
              - link "Моите заявки" [ref=e75] [cursor=pointer]:
                - /url: /leaves/my-requests
                - paragraph [ref=e77]: Моите заявки
            - listitem [ref=e78]:
              - link "Одобрения" [ref=e79] [cursor=pointer]:
                - /url: /leaves/approvals
                - paragraph [ref=e81]: Одобрения
            - listitem [ref=e82]:
              - link "Всички заявки" [ref=e83] [cursor=pointer]:
                - /url: /leaves/all
                - paragraph [ref=e85]: Всички заявки
        - listitem [ref=e87]:
          - button "Табло присъствие" [ref=e88] [cursor=pointer]:
            - img [ref=e90]
            - paragraph [ref=e93]: Табло присъствие
            - img [ref=e94]
        - listitem [ref=e97]:
          - button "Графици" [ref=e98] [cursor=pointer]:
            - img [ref=e100]
            - paragraph [ref=e103]: Графици
            - img [ref=e104]
        - listitem [ref=e107]:
          - button "Потребители" [ref=e108] [cursor=pointer]:
            - img [ref=e110]
            - paragraph [ref=e113]: Потребители
            - img [ref=e114]
        - listitem [ref=e117]:
          - button "Отдел ТРЗ" [ref=e118] [cursor=pointer]:
            - img [ref=e120]
            - paragraph [ref=e123]: Отдел ТРЗ
            - img [ref=e124]
        - listitem [ref=e127]:
          - button "Счетоводство" [ref=e128] [cursor=pointer]:
            - img [ref=e130]
            - paragraph [ref=e133]: Счетоводство
            - img [ref=e134]
        - listitem [ref=e137]:
          - button "Уведомления" [ref=e138] [cursor=pointer]:
            - img [ref=e140]
            - paragraph [ref=e143]: Уведомления
            - img [ref=e144]
        - listitem [ref=e147]:
          - button "Поведенчески анализ" [ref=e148] [cursor=pointer]:
            - img [ref=e150]
            - paragraph [ref=e154]: Поведенчески анализ
            - img [ref=e155]
        - listitem [ref=e158]:
          - link "Настройки" [ref=e159] [cursor=pointer]:
            - /url: /settings
            - img [ref=e161]
            - paragraph [ref=e164]: Настройки
        - listitem [ref=e166]:
          - link "Документация" [ref=e167] [cursor=pointer]:
            - /url: /documentation
            - img [ref=e169]
            - paragraph [ref=e172]: Документация
        - listitem [ref=e174]:
          - button "Отдел КД" [ref=e175] [cursor=pointer]:
            - img [ref=e177]
            - paragraph [ref=e180]: Отдел КД
            - img [ref=e181]
        - listitem [ref=e184]:
          - link "Склад" [ref=e185] [cursor=pointer]:
            - /url: /admin/warehouse
            - img [ref=e187]
            - paragraph [ref=e190]: Склад
        - listitem [ref=e192]:
          - link "Рецепти" [ref=e193] [cursor=pointer]:
            - /url: /admin/recipes
            - img [ref=e195]
            - paragraph [ref=e198]: Рецепти
        - listitem [ref=e200]:
          - link "Цени Рецепти" [ref=e201] [cursor=pointer]:
            - /url: /admin/menu-pricing
            - img [ref=e203]
            - paragraph [ref=e206]: Цени Рецепти
        - listitem [ref=e208]:
          - link "Поръчки" [ref=e209] [cursor=pointer]:
            - /url: /admin/orders
            - img [ref=e211]
            - paragraph [ref=e214]: Поръчки
        - listitem [ref=e216]:
          - link "Контрол" [ref=e217] [cursor=pointer]:
            - /url: /admin/production/control
            - img [ref=e219]
            - paragraph [ref=e222]: Контрол
        - listitem [ref=e224]:
          - link "Логистика" [ref=e225] [cursor=pointer]:
            - /url: /admin/logistics
            - img [ref=e227]
            - paragraph [ref=e230]: Логистика
        - listitem [ref=e232]:
          - link "Автомобили" [ref=e233] [cursor=pointer]:
            - /url: /admin/fleet
            - img [ref=e235]
            - paragraph [ref=e238]: Автомобили
        - listitem [ref=e240]:
          - link "Справки" [ref=e241] [cursor=pointer]:
            - /url: /admin/fleet/reports
            - img [ref=e243]
            - paragraph [ref=e246]: Справки
        - listitem [ref=e248]:
          - link "Терминал за присъствие" [ref=e249] [cursor=pointer]:
            - /url: /kiosk
            - img [ref=e251]
            - paragraph [ref=e254]: Терминал за присъствие
        - listitem [ref=e256]:
          - link "Терминал за достъп" [ref=e257] [cursor=pointer]:
            - /url: /kiosk/terminal
            - img [ref=e259]
            - paragraph [ref=e262]: Терминал за достъп
        - listitem [ref=e264]:
          - link "Производствен терминал" [ref=e265] [cursor=pointer]:
            - /url: /admin/production/kiosk
            - img [ref=e267]
            - paragraph [ref=e270]: Производствен терминал
      - separator [ref=e271]
      - generic [ref=e272]:
        - generic [ref=e273]: © Oblak24 Team © 2026
        - generic [ref=e274]: "Сесия: 00:01:57"
  - main [ref=e275]:
    - alert [ref=e277]:
      - img [ref=e279]
      - generic [ref=e281]:
        - generic [ref=e282]: Липсващи SMTP настройки
        - text: Системата няма въведени данни за имейл сървър. Потребителите няма да получават уведомления и писма за забравена парола. Моля, конфигурирайте ги в
        - link "Уведомления" [ref=e283] [cursor=pointer]:
          - /url: /admin/notifications/smtp
        - text: .
      - button "Close" [ref=e285] [cursor=pointer]:
        - img [ref=e286]
    - alert [ref=e289]:
      - img [ref=e291]
      - generic [ref=e293]: "Грешка при зареждане на данни: Response not successful: Received status code 522"
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import { login, navigateTo } from '../helpers/auth';
  3   | import { queryDB, queryOne } from '../helpers/db';
  4   | import { countRows } from '../helpers/seed';
  5   | 
  6   | test.describe('E2E: Create & Verify DB Persistence', () => {
  7   | 
  8   |   test.describe('Company Creation', () => {
  9   |     test('should create company via UI and verify in DB', async ({ page }) => {
  10  |       await login(page);
  11  |       await navigateTo(page, '/admin/users/org-structure');
  12  | 
  13  |       await page.getByRole('button', { name: 'Добави фирма' }).click();
  14  |       await page.getByLabel('Име на фирмата').fill('E2E Test Company');
  15  |       await page.getByLabel('ЕИК').fill('123456789');
  16  |       await page.getByLabel('Адрес').fill('Sofia, Bulgaria');
  17  |       await page.getByRole('button', { name: 'Създай' }).click();
  18  | 
  19  |       // Wait for dialog to close after successful creation
  20  |       await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
  21  | 
  22  |       const company = await queryOne(
  23  |         `SELECT id, name, eik, address FROM companies WHERE name = 'E2E Test Company' ORDER BY id DESC LIMIT 1`
  24  |       );
  25  |       expect(company).toBeTruthy();
  26  |       expect(company!.name).toBe('E2E Test Company');
  27  |       expect(company!.eik).toBe('123456789');
  28  |       expect(company!.address).toBe('Sofia, Bulgaria');
  29  |     });
  30  |   });
  31  | 
  32  |   test.describe('User Creation', () => {
  33  |     test('should create user via UI and verify in DB', async ({ page }) => {
  34  |       await login(page);
  35  |       await navigateTo(page, '/admin/users/list');
  36  | 
  37  |       const email = `e2e_user_${Date.now()}@test.bg`;
  38  | 
  39  |       await page.getByRole('button', { name: 'НОВ ПОТРЕБИТЕЛ' }).click();
  40  |       await page.getByLabel('Първо име').fill('E2E');
  41  |       await page.getByLabel('Фамилия').fill('TestUser');
  42  |       await page.getByLabel('Имейл адрес').fill(email);
  43  |       await page.getByLabel('Парола').fill('TestPass123!');
  44  |       await page.getByRole('button', { name: 'Създай' }).click();
  45  | 
  46  |       // Wait for dialog to close after successful creation
  47  |       await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
  48  | 
  49  |       const user = await queryOne(
  50  |         `SELECT id, email, first_name, last_name, is_active FROM users WHERE email = '${email}'`
  51  |       );
  52  |       expect(user).toBeTruthy();
  53  |       expect(user!.email).toBe(email);
  54  |       expect(user!.first_name).toBe('E2E');
  55  |       expect(user!.last_name).toBe('TestUser');
  56  |       expect(user!.is_active).toBe(true);
  57  |     });
  58  |   });
  59  | 
  60  |   test.describe('Leave Request Creation', () => {
  61  |     test('should create leave request via UI and verify in DB', async ({ page }) => {
  62  |       await login(page);
  63  |       await navigateTo(page, '/leaves');
  64  | 
> 65  |       await page.getByRole('button', { name: 'НОВА ЗАЯВКА' }).click();
      |                                                               ^ Error: locator.click: Test timeout of 120000ms exceeded.
  66  |       await page.getByLabel('Тип отпуск').click();
  67  |       await page.getByRole('option', { name: 'Платен годишен отпуск' }).click();
  68  |       // The dialog shows date pickers for the selected leave type
  69  |       // Fill the first date field (start date)
  70  |       await page.getByPlaceholder('мм/дд/гггг').first().fill('08/01/2026');
  71  |       // Fill the second date field (end date) if visible
  72  |       const dateInputs = page.getByPlaceholder('мм/дд/гггг');
  73  |       if (await dateInputs.count() > 1) {
  74  |         await dateInputs.nth(1).fill('08/05/2026');
  75  |       }
  76  |       await page.getByLabel('Причина (по избор)').fill('E2E Leave Test');
  77  |       await page.getByRole('button', { name: 'ИЗПРАТИ' }).click();
  78  | 
  79  |       // Wait for dialog to close after successful submission
  80  |       await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 10000 });
  81  | 
  82  |       const leave = await queryOne(
  83  |         `SELECT id, start_date, end_date, leave_type, status, reason
  84  |          FROM leave_requests WHERE reason = 'E2E Leave Test' ORDER BY created_at DESC LIMIT 1`
  85  |       );
  86  |       expect(leave).toBeTruthy();
  87  |       expect(leave!.start_date).toEqual(new Date('2026-08-01'));
  88  |       expect(leave!.end_date).toEqual(new Date('2026-08-05'));
  89  |       expect(leave!.leave_type).toBe('paid_leave');
  90  |       expect(leave!.status).toBe('pending');
  91  |     });
  92  |   });
  93  | 
  94  |   test.describe('Shift Creation', () => {
  95  |     test('should create shift via UI and verify in DB', async ({ page }) => {
  96  |       await login(page);
  97  |       await navigateTo(page, '/admin/schedules/shifts');
  98  | 
  99  |       const shiftName = `E2E Shift ${Date.now()}`;
  100 | 
  101 |       // Fill the form fields that are already visible on the page
  102 |       await page.getByLabel('Име на смяната').fill(shiftName);
  103 |       await page.getByLabel('Начало').fill('08:00');
  104 |       await page.getByLabel('Край').fill('16:00');
  105 |       // Click the + button to add the shift
  106 |       await page.getByRole('button', { name: '+' }).click();
  107 | 
  108 |       // Wait for the new shift to appear in the list
  109 |       await expect(page.getByText(shiftName)).toBeVisible({ timeout: 10000 });
  110 | 
  111 |       const shift = await queryOne(
  112 |         `SELECT id, name, start_time, end_time FROM shifts WHERE name = '${shiftName}'`
  113 |       );
  114 |       expect(shift).toBeTruthy();
  115 |       expect(shift!.name).toBe(shiftName);
  116 |     });
  117 |   });
  118 | 
  119 |   test.describe('Department Creation', () => {
  120 |     test('should create department via UI and verify in DB', async ({ page }) => {
  121 |       await login(page);
  122 |       await navigateTo(page, '/admin/users/org-structure');
  123 | 
  124 |       const deptName = `E2E Dept ${Date.now()}`;
  125 | 
  126 |       await page.getByLabel('Добави отдел').click();
  127 |       await page.getByLabel('Име на отдела').fill(deptName);
  128 |       // Select first available company from the dropdown in the dialog
  129 |       const dialog = page.getByRole('dialog');
  130 |       const companySelect = dialog.getByRole('combobox', { name: 'Фирма' });
  131 |       if (await companySelect.isVisible()) {
  132 |         await companySelect.click();
  133 |         await page.getByRole('option').first().click();
  134 |       }
  135 |       await dialog.getByRole('button', { name: 'Създай' }).click();
  136 | 
  137 |       // Wait for dialog to close after successful creation
  138 |       await expect(dialog).not.toBeVisible({ timeout: 10000 });
  139 | 
  140 |       const dept = await queryOne(
  141 |         `SELECT id, name FROM departments WHERE name = '${deptName}'`
  142 |       );
  143 |       expect(dept).toBeTruthy();
  144 |       expect(dept!.name).toBe(deptName);
  145 |     });
  146 |   });
  147 | });
  148 | 
```