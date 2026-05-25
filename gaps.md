# Gaps and Issues Identified

## 1. Permission System Issues (Severity: HIGH)
- **Dual Systems**: codebase has TWO completely different permission systems that don't work together:
  - Legacy: `current_user.role.name` hard-coded checks (328 occurrences)
  - New RBAC: `PermissionService.check_permission()` with permission strings
- **Decorator Not Used**: `require_permission` dependency is defined in `auth/dependencies.py` but never used in GraphQL mutations
- **No Company Scoping**: permission checks don't validate multi-company access via `CompanyRoleAssignment`; most checks use `current_user.company_id`
- **Inconsistent Error Handling**: mixes `PermissionDeniedException`, `AuthenticationException`, raw `HTTPException`
- **Cache Invalidation**: in-memory permission cache not shared across workers, lost on restart
- **Redundant Code**: `rbac_service.py` lines 114-129 contain duplicate/impossible code after return statements
- **No GraphQL Permission Middleware**: `ModuleGuardMiddleware` checks module status only, not user permissions

### Recommendations
1. Adopt one permission system (fully implement new RBAC or formalize legacy pattern)
2. Use permission decorator consistently in all mutations/queries
3. Create a GraphQL permission middleware using `PermissionService`
4. Fix company-scoping for multi-company users
5. Add Redis-based caching for production deployments


## 2. Module Management Issues
- **Inconsistent Definitions**: `is_enabled()` includes `["shifts", "users", "companies", "accounting", "confectionery"]`; `MODULE_MAPPING` maps `["shifts", "salaries", "kiosk", "integrations", "notifications", "accounting", "confectionery"]` — "users" and "companies" have no MODULE_MAPPING entries
- **Dual Enforcement**: both GraphQL middleware and explicit mutations check module enabled; explicit checks are redundant
- **Throttling Broken**: `ModuleGuardMiddleware._last_calls` is instance variable — each request gets new instance, throttling is non-functional
- **No Documentation**: no single source of truth for module list; must derive from `MODULE_MAPPING` values or database records
- **Confectionery Status Unclear**: core module (always enabled) but toggling via REST API would work inconsistently


## 3. Missing GraphQL Features
- No Strawberry mutations for user CRUD (`createUser`, `updateUser`, `deleteUser`) — referenced in middleware but unimplemented
- User mutations handled only via REST endpoints (`/auth/register`, `/auth/token`, etc.)
- GraphQL inputs (`UserCreateInput`, `UpdateUserInput`, etc.) are defined but never used
- GraphQL queries for reading user data (`me`, `users`, `all_users`, `user`) are implemented


## 4. Missing Data & Data Quality

### Missing Data
| Category | Missing Data | Value |
|---|---|---|
| Time | Break start/end timestamps | Break pattern analysis |
| Time | Clock-in method/device | Location-based behavior |
| Productivity | Quality inspection scores | Quality vs speed |
| Productivity | Rework/revision counts | First-pass yield |
| HR | Performance review scores | Performance tracking |
| HR | Disciplinary action records | Compliance |
| HR | Training/certification records | Skill development |
| HR | Exit interview data | Turnover prediction |
| Payroll | Salary benchmarking | Competitiveness |
| Payroll | Expense reimbursement | Spending behavior |
| Fleet | GPS track points | Route optimization |
| Fleet | Speed data | Driving safety |
| Fleet | Idle time | Fuel waste |
| Access | Visitor logs | External interactions |
| Access | Badge assignment history | Credential lifecycle |
| Communication | Email/message content | Sentiment analysis |
| Communication | Meeting calendar | Collaboration patterns |
| System | Page navigation logs | Workflow efficiency |
| System | Error/failure logs | Frustration indicators |
| System | Search query logs | Information needs |
| General | Peer feedback/ratings | Social dynamics |
| General | Customer satisfaction | External impact |
| General | Safety incident reports | Risk behavior |
| General | Equipment usage logs | Resource utilization |

### Data Quality Issues
| Issue | Affected Models | Impact |
|---|---|---|
| Nullable timestamps | TimeLog.end_time, ProductionTask.* | Incomplete sessions skew durations |
| String-based enums | TimeLog.type, Shift.shift_type, LeaveRequest.leave_type | No validation, typo-prone |
| Legacy dual fields | User.job_title vs Position.title | Sync risk |
| Encrypted fields | User.egn, User.iban | Cannot use in analytics |
| Missing foreign keys | AccessLog.user_id is String | Cannot join reliably |
| No soft deletes | Most models lack deleted_at | Lost historical records |
| No audit trails | Only AuditLog and OperationLog exist | Changes not tracked |
| Inconsistent date types | Mix of Date and DateTime | Timezone issues |
| No data validation | Numeric fields accept any value | Outliers possible |
| Missing audit fields | Many models lack created_by/updated_by | Cannot track authorship |
| Decimal precision | Numeric(10,2) insufficient | Rounding errors |

### Privacy Concerns
| Category | Risk | Concerns |
|---|---|---|
| Time & Attendance | HIGH | GPS location tracking, work pattern surveillance |
| Productivity | HIGH | Performance monitoring, peer comparison |
| HR & Contracts | CRITICAL | EGN (national ID), IBAN, health data |
| Payroll | CRITICAL | Full financial profile, debt, tax info |
| Fleet | MEDIUM-HIGH | Location tracking, driving behavior |
| Warehouse | MEDIUM | Health inference from allergen tracking |
| Access Control | HIGH | Movement tracking, zone patterns |
| Notifications | LOW-MEDIUM | Communication preferences |
| User/Org | HIGH | Role hierarchy, permission mapping |
| System Usage | HIGH | IP addresses, device fingerprinting |

### GDPR-Specific Concerns (Bulgaria/EU)
- EGN — special category data, requires explicit consent
- Health data (sick leave, maternity) — special category under Art. 9
- GPS coordinates — requires legal basis
- No data retention policies in models
- No soft-delete pattern for right to erasure
- No export mechanism for data portability


## 5. Authentication & Session Issues
Full analysis of `"Няма данни за потребителя."` appearing instead of login redirect.

### Token Lifetimes
| Token | Lifetime | Location |
|---|---|---|
| Access Token | 2 minutes | `backend/config.py` |
| Refresh Token | 7 days | `backend/auth/jwt_utils.py` |
| Idle Timeout | 15 minutes | `frontend/.../useSessionActivity.ts` |
| Auto-refresh | 5 minutes before idle | same |

### Root Cause Chain
1. Access token expires in 2 minutes
2. `me` GraphQL query returns `null` instead of throwing error when unauthenticated
3. Apollo error handler only fires on errors — `null` data is NOT an error
4. Token refresh never triggers → user sees "Няма данни за потребителя."

### Inconsistent Component Behavior
| Component | Behavior on `me: null` |
|---|---|
| SettingsPage | Shows warning (what user sees) |
| DashboardPage | Redirects to /login ✅ |
| AdminRoute | Redirects to /login ✅ |
| MainLayout | No redirect — renders with user=undefined |
| LeavesPage | Redirects to /login ✅ |
| Header | Shows "Вход" button |

### Session Hook Flaw
`shouldRefresh()` is called only when user becomes active after being idle — does NOT proactively refresh before 2-minute access token expires.

### Recommended Fixes (Priority Order)
1. **Backend**: Make `me` resolver throw `AuthenticationException` instead of returning `None` — fixes for ALL components
2. **Frontend**: Fix SettingsPage to redirect instead of showing warning
3. **Config**: Increase `ACCESS_TOKEN_EXPIRE_MINUTES` from 2 to 15-30
4. **Frontend**: Add global auth guard in MainLayout
5. **Frontend**: Add ApolloLink that catches `me: null` responses


## 6. Company Creation Flow Bugs

### Missing `await db.commit()` in Mutations
The schema has `autocommit=False`, but these mutations never commit:

| Mutation | File | Status |
|---|---|---|
| `create_company` | `backend/graphql/mutations/company.py` | MISSING commit — companies silently rolled back |
| `update_company` | `backend/graphql/mutations/company.py` | MISSING commit — updates silently rolled back |
| `update_department` | `backend/graphql/mutations/company.py` | MISSING commit — updates silently rolled back |

Proof: `create_department` and `create_position` DO have `await db.commit()`.

### Also Affected
- `update_company` passes `city=input.city` but `CompanyUpdateInput` has no `city` field and model has no `city` column
- Session is configured with `autocommit=False`, `autoflush=False` — every mutation MUST explicitly commit


## 7. Conflicts & Issues (Schedules & Templates)
### Critical
1. **create_shift parameter mismatch**: Frontend sends `toleranceMinutes`, `breakDurationMinutes`, `payMultiplier` — backend mutation only accepts `name`, `start_time`, `end_time`; extra params silently ignored
2. **No company isolation on Shift**: `Shift` has `company_id` column (via migration) but no field in model; `get_all_shifts(company_id=...)` should filter but check if it works
3. **UniqueConstraint not in model**: DB-level constraint exists via migration but not declared in `WorkSchedule.__table_args__`
4. **Duplicate template service**: `ScheduleTemplateService` exists but mutations use `time_repo` directly; service is never used
5. **ScheduleTemplateItemInput mismatch**: Frontend sends `{dayIndex, shiftId}` (camelCase) — backend input defines `day_of_week`, `start_time`, `end_time`, `break_minutes` (different fields)
6. **No validation on shift times**: No check that `end_time > start_time`; no handling for overnight shifts

### Minor
7. `WorkSchedule.shift` resolver uses direct DB call instead of dataloader → N+1 queries
8. No `update_schedule_template` mutation (create/delete only)
9. No bulk delete schedules mutation
10. `apply_schedule_template` accepts single `userId` — frontend suggests multi-user support
11. Frontend type mismatch: shifts typed as `WorkSchedule` instead of `Shift` in dropdown
12. No audit logging for schedule changes


## 8. Implementation Status (Schedule & Shift Feature)
### Models
| # | Item | Status |
|---|---|---|
| 1.1 | Shift model has `company_id` | ✅ IMPLEMENTED |
| 1.2 | Shift model has `overnight` field | ❌ NOT IMPLEMENTED |
| 1.3 | WorkSchedule UniqueConstraint in model | ❌ Only in migration, not model |
| 1.4 | ScheduleAuditLog model | ❌ NOT IMPLEMENTED |

### Mutations
| # | Item | Status |
|---|---|---|
| 2.1 | create_shift passes all params | ✅ PARTIALLY (no overnight) |
| 2.2 | update_schedule_template mutation | ❌ NOT IMPLEMENTED |
| 2.3 | bulk_delete_schedules mutation | ❌ NOT IMPLEMENTED |
| 2.4 | ScheduleTemplateService removed | ❌ Still exists (unused) |

### Repository (time_repo.py)
| # | Item | Status |
|---|---|---|
| 3.1 | create_shift has all params | ✅ IMPLEMENTED |
| 3.2 | get_all_shifts filters by company_id | ✅ IMPLEMENTED (single method) |
| 3.3 | create_or_update_schedule uses ON CONFLICT | ✅ IMPLEMENTED (uses `pg_insert().on_conflict_do_update()`) |
| 3.4 | update_schedule_template method | ❌ NOT IMPLEMENTED |
| 3.5 | bulk_delete_schedules method | ✅ IMPLEMENTED (exists in repo) |
| 3.6 | get_template_preview method | ❌ Only in service, not repo |

### Queries
| # | Item | Status |
|---|---|---|
| 4.1 | shifts query filters by company_id | ✅ IMPLEMENTED |
| 4.2 | template_preview query | ❌ NOT IMPLEMENTED |

### Other
| # | Item | Status |
|---|---|---|
| 5.1 | ScheduleTemplateItemInput defined | ✅ IMPLEMENTED |
| 6.1 | ShiftLoader dataloader | ❌ NOT IMPLEMENTED |
| 7.1 | WorkSchedule type uses DataLoader | ❌ Uses direct DB call (N+1) |
| Mig-1 | add_company_id_to_shifts migration | ✅ EXISTS |
| Mig-2 | add_unique_constraint migration | ✅ EXISTS |
| Mig-3 | add_overnight_to_shifts migration | ❌ MISSING |
| Mig-4 | add_schedule_audit_log migration | ❌ MISSING |

### Key Findings
1. **ScheduleTemplateService is redundant** — exists but unused; should be deleted or consolidated
2. **No overnight support** — model field, migration, and mutation param all missing
3. **No audit logging** for schedule changes
4. **No Shift dataloader** → N+1 queries in WorkSchedule type


## 9. Architectural Observations
1. **GraphQL is primary API** — mutations were a single 8,488-line file (now split into `mutations/`). Core of business operations.
2. **Single-file antipatterns**: `models.py` (3,079 lines), `crud_legacy.py` (3,231 lines), `types.py` (4,630 lines) — still monoliths
3. **Schema duplication**: Pydantic schemas + Strawberry types/inputs define same fields independently
4. **No test fixtures** — no active `conftest.py`
5. **Dual DB configs**: `database.py` and `database_optimized.py` — unclear which is active
6. **JWT dual implementation**: `jwt_utils.py` (basic) and `jwt_utils_rbac.py` (with permissions) — migration in progress
7. **Bulgarian i18n baked in** — all messages hardcoded in Bulgarian
8. **Legacy code in transition**: `crud_legacy.py` still imported via `__getattr__` for backward compatibility
9. **LockedSession pattern**: wraps each session with `asyncio.Lock()` — limits performance, prevents `InterfaceError`
10. **No DI framework** — module-level singleton services
11. **Version**: 3.4.7.0 (hardcoded)
12. **Pinned dependencies**: fastapi==0.128.0, strawberry-graphql==0.288.2, SQLAlchemy==2.0.45


## 10. Frontend Issues (AccountingPage)
- **Unused imports**: `Tabs` and `Tab` from MUI imported but never rendered
- **No tab navigation UI**: page relies on URL-based navigation (`tab` prop); no visible tab bar
- **Flat structure**: all 14 tabs at same level — no grouping or sub-navigation
- **Two shared dialogs**: invoice create/edit and details shared across tabs 0, 1, 7
- **Inline helper**: custom `ValidatedTextField` component defined inline (lines 80-165)

### ERP Feature Gaps
Missing for "complete" ERP: reporting/BI, CRM, project management, budgeting, full email delivery, document management workflows, multi-currency, configurable approval workflow engine. Email sending and broadcast notifications have partial implementations with TODOs remaining.


Приоритет 1 (P0 - лесна победа):
1. Замени threading.Lock с BackgroundTasks в backend/routers/deploy.py
Приоритет 2 (P1 - бързи подобрения):
2. Създай backend/tests/conftest.py с httpx AsyncClient fixture
3. Премести 10-те root-level тест файла в backend/tests/
Приоритет 3 (P2 - структурни промени):
4. Раздели backend/database/models.py на модули (user.py, payroll.py, time_tracking.py, etc.)
5. Създай backend/dependencies/ с resource validators
6. Планирай миграция на crud_legacy.py към repository pattern
Приоритет 4 (P3 - конфигурация):
7. Отключи file_template в alembic.ini
8. Добави MetaData(naming_convention=...) в database.py
9. Раздели config.py на domain-specific Settings (AuthConfig, DatabaseConfig, etc.)

----------
Незавършени задачи от плана:
1. P1 (бързо): backend/tests/conftest.py + преместване на 10 тестови файла в backend/tests/
2. P2 (API): Cursor-based pagination за list queries
3. P2 (API): DataLoader за N+1 query prevention
4. P2 (API): Input validation hardening (Pydantic validators)
5. P2 (рефакторинг): Разделяне на models.py (180KB) по домейни
6. P3: Standardized mutation responses + query complexity limiting