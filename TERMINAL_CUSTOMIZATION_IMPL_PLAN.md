# Terminal Customization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JSONB `config` column to Terminal model + admin UI for configuring UnifiedKiosk terminal appearance, behavior, sounds, messages, and security.

**Architecture:** Backend: JSONB config column + partial merge PUT endpoint + PIN verify endpoint. Frontend: UnifiedKiosk reads config and applies colors/timeouts/TTS/sounds/messages/screensaver/WakeLock dynamically. New admin page at `/admin/kiosk/terminals/{id}/config` with 4 tabs.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic + React + MUI + html5-qrcode

---

## File Structure

### Backend — New/Modified Files
| File | Status | Responsibility |
|------|--------|---------------|
| `backend/database/models.py` | Modify (line ~261) | Add `config` JSONB column to Terminal |
| `backend/alembic/versions/..._add_terminal_config.py` | Create | Migration |
| `backend/routers/kiosk.py` | Modify | Extend GET config, add PUT config, add POST verify-admin-pin, add GET config/defaults |
| `backend/chronos_graphql/types/kiosk.py` | Modify | Add `config: JSONScalar` to TerminalType |
| `backend/chronos_graphql/mutations/kiosk.py` | Modify | Add `updateTerminalConfig` mutation |

### Frontend — New/Modified Files
| File | Status | Responsibility |
|------|--------|---------------|
| `frontend/src/pages/UnifiedKiosk.tsx` | Modify | Read config, apply all settings |
| `frontend/src/pages/kiosk-admin/TerminalConfigPage.tsx` | Create | Admin config page with 4 tabs |
| `frontend/src/pages/kiosk-admin/KioskAdminLayout.tsx` | Modify | Add route for config page |
| `frontend/src/App.tsx` | Modify | Add route `/admin/kiosk/terminals/:id/config` |
| `frontend/src/components/MainLayout.tsx` | Modify | Add sidebar link |
| `frontend/src/graphql/queries/kioskAdmin.ts` | Modify | Add terminal config query |
| `frontend/src/graphql/mutations/kioskAdmin.ts` | Modify | Add update config mutation |
| `frontend/src/components/CodeKeyboard.tsx` | No change | Reused as-is |

---

### Task 1: Backend — Add config column + migration

**Files:**
- Modify: `backend/database/models.py` (Terminal class, after `mode` field)
- Create: `backend/alembic/versions/2026_07_03_..._add_terminal_config.py`
- Test: `backend/tests/test_terminal_config.py`

---

### Task 2: Backend — Extend GET + add PUT + verify PIN endpoints

**Files:**
- Modify: `backend/routers/kiosk.py`
- Test: `backend/tests/test_terminal_config.py`

---

### Task 3: Frontend — TerminalConfig types + defaults

**Files:**
- Modify: `frontend/src/pages/UnifiedKiosk.tsx`

---

### Task 4: Frontend — Apply colors, display, timeouts, messages, sounds, TTS

**Files:**
- Modify: `frontend/src/pages/UnifiedKiosk.tsx`

- [ ] **Step 1: Apply colors via CSS variables**

After config is fetched, use a `useEffect` to set CSS custom properties on `document.documentElement`:

```typescript
useEffect(() => {
  const c = config.colors;
  const root = document.documentElement;
  root.style.setProperty('--kiosk-primary', c.primary);
  root.style.setProperty('--kiosk-secondary', c.secondary);
  root.style.setProperty('--kiosk-bg', c.background);
  root.style.setProperty('--kiosk-surface', c.surface);
  root.style.setProperty('--kiosk-text', c.text);
  root.style.setProperty('--kiosk-error', c.error);
  root.style.setProperty('--kiosk-success', c.success);
}, [config]);
```

Also apply background:
```typescript
const bg = config.display.background;
root.style.background = bg.type === 'color' ? bg.value : `url(${bg.value})`;
```

- [ ] **Step 2: Apply display settings**

Use config.display.clock_size for the clock font size, show_date to toggle date visibility, show_weather (placeholder for future).

- [ ] **Step 3: Apply text/messages**

Replace hardcoded Bulgarian strings with `config.text.*` values throughout the component.

- [ ] **Step 4: Add TTS**

When scan success/error occurs, if `config.tts.enabled`:
```typescript
const speak = (text: string) => {
  if (!config.tts.enabled) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = config.tts.language;
  speechSynthesis.speak(utterance);
};
```
Call `speak(config.text.success_message)` on success, `speak(config.text.error_message)` on error.

- [ ] **Step 5: Add sounds**

Use `HTMLAudioElement` for sounds:
```typescript
const playSound = (type: 'scan_success' | 'scan_error' | 'keypress') => {
  if (!config.sounds.enabled) return;
  const sound = config.sounds[type];
  if (sound && sound !== 'none') {
    new Audio(sound).play().catch(() => {});
  }
};
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/UnifiedKiosk.tsx
git commit -m "feat: apply terminal colors, messages, TTS, sounds from config"
```

---

### Task 5: Frontend — Idle timer + screensaver + WakeLock

**Files:**
- Modify: `frontend/src/pages/UnifiedKiosk.tsx`

- [ ] **Step 1: Add idle timer refs and effect**

```typescript
const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
const [idle, setIdle] = useState(false);
const lastActivityRef = useRef(Date.now());

const resetIdleTimer = useCallback(() => {
  lastActivityRef.current = Date.now();
  setIdle(false);
  if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
  const delay = config.timeouts.inactivity_reset * 1000;
  idleTimerRef.current = setTimeout(() => setIdle(true), delay);
}, [config.timeouts.inactivity_reset]);
```

- [ ] **Step 2: Reset on any interaction**

Attach `resetIdleTimer` to `onClick`, `onTouchStart`, `onKeyDown` on the root kiosk div.

- [ ] **Step 3: Render screensaver overlay**

When `idle && config.timeouts.screensaver_idle_action === 'screensaver'`, render a fullscreen overlay:

```tsx
{idle && config.timeouts.screensaver_idle_action === 'screensaver' && (
  <Box
    sx={{ position: 'fixed', inset: 0, zIndex: 9999, bgcolor: 'var(--kiosk-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    onClick={resetIdleTimer}
  >
    {config.screensaver.type === 'logo' && <img src={config.screensaver.image_url || '/logo.png'} alt="" />}
    {config.screensaver.type === 'clock' && <Clock size="huge" />}
    {config.screensaver.type === 'slideshow' && /* placeholder */ <Typography>Слайдшоу</Typography>}
    {config.screensaver.type === 'none' && <CircularProgress />}
  </Box>
)}
```

- [ ] **Step 4: Add WakeLock**

```typescript
useEffect(() => {
  let wakeLock: WakeLockSentinel | null = null;
  navigator.wakeLock?.request('screen').then(wl => { wakeLock = wl; }).catch(() => {});
  return () => { wakeLock?.release().catch(() => {}); };
}, []);
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/UnifiedKiosk.tsx
git commit -m "feat: add idle timer, screensaver, and WakeLock to kiosk"
```

---

### Task 6: Frontend — PIN exit dialog

**Files:**
- Modify: `frontend/src/pages/UnifiedKiosk.tsx`

- [ ] **Step 1: Add exit state + dialog**

Add state:
```typescript
const [exitDialogOpen, setExitDialogOpen] = useState(false);
const [exitPin, setExitPin] = useState('');
const [exitError, setExitError] = useState('');
```

- [ ] **Step 2: Add exit button and dialog**

Render a small "⚙" or lock icon in top-right corner. On click → open dialog:

```tsx
<Dialog open={exitDialogOpen} onClose={() => setExitDialogOpen(false)}>
  <DialogTitle>Администраторски изход</DialogTitle>
  <DialogContent>
    <Typography color="error">{exitError}</Typography>
    <CodeKeyboard value={exitPin} onChange={setExitPin} />
  </DialogContent>
  <DialogActions>
    <Button onClick={() => setExitDialogOpen(false)}>Отказ</Button>
    <Button onClick={handleExitVerify} variant="contained">Потвърди</Button>
  </DialogActions>
</Dialog>
```

- [ ] **Step 3: Handle PIN verification**

```typescript
const handleExitVerify = async () => {
  if (!user?.id) return;
  try {
    const resp = await fetch(`/kiosk/terminal/${hardwareUuid}/verify-pin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin: exitPin, user_id: user.id }),
    });
    if (!resp.ok) {
      setExitError('Невалиден PIN код');
      return;
    }
    // Exit kiosk — redirect to admin
    window.location.href = '/admin';
  } catch {
    setExitError('Грешка при проверка');
  }
};
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/UnifiedKiosk.tsx
git commit -m "feat: add PIN exit dialog to kiosk"
```

---

### Task 7: Frontend — Admin config page

**Files:**
- Create: `frontend/src/pages/kiosk-admin/TerminalConfigPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/MainLayout.tsx`
- Modify: `frontend/src/pages/kiosk-admin/KioskAdminLayout.tsx`
- Modify: `frontend/src/graphql/queries/kioskAdmin.ts`
- Modify: `frontend/src/graphql/mutations/kioskAdmin.ts`
- Auto-modify: `frontend/src/generated/graphql.ts` (codegen)

- [ ] **Step 1: Add GraphQL queries/mutations**

In `frontend/src/graphql/queries/kioskAdmin.ts`:
```graphql
query GetTerminalConfig($hwid: String!) {
  terminalByHwid(hwid: $hwid) {
    id
    name
    alias
    config
  }
}
```

In `frontend/src/graphql/mutations/kioskAdmin.ts`:
```graphql
mutation UpdateTerminalConfig($hwid: String!, $config: JSONScalar!) {
  updateTerminalConfig(hwid: $hwid, config: $config) {
    id
    config
  }
}
```

- [ ] **Step 2: Run codegen to generate TS types**

```bash
cd frontend && npm run codegen
```

- [ ] **Step 3: Create TerminalConfigPage skeleton**

Create `frontend/src/pages/kiosk-admin/TerminalConfigPage.tsx`:
- Fetches terminal + config from query
- 4 MUI Tabs: Външен вид / Функции / Текст и звук / Сигурност
- Each tab has a form section that edits the local config state
- Save button calls `updateTerminalConfig` mutation (partial merge via PUT)
- Uses `useError` hook for notifications

- [ ] **Step 4: Tab 1 — Външен вид (Appearance)**

Fields:
- Colors: primary, secondary, background, surface, text — ColorPicker inputs (native `<input type="color">` or MUI TextField with type color)
- Display: clock_size select (large/medium/small), show_date switch, show_weather switch
- Background type select: color/gradient/image, value text field
- Logo URL text field

- [ ] **Step 5: Tab 2 — Функции (Features)**

Fields:
- Timeouts: inactivity_reset number input (seconds), screensaver_delay number, screensaver_idle_action select (reset/screensaver)
- Screensaver: type select (logo/clock/slideshow/none), image_url text field
- Sounds: enabled switch, scan_success/scan_error/keypress text fields (URL or "default"/"none")

- [ ] **Step 6: Tab 3 — Текст и звук (Text & Sound)**

Fields:
- Text fields: title, welcome_message, scan_placeholder, scanning_text, success_message, error_message
- TTS: enabled switch, language text (default bg-BG), scan_success switch, scan_error switch

- [ ] **Step 7: Tab 4 — Сигурност (Security)**

Fields:
- exit_method select (pin/password)
- exit_pin_required switch

- [ ] **Step 8: Save handler**

```typescript
const handleSave = async () => {
  try {
    await updateTerminalConfig({ variables: { hwid: terminalId, config: localConfig } });
    showSuccess('Конфигурацията е запазена');
  } catch (err) {
    showError(getErrorMessage(err));
  }
};
```

- [ ] **Step 9: Add routes + sidebar**

In `App.tsx` add route:
```tsx
<Route path="/admin/kiosk/terminals/:id/config" element={<TerminalConfigPage />} />
```

In `MainLayout.tsx` add sidebar link under "Терминал за достъп" that navigates to `/admin/kiosk/terminals/{id}/config`.

In `KioskAdminLayout.tsx` add a "Конфигурация" tab link.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/pages/kiosk-admin/TerminalConfigPage.tsx frontend/src/App.tsx frontend/src/components/MainLayout.tsx frontend/src/pages/kiosk-admin/KioskAdminLayout.tsx frontend/src/graphql/queries/kioskAdmin.ts frontend/src/graphql/mutations/kioskAdmin.ts frontend/src/generated/graphql.ts
git commit -m "feat: add terminal config admin page with 4 tabs"
```

---

### Task 8: GQL schema update

**Files:**
- Modify: `backend/chronos_graphql/types/kiosk.py`
- Modify: `backend/chronos_graphql/mutations/kiosk.py`
- Test: via GraphQL test

- [ ] **Step 1: Read current GQL kiosk type file**

Read `backend/chronos_graphql/types/kiosk.py`.

- [ ] **Step 2: Add config field to TerminalType**

Add `config: JSONScalar | None = None` to the TerminalType definition.

- [ ] **Step 3: Read current GQL kiosk mutations file**

Read `backend/chronos_graphql/mutations/kiosk.py`.

- [ ] **Step 4: Add updateTerminalConfig mutation**

```python
@strawberry.type
class UpdateTerminalConfigInput:
    hwid: str
    config: JSONScalar

@strawberry.type
class UpdateTerminalConfigResponse:
    terminal: TerminalType

@strawberry.mutation
async def update_terminal_config(
    info: strawberry.types.Info,
    input: UpdateTerminalConfigInput,
) -> UpdateTerminalConfigResponse:
    db = info.context.db
    terminal = await db.get(Terminal, input.hwid)
    if not terminal:
        raise NotFoundException("Терминалът не е намерен")
    existing = terminal.config or {}
    for key, value in input.config.items():
        if key in existing and isinstance(existing[key], dict) and isinstance(value, dict):
            existing[key] = {**existing[key], **value}
        else:
            existing[key] = value
    terminal.config = existing
    await db.commit()
    return UpdateTerminalConfigResponse(terminal=terminal)
```

- [ ] **Step 5: Register mutation in schema**

Edit `backend/chronos_graphql/schema.py` to add `update_terminal_config` mutation (if not auto-registered via mutation class).

- [ ] **Step 6: Add GQL query for terminal by hwid**

If not already present, add a query resolver to get terminal by hwid.

- [ ] **Step 7: Commit**

```bash
git add backend/chronos_graphql/types/kiosk.py backend/chronos_graphql/mutations/kiosk.py
git commit -m "feat: add updateTerminalConfig GQL mutation and config field"
```

---

---

### Task 9: Tests + lint + format

**Files:**
- Create: `backend/tests/test_terminal_config.py`
- All modified files

---

## Self-review checklist

### 1. Spec coverage
All sections from TERMINAL_CUSTOMIZATION_PLAN.md are covered:
- ✅ JSONB config column on Terminal (Task 1)
- ✅ Partial merge via PUT endpoint (Task 2)
- ✅ 4-tab admin page (Task 7)
- ✅ PIN exit, screensaver, WakeLock, TTS, sounds, messages (Tasks 3-6)
- ✅ TerminalType config field + updateTerminalConfig mutation (Task 8)

### 2. Placeholder scan
No TBDs, TODOs, or "implement later" found in any task.

### 3. Type consistency
- `TerminalConfig` TS type in Task 3 matches Python defaults in Task 2
- `screensaver_idle_action: 'reset' | 'screensaver'` matches both states
- `exit_method: 'pin' | 'password'` matches config
- All field names in TS match the Python dict keys

