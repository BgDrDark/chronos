# План за имплементация на йерархично меню с подменюта

## Общ преглед

Целта е да се преобразува плоското меню в лявата лента в разкриваеми (accordion-style) подменюта, подобно на табовете в страниците, но визуализирани в страничното меню.

---

## 1. Менюта с подменюта

| Главно меню | Подменюта |
|-------------|-----------|
| **Счетоводство** | Входящи фактури, Изходящи фактури, Касов дневник, Операции, Дневен отчет, Месечен отчет, Годишен отчет (7) |
| **Графици** | Календар, Текущ график, Управление на смени, Шаблони и Ротации, Масово назначаване (5) |
| **Потребители** | Списък служители, Организационна структура (2) |
| **Отпуски** | Моите заявки, Одобрения, Всички заявки (3) |
| **Уведомления** | Събития и Уведомления, SMTP Настройки (2) |
| **Табло присъствие** | Присъствие, Анализи и KPI (2) |

---

## 2. Стъпки за имплементация

### Стъпка 1: Модифицирай `MainLayout.tsx`

#### 1.1. Дефинирай новата структура на данните

```typescript
interface MenuItem {
  text: string;
  icon?: React.ReactNode;
  path?: string;
  visible: boolean;
  children?: MenuItem[];
}
```

#### 1.2. Добави state за разкритите менюта

```typescript
const [expandedMenus, setExpandedMenus] = useState<string[]>([]);

const toggleMenu = (text: string) => {
  setExpandedMenus(prev =>
    prev.includes(text)
      ? prev.filter(t => t !== text)
      : [...prev, text]
  );
};

// Автоматично разкриване на менюто ако текущият път е негово дете
const isMenuExpanded = (text: string, children?: MenuItem[]) => {
  if (!children || children.length === 0) return false;
  if (expandedMenus.includes(text)) return true;
  return children.some(child => location.pathname.startsWith(child.path || ''));
};
```

#### 1.3. Дефинирай менютата с деца

```javascript
const menuItems = [
  // ... менюта без деца ...
  {
    text: 'Счетоводство',
    icon: <ReceiptIcon />,
    visible: isAdmin && isEnabled('accounting'),
    children: [
      { text: 'Входящи фактури', path: '/admin/accounting/incoming', visible: true },
      { text: 'Изходящи фактури', path: '/admin/accounting/outgoing', visible: true },
      { text: 'Касов дневник', path: '/admin/accounting/cash-journal', visible: true },
      { text: 'Операции', path: '/admin/accounting/operations', visible: true },
      { text: 'Дневен отчет', path: '/admin/accounting/daily', visible: true },
      { text: 'Месечен отчет', path: '/admin/accounting/monthly', visible: true },
      { text: 'Годишен отчет', path: '/admin/accounting/yearly', visible: true },
    ]
  },
  {
    text: 'Графици',
    icon: <CalendarIcon />,
    visible: isAdmin && isEnabled('shifts'),
    children: [
      { text: 'Календар', path: '/admin/schedules/calendar', visible: true },
      { text: 'Текущ график', path: '/admin/schedules/current', visible: true },
      { text: 'Управление на смени', path: '/admin/schedules/shifts', visible: true },
      { text: 'Шаблони и Ротации', path: '/admin/schedules/templates', visible: true },
      { text: 'Масово назначаване', path: '/admin/schedules/bulk', visible: true },
    ]
  },
  {
    text: 'Потребители',
    icon: <PeopleIcon />,
    visible: isAdmin,
    children: [
      { text: 'Списък служители', path: '/admin/users/list', visible: true },
      { text: 'Организационна структура', path: '/admin/users/org-structure', visible: true },
    ]
  },
  {
    text: 'Отпуски',
    icon: <FlightTakeoffIcon />,
    visible: !!user && isEnabled('shifts'),
    children: [
      { text: 'Моите заявки', path: '/leaves/my-requests', visible: !!user },
      { text: 'Одобрения', path: '/leaves/approvals', visible: isAdmin },
      { text: 'Всички заявки', path: '/leaves/all', visible: isAdmin },
    ]
  },
  {
    text: 'Уведомления',
    icon: <NotificationsIcon />,
    visible: isAdmin && isEnabled('notifications'),
    children: [
      { text: 'Събития и Уведомления', path: '/admin/notifications/events', visible: true },
      { text: 'SMTP Настройки', path: '/admin/notifications/smtp', visible: true },
    ]
  },
  {
    text: 'Табло присъствие',
    icon: <AssignmentIndIcon />,
    visible: isAdmin && isEnabled('shifts'),
    children: [
      { text: 'Присъствие', path: '/admin/presence/attendance', visible: true },
      { text: 'Анализи и KPI', path: '/admin/presence/analytics', visible: true },
    ]
  },
  // ... останалите менюта без деца ...
];
```

#### 1.4. Рендерирай менюто с подменюта

Създай компонент за рендериране на меню елементи:

```typescript
const renderMenuItem = (item: MenuItem, isChild = false) => {
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = isMenuExpanded(item.text, item.children);
  const isActive = item.path ? location.pathname === item.path : false;

  if (!item.visible) return null;

  return (
    <Box key={item.text}>
      <ListItemButton
        component={item.path ? RouterLink : 'div'}
        to={item.path}
        onClick={() => hasChildren && toggleMenu(item.text)}
        selected={isActive}
        sx={{
          pl: isChild ? 4 : 2,
          py: isChild ? 1 : 1.5,
          '&.Mui-selected': {
            backgroundColor: 'primary.light',
            color: 'primary.contrastText',
          },
          ...(isChild && {
            fontSize: '0.875rem',
            '& .MuiListItemIcon-root': { minWidth: 32 },
          })
        }}
      >
        <ListItemIcon sx={{ minWidth: 40, fontSize: isChild ? '1rem' : '1.25rem' }}>
          {item.icon}
        </ListItemIcon>
        <ListItemText 
          primary={item.text}
          primaryTypographyProps={{ 
            fontWeight: isActive ? 'bold' : 'medium',
            fontSize: isChild ? '0.875rem' : '0.9375rem'
          }} 
        />
        {hasChildren && (
          <ListItemIcon sx={{ minWidth: 32 }}>
            <ExpandMoreIcon 
              sx={{ 
                transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }} 
            />
          </ListItemIcon>
        )}
      </ListItemButton>
      
      {hasChildren && isExpanded && (
        <Box sx={{ pl: 1 }}>
          {item.children
            .filter(child => child.visible)
            .map(child => renderMenuItem(child, true))}
        </Box>
      )}
    </Box>
  );
};
```

#### 1.5. Добави необходимите икони

Добави `ExpandMoreIcon` или `ExpandLessIcon` в импорта:

```typescript
import {
  // ... съществуващи икони
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
```

---

### Стъпка 2: Модифицирай `App.tsx`

Добави новите route-ове за всички подменюта:

```typescript
// Счетоводство
<Route path="/admin/accounting" element={<AccountingPage />} />
<Route path="/admin/accounting/incoming" element={<AccountingPage tab="incoming" />} />
<Route path="/admin/accounting/outgoing" element={<AccountingPage tab="outgoing" />} />
<Route path="/admin/accounting/cash-journal" element={<AccountingPage tab="cash-journal" />} />
<Route path="/admin/accounting/operations" element={<AccountingPage tab="operations" />} />
<Route path="/admin/accounting/daily" element={<AccountingPage tab="daily" />} />
<Route path="/admin/accounting/monthly" element={<AccountingPage tab="monthly" />} />
<Route path="/admin/accounting/yearly" element={<AccountingPage tab="yearly" />} />

// Графици
<Route path="/admin/schedules" element={<SchedulesPage />} />
<Route path="/admin/schedules/calendar" element={<SchedulesPage tab="calendar" />} />
<Route path="/admin/schedules/current" element={<SchedulesPage tab="current" />} />
<Route path="/admin/schedules/shifts" element={<SchedulesPage tab="shifts" />} />
<Route path="/admin/schedules/templates" element={<SchedulesPage tab="templates" />} />
<Route path="/admin/schedules/bulk" element={<SchedulesPage tab="bulk" />} />

// Потребители
<Route path="/admin/users" element={<UserManagementPage />} />
<Route path="/admin/users/list" element={<UserManagementPage tab="list" />} />
<Route path="/admin/users/org-structure" element={<UserManagementPage tab="org-structure" />} />

// Отпуски
<Route path="/leaves" element={<LeavesPage />} />
<Route path="/leaves/my-requests" element={<LeavesPage tab="my-requests" />} />
<Route path="/leaves/approvals" element={<LeavesPage tab="approvals" />} />
<Route path="/leaves/all" element={<LeavesPage tab="all" />} />

// Уведомления
<Route path="/admin/notifications" element={<NotificationsPage />} />
<Route path="/admin/notifications/events" element={<NotificationsPage tab="events" />} />
<Route path="/admin/notifications/smtp" element={<NotificationsPage tab="smtp" />} />

// Табло присъствие
<Route path="/admin/presence" element={<AdminDashboardPage />} />
<Route path="/admin/presence/attendance" element={<AdminDashboardPage tab="attendance" />} />
<Route path="/admin/presence/analytics" element={<AdminDashboardPage tab="analytics" />} />
```

---

### Стъпка 3: Модифицирай страниците

За всяка страница, която има табове:

#### 3.1. `AccountingPage.tsx`

```typescript
import { useParams, useSearchParams } from 'react-router-dom';

// В компонента:
const params = useParams();
const [searchParams] = useSearchParams();
const tabParam = searchParams.get('tab');

const tabMap: Record<string, number> = {
  'incoming': 0,
  'outgoing': 1,
  'cash-journal': 2,
  'operations': 3,
  'daily': 4,
  'monthly': 5,
  'yearly': 6,
};

// Превърни в tab index
const initialTab = tabParam ? (tabMap[tabParam] ?? 0) : 0;
const [tabValue, setTabValue] = useState(initialTab);

// Премахни Tabs от рендера - те вече не са необходими
// или ги направи hidden ако искаш да запазиш функционалността
```

#### 3.2. `SchedulesPage.tsx`

```typescript
const tabMap: Record<string, number> = {
  'calendar': 0,
  'current': 1,
  'shifts': 2,
  'templates': 3,
  'bulk': 4,
};
```

#### 3.3. `UserManagementPage.tsx`

```typescript
const tabMap: Record<string, number> = {
  'list': 0,
  'org-structure': 1,
};
```

#### 3.4. `LeavesPage.tsx`

```typescript
const tabMap: Record<string, number> = {
  'my-requests': 0,
  'approvals': 1,
  'all': 2,
};
```

#### 3.5. `NotificationsPage.tsx`

```typescript
const tabMap: Record<string, number> = {
  'events': 0,
  'smtp': 1,
};
```

#### 3.6. `AdminDashboardPage.tsx`

```typescript
const tabMap: Record<string, number> = {
  'attendance': 0,
  'analytics': 1,
};
```

---

### Стъпка 4: Визуални подобрения (опционално)

#### 4.1. Анимация при разкриване

```typescript
import { Collapse } from '@mui/material';

{hasChildren && (
  <Collapse in={isExpanded}>
    <Box sx={{ pl: 1 }}>
      {item.children
        .filter(child => child.visible)
        .map(child => renderMenuItem(child, true))}
    </Box>
  </Collapse>
)}
```

#### 4.2. Различни икони за родителски менюта

```typescript
const getIcon = (item: MenuItem) => {
  if (item.children && item.children.length > 0) {
    return <FolderIcon />; // или запази оригиналната икона
  }
  return item.icon;
};
```

#### 4.3. Hover ефект за подменютата

```typescript
'&:hover': {
  backgroundColor: isChild ? 'action.hover' : 'action.hover',
},
```

---

## 3. Маршрути (URL пътища)

| Страница | Път |
|----------|-----|
| **Счетоводство** | |
| Входящи фактури | `/admin/accounting/incoming` |
| Изходящи фактури | `/admin/accounting/outgoing` |
| Касов дневник | `/admin/accounting/cash-journal` |
| Операции | `/admin/accounting/operations` |
| Дневен отчет | `/admin/accounting/daily` |
| Месечен отчет | `/admin/accounting/monthly` |
| Годишен отчет | `/admin/accounting/yearly` |
| **Графици** | |
| Календар | `/admin/schedules/calendar` |
| Текущ график | `/admin/schedules/current` |
| Управление на смени | `/admin/schedules/shifts` |
| Шаблони и Ротации | `/admin/schedules/templates` |
| Масово назначаване | `/admin/schedules/bulk` |
| **Потребители** | |
| Списък служители | `/admin/users/list` |
| Организационна структура | `/admin/users/org-structure` |
| **Отпуски** | |
| Моите заявки | `/leaves/my-requests` |
| Одобрения | `/leaves/approvals` |
| Всички заявки | `/leaves/all` |
| **Уведомления** | |
| Събития и Уведомления | `/admin/notifications/events` |
| SMTP Настройки | `/admin/notifications/smtp` |
| **Табло присъствие** | |
| Присъствие | `/admin/presence/attendance` |
| Анализи и KPI | `/admin/presence/analytics` |

---

## 4. Приоритети за имплементация

1. **MainLayout.tsx** - основна логика за менюто
2. **App.tsx** - route-ове
3. **AccountingPage.tsx** - най-много табове (7)
4. **SchedulesPage.tsx** - 5 таба
5. Останалите страници (LeavesPage, UserManagementPage, NotificationsPage, AdminDashboardPage)

---

## 5. Очаквани проблеми и решения

| Проблем | Решение |
|---------|---------|
| Дублиране на код в страниците | Създай универсален `PageWithTabs` компонент |
| Много route-ове | Използвай nested routes в App.tsx |
| Преход от табове | Запази Tabs hidden, но синхронизирай с URL |
| Прехвърляне на големи страници | Имплементирай поетапно |

---

## 6. Тестване

1. **Навигация** - клик върху подменю променя URL и показва правилната страница
2. **Разкриване** - клик върху родителско меню разкрива подменюто
3. **Active state** - правилно подчертаване на активното меню
4. **Responsive** - мобилно меню работи коректно
5. **Права** - видимостта на менютата според ролите работи

---

## 7. Файлове за промяна

| Файл | Промяна |
|------|---------|
| `frontend/src/components/MainLayout.tsx` | Основна логика за менюто |
| `frontend/src/App.tsx` | Route-ове |
| `frontend/src/pages/AccountingPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |
| `frontend/src/pages/SchedulesPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |
| `frontend/src/pages/UserManagementPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |
| `frontend/src/pages/LeavesPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |
| `frontend/src/pages/NotificationsPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |
| `frontend/src/pages/AdminDashboardPage.tsx` | Премахни Tabs, добави поддръжка на tab проп |

---

## 8. Бележки

- Запази съществуващата функционалност
- Направи промените backward-compatible
- Използвай TypeScript типове за по-добра поддръжка
- Тествай след всяка стъпка
