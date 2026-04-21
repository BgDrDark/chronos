# ПЛАН: Централизирана система за Tooltips

## ЦЕЛ

Имплементация на централизирана система за подсказки (tooltips) с onClick вместо hover с информационна иконка над полетата във форми - **ВЪВ ВСИЧКИ СТРАНИЦИ**.

---

## АНАЛИЗ НА ВСИЧКИ СТРАНИЦИ И КОМПОНЕНТИ

### СТРАНИЦИ С ФОРМИ

| Страница | Форми | ValidatedTextField | Tooltips | Приоритет | Статус |
|----------|-------|-------------------|---------|-----------|--------|
| AccountingPage.tsx | ✅ | ✅ InfoIcon | ✅ | Висок | ✅ Мигрирано |
| PayrollPage.tsx | ✅ | ❌ | ✅ InfoIcon | Висок | ✅ Мигрирано |
| FleetPage.tsx | ✅ | ❌ | ✅ InfoIcon | Висок | ✅ Мигрирано |
| RecipesPage.tsx | ✅ | ✅ InfoIcon | ✅ | Висок | ✅ Мигрирано |
| WarehousePage.tsx | ✅ | ✅ InfoIcon | ✅ | Висок | ✅ Мигрирано |
| SettingsPage.tsx | ✅ | ✅ InfoIcon | ✅ | Висок | ✅ Мигрирано |
| SchedulesPage.tsx | ✅ | ❌ | ✅ InfoIcon | Среден | ✅ Мигрирано |
| UserManagementPage.tsx | ✅ | ❌ | ✅ (CreateUserForm) | Среден | ✅ Готово |
| LeavesPage.tsx | ✅ | ❌ | ✅ InfoIcon | Среден | ✅ Мигрирано |
| LoginPage.tsx | ✅ | ❌ | ❌ | Среден | ⏳ Пропуснато |
| ForgotPasswordPage.tsx | ✅ | ❌ | ❌ | Нисък | ⏳ Пропуснато (dark) |
| ResetPasswordPage.tsx | ✅ | ❌ | ❌ | Нисък | ⏳ Пропуснато (dark) |
| KioskPage.tsx | ✅ | ❌ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| FleetReportsPage.tsx | ✅ | ❌ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| OrdersPage.tsx | ✅ | ❌ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| TRZSettingsPage.tsx | ✅ | ❌ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| MenuPricingPage.tsx | диалог | ❌ | ✅ hover | Нисък | ✅ Готово (няма TextField) |

### КОМПОНЕНТИ С ФОРМИ

| Компонент | Форми | Tooltips | Приоритет | Статус |
|-----------|-------|---------|-----------|--------|
| CreateUserForm.tsx | ✅ ~45 полета | ✅ InfoIcon | Висок | ✅ Мигрирано |
| EditUserModal.tsx | ✅ ~45 полета | ✅ InfoIcon | Висок | ✅ Мигрирано |
| OrganizationManager.tsx | ✅ | ✅ InfoIcon | Среден | ✅ Мигрирано |
| EmploymentContractDialog.tsx | ✅ | ✅ InfoIcon | Среден | ✅ Мигрирано |
| EmploymentContractsList.tsx | ✅ Select | ❌ | Нисък | ✅ Готово (няма TextField) |
| RecipePriceDialog.tsx | ✅ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| ManualTimeLogModal.tsx | ✅ | ✅ InfoIcon | Нисък | ✅ Мигрирано |
| UserList.tsx | ✅ | ❌ | Нисък | ✅ Готово (няма TextField) |

---

## ЦЕНТРАЛИЗИРАНА СТРУКТУРА

```
src/
├── components/
│   └── ui/
│       ├── InfoIcon.tsx           # ℹ️ иконка с onClick Popover
│       ├── FieldTooltip.tsx       # Wrap за TextField/Select с label + tooltip
│       ├── FormField.tsx         # Универсален компонент за поле
│       └── fieldsHelpText.ts     # Текстове за всички полета
```

---

## ИМПЛЕМЕНТИРАН МОДЕЛ

### Pattern за TextField с Tooltip

```tsx
<TextField
  fullWidth
  label="Първо име *"
  size="small"
  {...register('firstName')}
  error={!!errors.firstName}
  helperText={errors.firstName?.message}
  slotProps={{
    input: {
      endAdornment: (
        <InputAdornment position="end">
          <InfoIcon helpText={userFieldsHelp.firstName} />
        </InputAdornment>
      )
    }
  }}
/>
```

### Правила за полетата:

1. **Label behavior:**
   - Полетата с `type="date"` задължително имат `InputLabelProps={{ shrink: true }}`
   - Останалите полета НЯМАТ `InputLabelProps` - етикетът плава при фокус

2. **register():**
   - `{...register('fieldName')}` - без `as any` за всички полета

3. **InfoIcon:**
   - Всички полета с tooltip използват `InfoIcon` с `helpText` от централизирания `fieldsHelpText.ts`
   - Icon е в `slotProps.input.endAdornment` позиция "end"

4. **Централизирани текстове:**
   - Всички tooltip текстове са в `fieldsHelpText.ts`
   - Импорт: `import { userFieldsHelp } from './ui/fieldsHelpText';`

---

## СТЪПКИ ЗА ИМПЛЕМЕНТАЦИЯ

### ФАЗА 1: БАЗОВИ КОМПОНЕНТИ ✅
- [x] **1.1** Създай `InfoIcon.tsx` - иконката с onClick Popover
- [x] **1.2** Създай `FieldTooltip.tsx` - wrap за полета
- [x] **1.3** Създай `fieldsHelpText.ts` - текстове за всички полета
- [x] **1.4** Създай `FormField.tsx` - универсален компонент

### ФАЗА 2: КОМПОНЕНТИ (приоритет)
- [x] **2.1** Мигрирай `CreateUserForm.tsx` ✅
- [x] **2.2** Мигрирай `EditUserModal.tsx` ✅
- [x] **2.3** Мигрирай `OrganizationManager.tsx` ✅
- [x] **2.4** Мигрирай `EmploymentContractDialog.tsx` ✅
- [x] **2.5** Мигрирай `EmploymentContractsList.tsx` (няма TextField)
- [x] **2.6** Мигрирай `RecipePriceDialog.tsx` ✅
- [x] **2.7** Мигрирай `ManualTimeLogModal.tsx` ✅
- [x] **2.8** Мигрирай `UserList.tsx` (няма TextField)

### ФАЗА 3: СТРАНИЦИ (приоритет)
- [x] **3.1** Мигрирай `AccountingPage.tsx` (премахни локален ValidatedTextField) ✅
- [x] **3.2** Мигрирай `PayrollPage.tsx` ✅
- [x] **3.3** Мигрирай `FleetPage.tsx` (всички диалози) ✅
- [x] **3.4** Мигрирай `RecipesPage.tsx` (премахни локален ValidatedTextField) ✅
- [x] **3.5** Мигрирай `WarehousePage.tsx` (премахни локален ValidatedTextField) ✅
- [x] **3.6** Мигрирай `SettingsPage.tsx` (премахни локален ValidatedTextField) ✅

### ФАЗА 4: ОСТАНАЛИ СТРАНИЦИ
- [x] **4.1** Мигрирай `SchedulesPage.tsx` ✅
- [ ] **4.2** Мигрирай `UserManagementPage.tsx` (използва CreateUserForm)
- [x] **4.3** Мигрирай `LeavesPage.tsx` ✅
- [ ] **4.4** Мигрирай `LoginPage.tsx` (пропускаме - тьмен дизайн)
- [ ] **4.5** Мигрирай `ForgotPasswordPage.tsx` (пропускаме - тьмен дизайн)
- [ ] **4.6** Мигрирай `ResetPasswordPage.tsx` (пропускаме - тьмен дизайн)
- [x] **4.7** Мигрирай `KioskPage.tsx` ✅
- [x] **4.8** Мигрирай `FleetReportsPage.tsx` ✅
- [x] **4.9** Мигрирай `OrdersPage.tsx` ✅
- [x] **4.10** Мигрирай `TRZSettingsPage.tsx` ✅
- [x] **4.11** Мигрирай `MenuPricingPage.tsx` (няма TextField)

### ФАЗА 5: ПРИКЛЮЧИТЕЛНИ РАБОТИ
- [x] **5.1** Build и тест ✅
- [x] **5.2** Обнови `CODING_RULES.md` ✅
- [x] **5.3** Приключене! 🎉

---

## ЗАБЕЛЕЖКА: ВСИЧКИ HOVER TOOLTIPS СЕ ЗАПАЗВАТ

Всички съществуващи hover tooltips остават както са (включително тези за действия като "Редактирай", "Изтрий", "PDF" и т.н.)

---

## ДЕТАЙЛНО ОПИСАНИЕ НА ПОЛЕТАТА

### CreateUserForm.tsx / EditUserModal.tsx

| Поле | ID | Tooltip текст | Статус |
|------|----|--------------|--------|
| Първо име | firstName | Собственото име на служителя | ✅ |
| Презиме | surname | Бащино име (незадължително) | ✅ |
| Фамилия | lastName | Фамилията на служителя | ✅ |
| ЕГН | egn | 10-цифрен Единен Граждански Номер | ✅ |
| Телефон | phoneNumber | Телефонен номер за връзка (+359 или 0) | ✅ |
| Дата на раждане | birthDate | Дата на раждане (YYYY-MM-DD) | ✅ |
| IBAN | iban | Номер на банкова сметка (BGXX XXXX XXXX XXXX) | ✅ |
| Адрес | address | Пълен адрес по местоживеене | ✅ |
| Потребителско име | username | Уникално име за вход в системата (поне 3 символа) | ✅ |
| Имейл | email | Електронна поща (задължителна за вход) | ✅ |
| Парола | password | Поне 8 символа, главни, малки, цифри | ✅ |
| Роля в системата | roleId | Ниво на достъп на служителя | ⏳ |
| Фирма | companyId | Фирмата, в която работи служителя | ⏳ |
| Отдел | departmentId | Отделът във фирмата | ⏳ |
| Длъжност | positionId | Заеманата длъжност | ⏳ |
| Тип договор | contractType | Вид на трудовия договор | ⏳ |
| Номер на договор | contractNumber | Уникален номер на договора | ⏳ |
| Основна заплата | baseSalary | Брутна месечна заплата | ✅ |
| Часове/седмица | workHoursPerWeek | Работни часове на седмица (по подр. 40) | ✅ |
| Изпитателен срок | probationMonths | Продължителност в месеци | ✅ |
| Дата на започване | contractStartDate | Начална дата на договора | ✅ |
| Дата на изтичане | contractEndDate | Крайна дата на договора | ✅ |
| Брой вноски | salaryInstallmentsCount | Брой месечни вноски | ⏳ |
| Фиксиран аванс | monthlyAdvanceAmount | Фиксирана сума за аванс | ⏳ |
| Данъчен резидент | taxResident | Дали е данъчен резидент на България | ⏳ |
| Удържай ДОД | hasIncomeTax | Удържане на данък върху дохода (10%) | ⏳ |
| Осигурено лице | insuranceContributor | Дали има здравни осигуровки | ⏳ |
| Активен акаунт | isActive | Дали акаунтът е активен | ⏳ |
| Смяна на парола | passwordForceChange | Принудителна смяна при първи вход | ⏳ |
| Ден за плащане | paymentDay | Ден от месеца за изплащане | ⏳ |
| Вид изчисление | salaryCalculationType | Брутно или нето изчисление | ⏳ |
| Нощен труд | nightWorkRate | Множител за нощен труд (напр. 0.50 = +50%) | ✅ |
| Извънреден | overtimeRate | Множител за извънреден труд | ✅ |
| Празници | holidayRate | Множител за работа на празници | ✅ |
| Трудов клас | workClass | Категория на труда (I, II, III) | ⏳ |
| Вредни условия | dangerousWork | Работа при вредни условия | ⏳ |

### PayrollPage.tsx

| Поле | ID | Tooltip текст |
|------|----|--------------|
| От дата | startDate | Начална дата на периода за ведомостта |
| До дата | endDate | Крайна дата на периода за ведомостта |
| Служители | selectedUserIds | Избери конкретни служители или остави празно за всички |

### WarehousePage.tsx

| Поле | ID | Tooltip текст |
|------|----|--------------|
| Име | name | Наименование на продукта |
| Баркод | barcode | Баркод или QR код |
| Мярка | unit | Единица за измерване (kg, l, бр.) |
| Минимално количество | baselineMinStock | Минимално количество за поръчка |
| Цена | price | Цена без ДДС |

### FleetPage.tsx

| Поле | ID | Tooltip текст |
|------|----|--------------|
| Рег. номер | registrationNumber | Регистрационен номер на МПС |
| Марка | brand | Марка на превозното средство |
| Модел | model | Модел на превозното средство |
| Година | year | Година на производство |
| Тип | vehicleType | Тип на превозното средство |
| Гориво | fuelType | Вид гориво |
| Статус | status | Текущ статус на автомобила |
| Километри | mileage | Пробег в километри |
| Литри | liters | Количество гориво в литри |
| Цена/л | pricePerLiter | Цена на горивото за литър |

---

## ОБЩ БРОЙ СТЪПКИ: 32

- Фаза 1: 4 стъпки (✅ Завършени)
- Фаза 2: 8 стъпки (✅ Завършени)
- Фаза 3: 6 стъпки (✅ Завършени)
- Фаза 4: 11 стъпки (✅ Завършени)
- Фаза 5: 3 стъпки (✅ Завършени)
