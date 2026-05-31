# Chronos GraphQL Schema — Complete Report

Generated: 2026-05-30

Schema entry: `backend/graphql/schema.py` → `Query` + `Mutation` with extensions: `PermissionGuardMiddleware`, `ModuleGuardMiddleware`, `ChronosErrorExtension`

---

## STEP 4: Additional Sources

### `backend/graphql/queries_optimized.py`
- Contains `OptimizedQuery` class (742 lines) — **NOT used in the schema**. It's a standalone alternative resolver with N+1 fixes, not wired into `schema.py`.

### `backend/modules/behavioral_analysis/graphql/queries.py`
- **YES — used in schema** via `BehavioralQuery` parent class (included in Query MRO).

---

## STEP 1: QUERIES (91 fields total)

### Query (root) — `backend/graphql/queries/__init__.py:39`
Inherits: `LeaveQuery, UserQuery, NotificationsQuery, VehicleQuery, CostCenterQuery, ShiftsQuery, LogisticsQuery, ProductionQuery, AccountingQuery, ContractQuery, HardwareQuery, AccessControlQuery, PayrollQuery, BehavioralQuery, TimeTrackingQuery, SystemQuery, CompanyQuery, StatsQuery`

| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `hello` | — | `str` | `queries/__init__.py:41` |

### AccessControlQuery — `queries/access_control.py:14`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `accessZones` | `info` | `list[AccessZone]` | `access_control.py:17` |
| 2 | `accessDoors` | `info, gateway_id: int\|None=None` | `list[AccessDoor]` | `access_control.py:31` |
| 3 | `accessCodes` | `info, gateway_id: int\|None=None` | `list[AccessCode]` | `access_control.py:47` |
| 4 | `accessLogs` | `info, gateway_id: int\|None=None, limit: int=100` | `list[AccessLog]` | `access_control.py:68` |

### AccountingQuery — `queries/accounting.py:15`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `invoices` | `info, type: str\|None, status: str\|None, search: str\|None` | `list[Invoice]` | `accounting.py:17` |
| 2 | `invoice` | `info, id: int` | `Invoice\|None` | `accounting.py:51` |
| 3 | `invoiceByNumber` | `info, number: str` | `Invoice\|None` | `accounting.py:68` |
| 4 | `cashJournalEntries` | `info, start_date: str\|None, end_date: str\|None, operation_type: str\|None` | `list[CashJournalEntryType]` | `accounting.py:87` |
| 5 | `operationLogs` | `info, start_date: str\|None, end_date: str\|None, operation: str\|None, entity_type: str\|None` | `list[OperationLogType]` | `accounting.py:120` |
| 6 | `dailySummaries` | `info, start_date: str\|None, end_date: str\|None` | `list[DailySummaryType]` | `accounting.py:155` |
| 7 | `monthlySummaries` | `info, start_year: int\|None, end_year: int\|None` | `list[MonthlySummaryType]` | `accounting.py:185` |
| 8 | `yearlySummaries` | `info, start_year: int\|None, end_year: int\|None` | `list[YearlySummaryType]` | `accounting.py:213` |
| 9 | `proformaInvoices` | `info, status: str\|None, search: str\|None` | `list[ProformaInvoice]` | `accounting.py:241` |
| 10 | `invoiceCorrections` | `info, type: str\|None, status: str\|None` | `list[InvoiceCorrection]` | `accounting.py:272` |
| 11 | `invoiceCorrection` | `info, id: int` | `InvoiceCorrection\|None` | `accounting.py:302` |
| 12 | `cashReceipts` | `info, start_date: str\|None, end_date: str\|None, search: str\|None` | `list[CashReceipt]` | `accounting.py:326` |
| 13 | `cashReceipt` | `info, id: int` | `CashReceipt\|None` | `accounting.py:357` |
| 14 | `accounts` | `info, type: str\|None, parent_id: int\|None` | `list[Account]` | `accounting.py:374` |
| 15 | `account` | `info, id: int` | `Account\|None` | `accounting.py:402` |
| 16 | `accountByCode` | `info, code: str` | `Account\|None` | `accounting.py:419` |
| 17 | `accountingEntries` | `info, account_id: int\|None, start_date: str\|None, end_date: str\|None, search: str\|None` | `list[AccountingEntry]` | `accounting.py:438` |
| 18 | `accountingEntry` | `info, id: int` | `AccountingEntry\|None` | `accounting.py:475` |
| 19 | `vatRegisters` | `info, year: int\|None, month: int\|None` | `list[VATRegister]` | `accounting.py:492` |
| 20 | `vatRegister` | `info, id: int` | `VATRegister\|None` | `accounting.py:520` |

### CompanyQuery — `queries/company.py:13`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `roles` | `info` | `list[Role]` | `company.py:15` |
| 2 | `role` | `id: int, info` | `Role\|None` | `company.py:25` |
| 3 | `companies` | `info` | `list[Company]` | `company.py:36` |
| 4 | `departments` | `info, company_id: int\|None` | `list[Department]` | `company.py:46` |
| 5 | `positions` | `info, department_id: int\|None` | `list[Position]` | `company.py:59` |

### ContractQuery — `queries/contract.py:10`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `employmentContracts` | `info, company_id: int\|None, user_id: int\|None, status: str\|None` | `list[EmploymentContract]` | `contract.py:11` |
| 2 | `employmentContract` | `info, id: int` | `EmploymentContract\|None` | `contract.py:56` |
| 3 | `contractTemplates` | `info` | `list[ContractTemplate]` | `contract.py:81` |
| 4 | `contractTemplate` | `info, id: int` | `ContractTemplate\|None` | `contract.py:100` |
| 5 | `contractTemplateVersions` | `info, template_id: int` | `list[ContractTemplateVersion]` | `contract.py:113` |
| 6 | `annexTemplates` | `info` | `list[AnnexTemplate]` | `contract.py:129` |
| 7 | `annexTemplate` | `info, id: int` | `AnnexTemplate\|None` | `contract.py:148` |
| 8 | `annexTemplateVersions` | `info, template_id: int` | `list[AnnexTemplateVersion]` | `contract.py:161` |
| 9 | `annexes` | `info, status: str\|None` | `list[ContractAnnex]` | `contract.py:177` |
| 10 | `clauseTemplates` | `info, category: str\|None` | `list[ClauseTemplate]` | `contract.py:199` |

### CostCenterQuery — `queries/cost_center.py:17`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `costCenters` | `info, company_id: int\|None` | `list[VehicleCostCenter]` | `cost_center.py:19` |
| 2 | `costCenter` | `id: int, info` | `VehicleCostCenter\|None` | `cost_center.py:38` |

### HardwareQuery — `queries/hardware.py:12`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `gateways` | `info, is_active: bool\|None` | `list[Gateway]` | `hardware.py:15` |
| 2 | `gateway` | `info, id: int` | `Gateway\|None` | `hardware.py:36` |
| 3 | `terminals` | `info, gateway_id: int\|None, is_active: bool\|None` | `list[Terminal]` | `hardware.py:50` |
| 4 | `terminal` | `info, id: int` | `Terminal\|None` | `hardware.py:82` |
| 5 | `gatewayStats` | `info` | `GatewayStats` | `hardware.py:96` |
| 6 | `printers` | `info, gateway_id: int` | `list[Printer]` | `hardware.py:127` |

### LeaveQuery — `queries/leave.py:11`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `myLeaveRequests` | `info` | `list[LeaveRequest]` | `leave.py:13` |
| 2 | `pendingLeaveRequests` | `info` | `list[LeaveRequest]` | `leave.py:25` |
| 3 | `allLeaveRequests` | `info, status: str\|None` | `list[LeaveRequest]` | `leave.py:40` |
| 4 | `leaveBalance` | `user_id: int, year: int, info` | `LeaveBalance` | `leave.py:58` |

### LogisticsQuery — `queries/logistics.py:14`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `storageZones` | `info` | `list[StorageZone]` | `logistics.py:17` |
| 2 | `suppliers` | `info` | `list[Supplier]` | `logistics.py:31` |
| 3 | `ingredients` | `info, search: str\|None` | `list[Ingredient]` | `logistics.py:45` |
| 4 | `batches` | `info, ingredient_id: int\|None, status: str\|None="active"` | `list[Batch]` | `logistics.py:62` |
| 5 | `getFefoSuggestion` | `ingredient_id: int, quantity: Decimal, info` | `list[FefoSuggestion]` | `logistics.py:87` |
| 6 | `stockConsumptionLogs` | `info, ingredient_id: int\|None, batch_id: int\|None, start_date: date\|None, end_date: date\|None` | `list[StockConsumptionLog]` | `logistics.py:126` |
| 7 | `ingredientBatchesWithStock` | `info, ingredient_id: int` | `list[Batch]` | `logistics.py:152` |
| 8 | `inventorySessions` | `info, status: str\|None` | `list[InventorySession]` | `logistics.py:178` |
| 9 | `inventorySessionItems` | `session_id: int, info` | `list[InventoryItem]` | `logistics.py:197` |
| 10 | `inventoryByBarcode` | `barcode: str, info` | `InventoryItem\|None` | `logistics.py:215` |

### NotificationsQuery — `queries/notifications.py:14`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `myNotifications` | `info, unread_only: bool=False` | `list[Notification]` | `notifications.py:16` |
| 2 | `maintenanceStatus` | `info` | `MaintenanceStatus` | `notifications.py:28` |
| 3 | `updateSchedule` | `info` | `UpdateScheduleType\|None` | `notifications.py:65` |
| 4 | `smtpSettings` | `info` | `SmtpSettings\|None` | `notifications.py:80` |
| 5 | `notificationSettings` | `info, company_id: int` | `list[NotificationSetting]` | `notifications.py:109` |
| 6 | `notificationSetting` | `info, event_type: str, company_id: int` | `NotificationSetting\|None` | `notifications.py:121` |
| 7 | `vapidPublicKey` | `info` | `str\|None` | `notifications.py:137` |

### PayrollQuery — `queries/payroll.py:17`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `payrollLegalSettings` | `info` | `PayrollLegalSettings` | `payroll.py:20` |
| 2 | `payrollSummary` | `info, start_date: date, end_date: date, user_ids: list[int]\|None` | `list[PayrollSummaryItem]` | `payroll.py:47` |
| 3 | `globalPayrollConfig` | `info` | `GlobalPayrollConfig` | `payroll.py:170` |
| 4 | `payrollForecast` | `info, year: int, month: int` | `PayrollForecast` | `payroll.py:190` |

### ProductionQuery — `queries/production.py:9`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `recipes` | `info` | `list[Recipe]` | `production.py:12` |
| 2 | `recipesWithPrices` | `info, category_id: int\|None` | `list[Recipe]` | `production.py:26` |
| 3 | `priceHistory` | `info, recipe_id: int, limit: int=20` | `list[PriceHistory]` | `production.py:48` |
| 4 | `workstations` | `info` | `list[Workstation]` | `production.py:76` |
| 5 | `productionOrders` | `info, status: str\|None` | `list[ProductionOrder]` | `production.py:90` |
| 6 | `terminalOrders` | `info, workstation_id: int` | `list[TerminalOrder]` | `production.py:109` |
| 7 | `productionRecords` | `info, order_id: int\|None` | `list[ProductionRecord]` | `production.py:150` |
| 8 | `productionRecordByOrder` | `order_id: int, info` | `ProductionRecord\|None` | `production.py:170` |
| 9 | `productionOrdersForDay` | `info, date: str\|None` | `list[ProductionOrder]` | `production.py:188` |
| 10 | `overdueProductionOrders` | `info` | `list[ProductionOrder]` | `production.py:224` |

### ShiftsQuery — `queries/shifts.py:13`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `shifts` | `info` | `list[Shift]` | `shifts.py:16` |
| 2 | `mySchedules` | `start_date: date, end_date: date, info` | `list[WorkSchedule]` | `shifts.py:24` |
| 3 | `workSchedules` | `info, start_date: date, end_date: date` | `list[WorkSchedule]` | `shifts.py:47` |
| 4 | `mySwapRequests` | `info` | `list[ShiftSwapRequest]` | `shifts.py:64` |
| 5 | `pendingAdminSwaps` | `info` | `list[ShiftSwapRequest]` | `shifts.py:73` |
| 6 | `scheduleTemplates` | `info` | `list[ScheduleTemplate]` | `shifts.py:82` |
| 7 | `scheduleTemplate` | `info, id: int` | `ScheduleTemplate\|None` | `shifts.py:91` |
| 8 | `templatePreview` | `template_id: int, start_date: date, end_date: date, info` | `list[TemplatePreviewItem]` | `shifts.py:102` |
| 9 | `scheduleStats` | `month: int, year: int, info` | `list[ScheduleStat]` | `shifts.py:123` |

### StatsQuery — `queries/stats.py:16`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `userDailyStats` | `info, user_id: int, start_date: date, end_date: date` | `list[DailyStat]` | `stats.py:18` |
| 2 | `myDailyStats` | `info, start_date: date, end_date: date` | `list[DailyStat]` | `stats.py:49` |
| 3 | `weeklySummary` | `info, date: date\|None, user_id: int\|None` | `WeeklySummary\|None` | `stats.py:79` |
| 4 | `monthlyWorkDays` | `info, year: int, month: int` | `MonthlyWorkDays\|None` | `stats.py:118` |
| 5 | `managementStats` | `info` | `ManagementStats` | `stats.py:135` |

### SystemQuery — `queries/system.py:12`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `kioskSecuritySettings` | `info` | `KioskSecuritySettings` | `system.py:14` |
| 2 | `googleCalendarAccount` | `info` | `GoogleCalendarAccount\|None` | `system.py:31` |
| 3 | `auditLogs` | `info, skip: int=0, limit: int=100, action: str\|None` | `list[AuditLog]` | `system.py:62` |
| 4 | `apiKeys` | `info` | `list[APIKey]` | `system.py:90` |
| 5 | `webhooks` | `info` | `list[Webhook]` | `system.py:100` |
| 6 | `modules` | `info` | `list[Module]` | `system.py:110` |
| 7 | `passwordSettings` | `info` | `PasswordSettings` | `system.py:118` |
| 8 | `deployStatus` | `info` | `DeployStatus` | `system.py:135` |
| 9 | `officeLocation` | `info` | `OfficeLocation\|None` | `system.py:147` |
| 10 | `publicHolidays` | `info, year: int\|None` | `list[PublicHoliday]` | `system.py:171` |
| 11 | `orthodoxHolidays` | `info, year: int\|None` | `list[OrthodoxHoliday]` | `system.py:184` |

### TimeTrackingQuery — `queries/time_tracking.py:14`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `activeTimeLog` | `info` | `TimeLog\|None` | `time_tracking.py:16` |
| 2 | `timeLogs` | `info, user_id: int\|None, start_date: date\|None, end_date: date\|None, limit: int=50` | `list[TimeLog]` | `time_tracking.py:27` |

### UserQuery — `queries/user.py:14`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `me` | `info` | `User` | `user.py:16` |
| 2 | `users` | `info, skip: int=0, limit: int=10, search: str\|None, sort_by: str="id", sort_order: str="asc"` | `PaginatedUsers` | `user.py:23` |
| 3 | `allUsers` | `info, search: str\|None` | `list[User]` | `user.py:52` |
| 4 | `user` | `info, id: int\|None` | `User\|None` | `user.py:68` |
| 5 | `userPresences` | `info, date: date, status: PresenceStatus\|None` | `list[UserPresence]` | `user.py:85` |
| 6 | `activeSessions` | `info, skip: int=0, limit: int=100` | `list[UserSession]` | `user.py:227` |

### VehicleQuery — `queries/vehicle.py:26`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `vehicles` | `info, company_id: int\|None` | `list[Vehicle]` | `vehicle.py:28` |
| 2 | `vehicle` | `info, id: int` | `Vehicle\|None` | `vehicle.py:45` |
| 3 | `vehicleTypes` | `info` | `list[VehicleType]` | `vehicle.py:59` |
| 4 | `vehicleDocuments` | `info, vehicle_id: int` | `list[VehicleDocument]` | `vehicle.py:65` |
| 5 | `vehicleMileage` | `info, vehicle_id: int` | `list[VehicleMileage]` | `vehicle.py:72` |
| 6 | `vehicleFuelLogs` | `info, vehicle_id: int` | `list[VehicleFuel]` | `vehicle.py:79` |
| 7 | `vehicleRepairs` | `info, vehicle_id: int` | `list[VehicleRepair]` | `vehicle.py:86` |
| 8 | `vehicleInsurances` | `info, vehicle_id: int` | `list[VehicleInsurance]` | `vehicle.py:93` |
| 9 | `vehicleInspections` | `info, vehicle_id: int` | `list[VehicleInspection]` | `vehicle.py:100` |
| 10 | `vehicleDrivers` | `info, vehicle_id: int` | `list[VehicleDriver]` | `vehicle.py:107` |
| 11 | `vehicleTrips` | `info, vehicle_id: int` | `list[VehicleTrip]` | `vehicle.py:114` |

### BehavioralQuery — `modules/behavioral_analysis/graphql/queries.py:30`
| # | Field | Params | Return | File:Line |
|---|-------|--------|--------|-----------|
| 1 | `behavioralProfiles` | `info, company_id: int\|None, user_id: int\|None` | `list[BehavioralProfileType]` | `queries.py:32` |
| 2 | `behavioralAnomalies` | `info, profile_id: int\|None, user_id: int\|None` | `list[BehavioralAnomalyType]` | `queries.py:82` |
| 3 | `behavioralRules` | `info` | `list[BehavioralRuleType]` | `queries.py:123` |
| 4 | `behavioralRecommendations` | `info, user_id: int\|None, status: str\|None` | `list[BehavioralRecommendationType]` | `queries.py:162` |
| 5 | `behavioralSettings` | `info` | `BehavioralSettingsType\|None` | `queries.py:212` |
| 6 | `organizationalHealth` | `info, period_start: str\|None, period_end: str\|None` | `list[OrganizationalHealthType]` | `queries.py:242` |
| 7 | `biasReports` | `info` | `list[BiasReportType]` | `queries.py:275` |
| 8 | `behavioralSystemHealth` | `info, company_id: int\|None` | `BehavioralSystemHealthType\|None` | `queries.py:300` |

---

## STEP 2: MUTATIONS (120+ fields total)

### Mutation (root) — `mutations/__init__.py:41`
Inherits: `VehicleMutation, CostCenterMutation, NotificationsMutation, ShiftMutation, LogisticsMutation, ProductionMutation, AccountingMutation, ContractMutation, HardwareMutation, AccessControlMutation, PayrollMutation, TrzMutation, LeaveMutation, CalendarMutation, NapReportMutation, BehavioralMutation, HRMutation, InventoryMutation, ShiftSwapMutation, CompanyMutation, SettingsMutation, UserMutation`

### AccessControlMutation — `mutations/access_control.py:20`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createAccessCode` | `input: AccessCodeInput, info` | `AccessCode` | `access_control.py:22` |
| 2 | `deleteAccessCode` | `id: int, info` | `bool` | `access_control.py:50` |
| 3 | `revokeAccessCode` | `id: int, info` | `bool` | `access_control.py:62` |
| 4 | `assignZoneToUser` | `user_id: int, zone_id: int, info` | `bool` | `access_control.py:74` |
| 5 | `removeZoneFromUser` | `user_id: int, zone_id: int, info` | `bool` | `access_control.py:95` |
| 6 | `openDoor` | `id: int, info` | `bool` | `access_control.py:111` |
| 7 | `createAccessDoor` | `input: AccessDoorInput, info` | `AccessDoor` | `access_control.py:144` |
| 8 | `deleteAccessDoor` | `id: int, info` | `bool` | `access_control.py:164` |
| 9 | `updateDoorTerminal` | `id: int, terminal_id: str\|None, terminal_mode: str\|None, info` | `AccessDoor` | `access_control.py:176` |
| 10 | `createAccessZone` | `input: AccessZoneInput, info` | `AccessZone` | `access_control.py:212` |
| 11 | `deleteAccessZone` | `id: int, info` | `bool` | `access_control.py:235` |
| 12 | `updateAccessZone` | `id: int, input: AccessZoneInput, info` | `AccessZone` | `access_control.py:247` |

### AccountingMutation — `mutations/accounting.py:31`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createBankAccount` | `input: BankAccountInput, info` | `BankAccount` | `accounting.py:33` |
| 2 | `updateBankAccount` | `id: int, input: BankAccountUpdateInput, info` | `BankAccount\|None` | `accounting.py:70` |
| 3 | `deleteBankAccount` | `id: int, info` | `bool` | `accounting.py:119` |
| 4 | `createBankTransaction` | `input: BankTransactionInput, info` | `BankTransaction` | `accounting.py:141` |
| 5 | `updateBankTransaction` | `id: int, input: BankTransactionUpdateInput, info` | `BankTransaction\|None` | `accounting.py:186` |
| 6 | `deleteBankTransaction` | `id: int, info` | `bool` | `accounting.py:242` |
| 7 | `matchBankTransaction` | `transaction_id: int, invoice_id: int, info` | `BankTransaction\|None` | `accounting.py:284` |
| 8 | `unmatchBankTransaction` | `transaction_id: int, info` | `BankTransaction\|None` | `accounting.py:314` |
| 9 | `createProformaInvoice` | `client_name, client_eik, client_address, date, items, vat_rate, discount_percent, notes, info` | `ProformaInvoice` | `accounting.py:339` |
| 10 | `convertProformaToInvoice` | `proforma_id: int, invoice_type: str, info` | `Invoice` | `accounting.py:422` |
| 11 | `createCreditNote` | `original_invoice_id: int, reason: str, correction_date: date, info` | `InvoiceCorrection` | `accounting.py:505` |
| 12 | `deleteAccount` | `id: int, info` | `bool` | `accounting.py:541` |
| 13 | `updateAccount` | `id: int, input: AccountUpdateInput, info` | `Account\|None` | `accounting.py:563` |
| 14 | `deleteCashJournalEntry` | `id: int, info` | `bool` | `accounting.py:597` |
| 15 | `deleteCashReceipt` | `id: int, info` | `bool` | `accounting.py:634` |
| 16 | `deleteInvoice` | `id: int, info` | `bool` | `accounting.py:662` |
| 17 | `validateSaftXml` | `xml_content: str, info` | `SAFTValidationResult` | `accounting.py:672` |
| 18 | `updateCompanyAccountingSettings` | `input: CompanyAccountingSettingsInput, info` | `Company` | `accounting.py:690` |
| 19 | `autoMatchBankTransactions` | `bank_account_id: int, info` | `AutoMatchResult` | `accounting.py:718` |
| 20 | `createAccount` | `input: AccountInput, info` | `Account` | `accounting.py:770` |
| 21 | `createAccountingEntry` | `input: AccountingEntryInput, info` | `AccountingEntry` | `accounting.py:796` |
| 22 | `createAdvancePayment` | `user_id: int, amount: float, payment_date: date, info, description: str\|None` | `AdvancePayment` | `accounting.py:850` |
| 23 | `createCashJournalEntry` | `input: CashJournalEntryInput, info` | `CashJournalEntryType` | `accounting.py:874` |
| 24 | `createCashReceipt` | `input: CashReceiptInput, info` | `CashReceipt` | `accounting.py:915` |
| 25 | `createInvoice` | `invoice_data: InvoiceInput, info` | `Invoice` | `accounting.py:943` |
| 26 | `createInvoiceCorrection` | `original_invoice_id, correction_type, reason, correction_date, info, create_new_invoice=False` | `InvoiceCorrection` | `accounting.py:1077` |
| 27 | `createInvoiceFromBatch` | `batch_id: int, info` | `Invoice` | `accounting.py:1234` |
| 28 | `deleteAccountingEntry` | `id: int, info` | `bool` | `accounting.py:1321` |
| 29 | `generateSaftFile` | `info, company_id: int, year: int, month: int, saft_type: str\|None="monthly"` | `SAFTFileResult` | `accounting.py:1358` |
| 30 | `generateVatRegister` | `input: VATRegisterInput, info` | `VATRegister` | `accounting.py:1400` |
| 31 | `getInvoicePdfUrl` | `invoice_id: int, info` | `str` | `accounting.py:1493` |
| 32 | `updateCashReceipt` | `id: int, input: CashReceiptUpdateInput, info` | `CashReceipt\|None` | `accounting.py:1516` |
| 33 | `updateInvoice` | `id: int, invoice_data: InvoiceInput, info` | `Invoice` | `accounting.py:1555` |

### CalendarMutation — `mutations/calendar.py:13`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `syncHolidays` | `year: int, info` | `int` | `calendar.py:15` |
| 2 | `syncOrthodoxHolidays` | `year: int, info` | `int` | `calendar.py:22` |

### CompanyMutation — `mutations/company.py:22`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createCompany` | `input: CompanyCreateInput, info` | `Company` | `company.py:24` |
| 2 | `updateCompany` | `input: CompanyUpdateInput, info` | `Company` | `company.py:42` |
| 3 | `createDepartment` | `input: DepartmentCreateInput, info` | `Department` | `company.py:68` |
| 4 | `updateDepartment` | `input: DepartmentUpdateInput, info` | `Department` | `company.py:79` |
| 5 | `createPosition` | `title: str, department_id: int\|None, info` | `Position` | `company.py:89` |
| 6 | `updatePosition` | `id: int, title: str, department_id: int, info` | `Position` | `company.py:101` |
| 7 | `deletePosition` | `id: int, info` | `bool` | `company.py:111` |
| 8 | `createRole` | `input: RoleCreateInput, info` | `Role` | `company.py:119` |
| 9 | `updateRole` | `id: int, name: str\|None, description: str\|None, info` | `Role` | `company.py:129` |
| 10 | `deleteRole` | `id: int, info` | `bool` | `company.py:142` |
| 11 | `updateOfficeLocation` | `latitude, longitude, radius, entry_enabled, exit_enabled, info` | `OfficeLocation` | `company.py:150` |

### ContractMutation — `mutations/contract.py:19`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `addSectionToAnnexTemplate` | `template_id: int, section: AnnexTemplateSectionInput, info` | `AnnexTemplateSection` | `contract.py:21` |
| 2 | `addSectionToContractTemplate` | `template_id: int, section: ContractTemplateSectionInput, info` | `ContractTemplateSection` | `contract.py:59` |
| 3 | `signContractAnnex` | `annex_id: int, role: str, info` | `ContractAnnex` | `contract.py:97` |
| 4 | `signEmploymentContract` | `id: int, info` | `EmploymentContract` | `contract.py:147` |
| 5 | `rejectContractAnnex` | `annex_id: int, reason: str, info` | `ContractAnnex` | `contract.py:171` |
| 6 | `restoreContractTemplateVersion` | `version_id: int, info` | `ContractTemplate` | `contract.py:192` |
| 7 | `linkEmploymentContractToUser` | `contract_id: int, user_id: int, info` | `EmploymentContract` | `contract.py:234` |

### CostCenterMutation — `mutations/cost_center.py:15`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createCostCenter` | `input: CostCenterInput, info` | `VehicleCostCenter` | `cost_center.py:17` |
| 2 | `updateCostCenter` | `input: UpdateCostCenterInput, info` | `VehicleCostCenter` | `cost_center.py:42` |
| 3 | `deleteCostCenter` | `id: int, info` | `bool` | `cost_center.py:62` |

### HardwareMutation — `mutations/hardware.py:16`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `updateTerminal` | `id: int, alias: str\|None, mode: str\|None, is_active: bool\|None, info` | `Terminal` | `hardware.py:19` |
| 2 | `deleteTerminal` | `id: int, info` | `bool` | `hardware.py:48` |
| 3 | `updateGateway` | `id: int, alias: str\|None, company_id: int\|None, info` | `Gateway` | `hardware.py:61` |

### HRMutation — `mutations/hr.py:21`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createEmploymentContract` | `input: EmploymentContractCreateInput, info` | `EmploymentContract` | `hr.py:23` |
| 2 | `generateContractNumber` | `company_id: int, info` | `str` | `hr.py:89` |
| 3 | `getContractPdfUrl` | `contract_id: int, info` | `str` | `hr.py:120` |
| 4 | `createContractTemplate` | `name, description, contract_type, work_hours_per_week, probation_months, salary_calculation_type, payment_day, night_work_rate, overtime_rate, holiday_rate, work_class, position_id, department_id, base_salary, clause_ids, info` | `ContractTemplate` | `hr.py:141` |
| 5 | `updateContractTemplate` | `id, name, description, contract_type, work_hours_per_week, probation_months, salary_calculation_type, payment_day, night_work_rate, overtime_rate, holiday_rate, work_class, change_note, info` | `ContractTemplate` | `hr.py:269` |
| 6 | `deleteContractTemplate` | `id: int, info` | `bool` | `hr.py:358` |
| 7 | `createClauseTemplate` | `title, content, category, info` | `ClauseTemplate` | `hr.py:378` |
| 8 | `updateClauseTemplate` | `id, title, content, category, info` | `ClauseTemplate` | `hr.py:413` |
| 9 | `deleteClauseTemplate` | `id: int, info` | `bool` | `hr.py:448` |
| 10 | `createAnnexTemplate` | `name, description, change_type, new_base_salary, new_work_hours_per_week, new_night_work_rate, new_overtime_rate, new_holiday_rate, info` | `AnnexTemplate` | `hr.py:468` |
| 11 | `updateSectionInAnnexTemplate` | `section_id: int, section: AnnexTemplateSectionUpdateInput, info` | `AnnexTemplateSection` | `hr.py:556` |
| 12 | `deleteSectionFromAnnexTemplate` | `section_id: int, info` | `bool` | `hr.py:595` |
| 13 | `deleteAnnexTemplate` | `id: int, info` | `bool` | `hr.py:615` |
| 14 | `getAnnexPdfUrl` | `annex_id: int, info` | `str` | `hr.py:635` |
| 15 | `createContractAnnex` | `contract_id, effective_date, annex_number, base_salary, position_id, work_hours_per_week, night_work_rate, overtime_rate, holiday_rate, info` | `ContractAnnex` | `hr.py:656` |
| 16 | `updateSectionInContractTemplate` | `section_id: int, section: ContractTemplateSectionUpdateInput, info` | `ContractTemplateSection` | `hr.py:693` |
| 17 | `deleteSectionFromContractTemplate` | `section_id: int, info` | `bool` | `hr.py:732` |

### InventoryMutation — `mutations/inventory.py:21`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createIngredient` | `input: IngredientInput, info` | `Ingredient` | `inventory.py:23` |
| 2 | `updateIngredient` | `input: IngredientInput, info` | `Ingredient` | `inventory.py:56` |
| 3 | `createStorageZone` | `input: StorageZoneInput, info` | `StorageZone` | `inventory.py:83` |
| 4 | `updateStorageZone` | `input: UpdateStorageZoneInput, info` | `StorageZone` | `inventory.py:114` |
| 5 | `addBatch` | `input: BatchInput, info` | `Batch` | `inventory.py:137` |
| 6 | `updateBatch` | `input: BatchInput, info` | `Batch` | `inventory.py:163` |
| 7 | `updateBatchStatus` | `id: int, status: str, info` | `Batch` | `inventory.py:187` |
| 8 | `startInventorySession` | `info` | `InventorySession` | `inventory.py:204` |
| 9 | `completeInventorySession` | `session_id: int, info` | `InventorySession` | `inventory.py:222` |
| 10 | `addInventoryItem` | `session_id: int, ingredient_id: int, found_quantity: float, info` | `InventoryItem` | `inventory.py:298` |
| 11 | `consumeFromBatch` | `batch_id: int, quantity: Decimal, reason: str, info, notes: str\|None` | `Batch` | `inventory.py:361` |
| 12 | `bulkAddBatches` | `invoice_number, supplier_id, date, items: list[BatchInput], create_invoice: bool, info` | `list[Batch]` | `inventory.py:404` |

### LeaveMutation — `mutations/leave.py:27`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `requestLeave` | `leave_input: LeaveRequestInput, info` | `LeaveRequest` | `leave.py:28` |
| 2 | `deleteLeaveRequest` | `id: int, info` | `bool` | `leave.py:48` |
| 3 | `cancelLeaveRequest` | `request_id: int, info` | `LeaveRequest` | `leave.py:58` |
| 4 | `approveLeave` | `info, request_id: int, admin_comment: str=None, employer_top_up: bool=False` | `LeaveRequest` | `leave.py:73` |
| 5 | `rejectLeave` | `info, request_id: int, admin_comment: str=None` | `LeaveRequest` | `leave.py:91` |
| 6 | `updateLeaveRequestStatus` | `input: UpdateLeaveRequestStatusInput, info` | `LeaveRequest` | `leave.py:108` |
| 7 | `attachLeaveDocument` | `request_id: int, file: Upload, info` | `LeaveRequest` | `leave.py:133` |

### LogisticsMutation — `mutations/logistics.py:23`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `approveBusinessTrip` | `trip_id: int, approved: bool, notes: str\|None, info` | `BusinessTrip` | `logistics.py:25` |
| 2 | `createSupplier` | `input: SupplierInput, info` | `Supplier` | `logistics.py:55` |
| 3 | `updateSupplier` | `input: UpdateSupplierInput, info` | `Supplier` | `logistics.py:84` |
| 4 | `createServiceLoan` | `user_id, total_amount, installments_count, start_date, description, info` | `ServiceLoan` | `logistics.py:106` |

### NapReportMutation — `mutations/nap_reports.py:14`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `generateAnnualInsuranceReport` | `info, year: int` | `AnnualInsuranceReport` | `nap_reports.py:17` |
| 2 | `generateIncomeReportByType` | `info, year: int` | `IncomeReportByType` | `nap_reports.py:34` |
| 3 | `generateServiceBookExport` | `info, year: int` | `ServiceBookExport` | `nap_reports.py:58` |
| 4 | `generateMonthlyDeclaration` | `info, year: int, month: int` | `MonthlyDeclarationReport` | `nap_reports.py:82` |

### NotificationsMutation — `mutations/notifications.py:22`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `markNotificationRead` | `info, id: int` | `bool` | `notifications.py:24` |
| 2 | `subscribeToPush` | `info, subscription_json: str, preferences_json: str` | `bool` | `notifications.py:37` |
| 3 | `scheduleMaintenance` | `info, input: MaintenanceInput` | `bool` | `notifications.py:82` |
| 4 | `cancelMaintenance` | `info` | `bool` | `notifications.py:116` |
| 5 | `setUpdateSchedule` | `info, input: UpdateScheduleInput` | `UpdateScheduleType` | `notifications.py:136` |
| 6 | `runUpdateNow` | `info` | `str` | `notifications.py:173` |
| 7 | `updateSmtpSettings` | `settings: SmtpSettingsInput, info` | `SmtpSettings` | `notifications.py:225` |
| 8 | `saveNotificationSetting` | `setting_data: NotificationSettingInput, info` | `NotificationSetting` | `notifications.py:254` |
| 9 | `testNotification` | `info, event_type: str, recipient_email: str\|None` | `bool` | `notifications.py:303` |

### PayrollMutation — `mutations/payroll.py:20`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `generateDailySummary` | `date: str, info` | `DailySummaryType` | `payroll.py:22` |
| 2 | `generateMonthlySummary` | `year: int, month: int, info` | `MonthlySummaryType` | `payroll.py:131` |
| 3 | `generateYearlySummary` | `year: int, info` | `YearlySummaryType` | `payroll.py:250` |
| 4 | `addBonus` | `employee_id: int, amount: Decimal, description: str, info` | `Bonus` | `payroll.py:363` |
| 5 | `removeBonus` | `bonus_id: int, info` | `bool` | `payroll.py:389` |
| 6 | `generatePayslip` | `employee_id: int, period_start: date, period_end: date, info` | `Payslip` | `payroll.py:410` |
| 7 | `generateMyPayslip` | `period_start: date, period_end: date, info` | `Payslip` | `payroll.py:432` |
| 8 | `markPayslipAsPaid` | `payslip_id: int, info` | `Payslip` | `payroll.py:453` |
| 9 | `bulkMarkPayslipsAsPaid` | `payslip_ids: list[int], info` | `list[Payslip]` | `payroll.py:477` |
| 10 | `generateSepaXml` | `payslip_ids: list[int], info` | `str` | `payroll.py:503` |

### ProductionMutation — `mutations/production.py:24`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createRecipe` | `input: RecipeInput, info` | `Recipe` | `production.py:27` |
| 2 | `deleteRecipe` | `id: int, info` | `bool` | `production.py:110` |
| 3 | `updateRecipePrice` | `recipe_id: int, input: RecipePriceUpdateInput, info` | `Recipe` | `production.py:126` |
| 4 | `calculateRecipeCost` | `recipe_id: int, info` | `RecipeCostResult` | `production.py:147` |
| 5 | `recalculateAllRecipeCosts` | `info` | `list[RecalculateResult]` | `production.py:164` |
| 6 | `createWorkstation` | `name, description, company_id, info` | `Workstation` | `production.py:183` |
| 7 | `createProductionOrder` | `input: ProductionOrderInput, info` | `ProductionOrder` | `production.py:204` |
| 8 | `updateProductionOrderStatus` | `id: int, status: str, info` | `ProductionOrder` | `production.py:270` |
| 9 | `confirmProductionOrder` | `id: int, info` | `ProductionOrder` | `production.py:289` |
| 10 | `markTaskScrap` | `id: int, info` | `ProductionTask` | `production.py:348` |
| 11 | `scrapTask` | `input: ScrapTaskInput, info` | `ProductionTask` | `production.py:391` |
| 12 | `getScrapLogs` | `task_id: int, info` | `list[ProductionScrapLog]` | `production.py:421` |
| 13 | `updateProductionTaskStatus` | `id: int, status: str, info` | `ProductionTask` | `production.py:445` |
| 14 | `reassignTaskWorkstation` | `task_id: int, new_workstation_id: int, info` | `ProductionTask` | `production.py:476` |
| 15 | `recalculateProductionDeadline` | `order_id: int, info` | `ProductionOrder` | `production.py:497` |
| 16 | `updateProductionOrderQuantity` | `order_id: int, quantity: float, info` | `ProductionOrder` | `production.py:519` |
| 17 | `generateLabel` | `order_id: int, info` | `LabelData` | `production.py:538` |
| 18 | `createQuickSale` | `input: QuickSaleInput, info` | `ProductionOrder` | `production.py:577` |

### SettingsMutation — `mutations/settings.py:22`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `setGlobalSetting` | `key: str, value: str, info` | `GlobalSetting` | `settings.py:24` |
| 2 | `updatePasswordSettings` | `settings: PasswordSettingsInput, info` | `PasswordSettings` | `settings.py:35` |
| 3 | `updateSecurityConfig` | `max_login_attempts: int, lockout_minutes: int, info` | `bool` | `settings.py:78` |
| 4 | `updateKioskSecuritySettings` | `require_gps: bool, require_same_network: bool, info` | `bool` | `settings.py:95` |
| 5 | `updateGoogleCalendarSettings` | `sync_work_schedules, sync_time_logs, sync_leave_requests, sync_public_holidays, privacy_level, info` | `bool` | `settings.py:116` |
| 6 | `disconnectGoogleCalendar` | `info` | `bool` | `settings.py:140` |
| 7 | `bulkEmergencyAction` | `action: str, info` | `bool` | `settings.py:148` |

### ShiftSwapMutation — `mutations/shift_swap.py:15`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createSwapRequest` | `requestor_schedule_id: int, target_user_id: int, target_schedule_id: int, info` | `ShiftSwapRequest` | `shift_swap.py:17` |
| 2 | `approveSwap` | `swap_id: int, approve: bool, info` | `ShiftSwapRequest` | `shift_swap.py:34` |
| 3 | `respondToSwap` | `swap_id: int, accept: bool, info` | `ShiftSwapRequest` | `shift_swap.py:48` |

### ShiftMutation — `mutations/shifts.py:151`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `clockIn` | `info, latitude: float\|None, longitude: float\|None` | `TimeLog` | `shifts.py:153` |
| 2 | `clockOut` | `info, notes: str\|None, latitude: float\|None, longitude: float\|None` | `TimeLog` | `shifts.py:174` |
| 3 | `adminClockIn` | `user_id: int, info, custom_time: datetime\|None` | `TimeLog` | `shifts.py:208` |
| 4 | `adminClockOut` | `user_id: int, info, notes: str\|None, custom_time: datetime\|None` | `TimeLog` | `shifts.py:232` |
| 5 | `createTimeLog` | `user_id, start_time, end_time, is_manual, break_duration_minutes, notes, info` | `TimeLog` | `shifts.py:265` |
| 6 | `updateTimeLog` | `id, start_time, end_time, is_manual, break_duration_minutes, notes, info` | `TimeLog` | `shifts.py:298` |
| 7 | `deleteTimeLog` | `id: int, info` | `bool` | `shifts.py:318` |
| 8 | `createManualTimeLog` | `user_id, start_time, end_time, break_duration_minutes, notes, info` | `TimeLog` | `shifts.py:329` |
| 9 | `setMonthlyWorkDays` | `input: MonthlyWorkDaysInput, info` | `MonthlyWorkDays` | `shifts.py:357` |
| 10 | `createShift` | `name, start_time, end_time, info, tolerance_minutes, break_duration_minutes, pay_multiplier, shift_type, overnight` | `Shift` | `shifts.py:366` |
| 11 | `updateShift` | `id, name, start_time, end_time, tolerance_minutes, break_duration_minutes, pay_multiplier, shift_type, overnight, info` | `Shift` | `shifts.py:395` |
| 12 | `deleteShift` | `id: int, info` | `bool` | `shifts.py:418` |
| 13 | `setWorkSchedule` | `user_id, shift_id, date, info` | `WorkSchedule\|None` | `shifts.py:427` |
| 14 | `deleteWorkSchedule` | `id: int, info` | `bool` | `shifts.py:444` |
| 15 | `bulkSetSchedule` | `user_ids, shift_id, start_date, end_date, days_of_week, info` | `bool` | `shifts.py:454` |
| 16 | `bulkDeleteSchedules` | `user_ids, start_date, end_date, info` | `int` | `shifts.py:467` |
| 17 | `copySchedulesFromMonth` | `user_id, source_month, source_year, target_month, target_year, info` | `int` | `shifts.py:491` |
| 18 | `createScheduleTemplate` | `name, description, items: list[ScheduleTemplateItemInput], info` | `ScheduleTemplate` | `shifts.py:516` |
| 19 | `updateScheduleTemplate` | `id, name, description, items, info` | `ScheduleTemplate` | `shifts.py:536` |
| 20 | `deleteScheduleTemplate` | `id: int, info` | `bool` | `shifts.py:572` |
| 21 | `applyScheduleTemplate` | `template_id, user_ids, start_date, end_date, info` | `bool` | `shifts.py:585` |

### TrzMutation — `mutations/trz.py:145`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createNightWorkBonus` | `user_id, date, hours, hourly_rate, period_id, notes, info` | `NightWorkBonus` | `trz.py:148` |
| 2 | `createOvertimeWork` | `user_id, date, hours, hourly_rate, multiplier, period_id, notes, info` | `OvertimeWork` | `trz.py:185` |
| 3 | `createBusinessTrip` | `user_id, destination, start_date, end_date, daily_allowance, accommodation, transport, other_expenses, department_id, period_id, notes, info` | `BusinessTrip` | `trz.py:224` |
| 4 | `createWorkExperience` | `user_id, company_name, start_date, end_date, position, years, months, class_level, is_current, notes, info` | `WorkExperience` | `trz.py:273` |

### UserMutation — `mutations/user.py:35`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createUser` | `userInput: UserCreateInput, info` | `User` | `user.py:37` |
| 2 | `updateUser` | `userInput: UpdateUserInput, info` | `User` | `user.py:53` |
| 3 | `deleteUser` | `id: int, info` | `bool` | `user.py:213` |
| 4 | `changePassword` | `old_password: str, new_password: str, info` | `bool` | `user.py:221` |
| 5 | `regenerateMyQrCode` | `info` | `str` | `user.py:251` |
| 6 | `invalidateUserSession` | `sessionId: int, info` | `bool` | `user.py:260` |
| 7 | `assignRoleToUser` | `user_id, company_id, role_id, info` | `bool` | `user.py:276` |
| 8 | `bulkUpdateUserAccess` | `user_ids: list[int], zone_ids: list[int], action: str, info` | `bool` | `user.py:289` |

### VehicleMutation — `mutations/vehicle.py:30`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createVehicle` | `input: VehicleCreateInput, info` | `Vehicle` | `vehicle.py:32` |
| 2 | `updateVehicle` | `id: int, input: VehicleUpdateInput, info` | `Vehicle` | `vehicle.py:67` |
| 3 | `deleteVehicle` | `id: int, info` | `bool` | `vehicle.py:102` |
| 4 | `createVehicleMileage` | `input: VehicleMileageInput, info` | `VehicleMileage` | `vehicle.py:114` |
| 5 | `createVehicleFuel` | `input: VehicleFuelInput, info` | `VehicleFuel` | `vehicle.py:131` |
| 6 | `createVehicleRepair` | `input: VehicleRepairInput, info` | `VehicleRepair` | `vehicle.py:151` |
| 7 | `createVehicleInsurance` | `input: VehicleInsuranceInput, info` | `VehicleInsurance` | `vehicle.py:169` |
| 8 | `createVehicleInspection` | `input: VehicleInspectionInput, info` | `VehicleInspection` | `vehicle.py:189` |
| 9 | `createVehicleDriver` | `input: VehicleDriverInput, info` | `VehicleDriver` | `vehicle.py:209` |
| 10 | `createVehicleTrip` | `input: VehicleTripInput, info` | `VehicleTrip` | `vehicle.py:228` |
| 11 | `deleteVehicleMileage` | `id: int, info` | `bool` | `vehicle.py:250` |
| 12 | `deleteVehicleFuel` | `id: int, info` | `bool` | `vehicle.py:259` |
| 13 | `deleteVehicleRepair` | `id: int, info` | `bool` | `vehicle.py:268` |
| 14 | `deleteVehicleInsurance` | `id: int, info` | `bool` | `vehicle.py:277` |
| 15 | `deleteVehicleInspection` | `id: int, info` | `bool` | `vehicle.py:286` |
| 16 | `deleteVehicleDriver` | `id: int, info` | `bool` | `vehicle.py:295` |
| 17 | `deleteVehicleTrip` | `id: int, info` | `bool` | `vehicle.py:304` |
| 18 | `updateVehicleMileage` | `id: int, input: VehicleMileageUpdateInput, info` | `VehicleMileage` | `vehicle.py:313` |
| 19 | `updateVehicleFuel` | `id: int, input: VehicleFuelUpdateInput, info` | `VehicleFuel` | `vehicle.py:328` |
| 20 | `updateVehicleRepair` | `id: int, input: VehicleRepairUpdateInput, info` | `VehicleRepair` | `vehicle.py:346` |
| 21 | `updateVehicleInsurance` | `id: int, input: VehicleInsuranceUpdateInput, info` | `VehicleInsurance` | `vehicle.py:363` |
| 22 | `updateVehicleInspection` | `id: int, input: VehicleInspectionUpdateInput, info` | `VehicleInspection` | `vehicle.py:382` |
| 23 | `updateVehicleDriver` | `id: int, input: VehicleDriverUpdateInput, info` | `VehicleDriver` | `vehicle.py:400` |
| 24 | `updateVehicleTrip` | `id: int, input: VehicleTripUpdateInput, info` | `VehicleTrip` | `vehicle.py:418` |

### BehavioralMutation — `modules/behavioral_analysis/graphql/mutations.py:54`
| # | Mutation | Params | Return | File:Line |
|---|----------|--------|--------|-----------|
| 1 | `createBehavioralRule` | `info, input: BehavioralRuleInput` | `BehavioralRuleType` | `mutations.py:56` |
| 2 | `updateBehavioralRule` | `info, rule_id: int, input: BehavioralRuleInput` | `BehavioralRuleType` | `mutations.py:110` |
| 3 | `deleteBehavioralRule` | `info, rule_id: int` | `bool` | `mutations.py:168` |
| 4 | `updateBehavioralSettings` | `info, input: BehavioralSettingsInput` | `BehavioralSettingsType` | `mutations.py:190` |
| 5 | `updateRecommendationStatus` | `info, recommendation_id: int, status: str, dispute_reason: str\|None, dispute_notes: str\|None` | `BehavioralRecommendationType` | `mutations.py:242` |
| 6 | `recordRecommendationFeedback` | `info, recommendation_id: int, action: str, notes: str\|None` | `RecommendationFeedbackType` | `mutations.py:291` |
| 7 | `computeOrganizationalHealth` | `info, period_start: str\|None, period_end: str\|None` | `list[OrganizationalHealthType]` | `mutations.py:324` |
| 8 | `computeBiasReport` | `info, period_start: str\|None, period_end: str\|None` | `BiasReportType` | `mutations.py:357` |

---

## STEP 3: TYPES (80+ types)

### Access Control Types — `types/access_control.py`
- **AccessZone** (`@sp.type(schemas.AccessZone)`) :12 — `id, zone_id, name, level, depends_on, required_hours_start, required_hours_end, anti_passback_enabled, anti_passback_type, anti_passback_timeout, description, is_active` + resolver: `authorized_users`
- **AccessDoor** (`@sp.type(schemas.AccessDoor)`) :38 — `id, door_id, name, zone_db_id, gateway_id, device_id, relay_number, terminal_id, terminal_mode, description, is_active, is_online, last_check` + resolvers: `zone, gateway`
- **AccessCode** (`@sp.type(schemas.AccessCode)`) :68 — `id, code, code_type, zones, uses_remaining, expires_at, created_at, last_used_at, is_active, gateway_id`
- **AccessLog** (`@sp.type(schemas.AccessLog)`) :82 — `id, timestamp, user_id, user_name, zone_id, zone_name, door_id, door_name, action, result, reason, method, terminal_id, gateway_id`

### Accounting Types — `types/accounting.py`
- **InvoiceItem** (`@sp.type`) :15 — `id, invoice_id, ingredient_id, batch_id, name, quantity, unit, unit_price, unit_price_with_vat, discount_percent, total, expiration_date, batch_number` + resolvers: `ingredient, batch`
- **Invoice** (`@sp.type`) :46 — `id, number, type, date, subtotal, discount_percent, discount_amount, vat_rate, vat_amount, total, status, company_id, created_at, document_type, griff, description, supplier_id, batch_id, client_name, client_eik, client_address, payment_method, delivery_method, due_date, payment_date, notes, created_by` + resolvers: `supplier, batch, company, items, creator`
- **CashJournalEntryType** (`@sp.type`) :104 — `id, date, operation_type, amount, description, reference_type, reference_id, created_at, created_by` + resolver: `creator`
- **OperationLogType** (`@sp.type`) :122 — `id, timestamp, operation, entity_type, entity_id, changes: JSONScalar|None, user_id` + resolver: `user`
- **DailySummaryType** (`@sp.type`) :138 — `id, date, invoices_count, incoming_invoices_count, outgoing_invoices_count, invoices_total, incoming_invoices_total, outgoing_invoices_total, cash_income, cash_expense, cash_balance, vat_collected, vat_paid, paid_invoices_count, unpaid_invoices_count, overdue_invoices_count`
- **MonthlySummaryType** (`@sp.type`) :158 — same fields + `year, month`
- **YearlySummaryType** (`@sp.type`) :179 — same fields + `year`
- **SAFTValidationResult** (`@strawberry.type`) :199 — `status, errors, warnings, is_valid`
- **SAFTFileResult** (`@strawberry.type`) :207 — `xml_content, validation_result, period_start, period_end, file_size, file_name`
- **ProformaInvoice** (`@strawberry.type`) :218 — same as Invoice + resolvers: `items, company, creator`
- **InvoiceCorrection** (`@sp.type`) :292 — `id, number, type, date, original_invoice_id, reason, status, company_id, created_by, created_at` + resolvers: `original_invoice, client_name, client_eik, subtotal, vat_rate, vat_amount, total`
- **CashReceipt** (`@sp.type`) :350 — `id, receipt_number, date, payment_type, amount, vat_amount, items_json: JSONScalar|None, fiscal_printer_id, company_id, created_by, created_at`
- **BankAccount** (`@sp.type`) :365 — `id, company_id, iban, bic, bank_name, account_type, is_default, currency, is_active, created_at`
- **BankTransaction** (`@sp.type`) :379 — `id, bank_account_id, date, amount, type, description, reference, invoice_id, matched, company_id, created_at`
- **Account** (`@sp.type`) :394 — `id, code, name, type, parent_id, company_id, opening_balance, closing_balance`
- **AutoMatchResult** (`@strawberry.type`) :406 — `matched_count, unmatched_count`
- **AccountingEntry** (`@sp.type`) :412 — `id, date, entry_number, description, debit_account_id, credit_account_id, amount, vat_amount, invoice_id, bank_transaction_id, cash_journal_id, company_id, created_by, created_at` + resolvers: `debit_account, credit_account, invoice, creator`
- **VATRegister** (`@sp.type`) :460 — `id, company_id, period_month, period_year, vat_collected_20, vat_collected_9, vat_collected_0, vat_paid_20, vat_paid_9, vat_paid_0, vat_adjustment, vat_due, vat_credit, created_at`

### Calendar Types — `types/calendar.py`
- **PublicHoliday** (`@sp.type`) :8 — `id, date, name, local_name`
- **OrthodoxHoliday** (`@sp.type`) :16 — `id, date, name, local_name, is_fixed`

### Company Types — `types/company.py`
- **Role** (`@sp.type`) :18 — `id, name, description`
- **Company** (`@sp.type`) :25 — `id, name, eik, bulstat, vat_number, address, mol_name, default_sales_account_id, default_expense_account_id, default_vat_account_id, default_customer_account_id, default_supplier_account_id, default_cash_account_id, default_bank_account_id` + resolvers: `default_sales_account, default_expense_account, default_vat_account, default_customer_account, default_supplier_account, default_cash_account, default_bank_account`
- **Department** (`@sp.type`) :99 — `id, name, company_id, manager_id` + resolvers: `company, manager`
- **Position** (`@sp.type`) :120 — `id, title, department_id` + resolvers: `department, payrolls`

### Contract Types — `types/contract.py`
- **ContractAnnex** (`@sp.type`) :10 — `id, contract_id, annex_number, effective_date, base_salary, position_id, work_hours_per_week, probation_months, night_work_rate, overtime_rate, holiday_rate, work_class, is_signed, signed_at, status, template_id, change_type, change_description, signature_requested_at, signed_by_employee, signed_by_employee_at, signed_by_employer, signed_by_employer_at, rejection_reason, created_at, updated_at` + resolver: `position`
- **EmploymentContract** (`@sp.type`) :46 — `id, user_id, company_id, contract_type, contract_number, start_date, end_date, base_salary, work_hours_per_week, probation_months, is_active, salary_calculation_type, salary_installments_count, monthly_advance_amount, tax_resident, insurance_contributor, has_income_tax, payment_day, experience_start_date, night_work_rate, overtime_rate, holiday_rate, work_class, dangerous_work, template_id, position_id, department_id, clause_ids, employee_name, employee_egn, status, signed_at, created_at, updated_at` + resolvers: `company, department, position, position_title, annexes`
- **ContractTemplateSection** (`@sp.type`) :123 — `id, template_id, version_id, title, content, order_index, is_required`
- **ContractTemplateVersion** (`@sp.type`) :134 — `id, template_id, version, contract_type, base_salary, work_hours_per_week, probation_months, salary_calculation_type, payment_day, night_work_rate, overtime_rate, holiday_rate, work_class, position_id, department_id, is_current, created_by, created_at, change_note` + resolver: `sections`
- **ContractTemplate** (`@sp.type`) :166 — `id, company_id, name, description, contract_type, base_salary, work_hours_per_week, probation_months, salary_calculation_type, payment_day, night_work_rate, overtime_rate, holiday_rate, work_class, position_id, department_id, is_active, created_at, updated_at` + resolvers: `position, department, clauses, current_version`
- **ContractTemplateClauseGQL** (`@strawberry.type`) :228 — `id, template_id, clause_id, order_index` + resolver: `clause`
- **AnnexTemplateSection** (`@sp.type`) :247 — `id, template_id, version_id, title, content, order_index, is_required`
- **AnnexTemplateVersion** (`@sp.type`) :258 — `id, template_id, version, change_type, new_base_salary, new_work_hours_per_week, new_night_work_rate, new_overtime_rate, new_holiday_rate, is_current, created_by, created_at, change_note` + resolver: `sections`
- **AnnexTemplate** (`@sp.type`) :284 — `id, company_id, name, description, change_type, new_base_salary, new_work_hours_per_week, new_night_work_rate, new_overtime_rate, new_holiday_rate, is_active, created_at, updated_at` + resolver: `current_version`
- **ClauseTemplate** (`@sp.type`) :315 — `id, company_id, title, content, category, is_active, created_at, updated_at`

### Cost Center Types — `types/cost_center.py`
- **VehicleCostCenter** (`@sp.type`) :8 — `id, name, department_id, is_active, company_id, created_at`

### Hardware Types — `types/hardware.py`
- **Gateway** (`@sp.type`) :8 — `id, name, hardware_uuid, alias, ip_address, local_hostname, terminal_port, web_port, is_active, last_heartbeat, registered_at, company_id`
- **Terminal** (`@sp.type`) :24 — `id, hardware_uuid, device_name, device_type, device_model, os_version, gateway_id, is_active, last_seen, total_scans, alias, mode`
- **Printer** (`@sp.type`) :40 — `id, name, printer_type, ip_address, port, protocol, windows_share_name, manufacturer, model, gateway_id, is_active, is_default, last_test, last_error`
- **GatewayStats** (`@strawberry.type`) :58 — `total_gateways, active_gateways, inactive_gateways, total_terminals, active_terminals, total_printers, active_printers`

### Leave Types — `types/leave.py`
- **LeaveRequest** (`@sp.type`) :12 — `id, user_id, start_date, end_date, leave_type, reason, status, created_at, admin_comment, employer_top_up` + resolver: `user`
- **LeaveBalance** (`@sp.type`) :31 — `id, user_id, year, total_days, used_days`

### Logistics Types — `types/logistics.py`
- **StorageZone** (`@sp.type`) :14 — `id, name, temp_min, temp_max, description, company_id, is_active, asset_type, zone_type`
- **Supplier** (`@sp.type`) :27 — `id, name, eik, vat_number, address, contact_person, phone, email, company_id`
- **Ingredient** (`@sp.type`) :40 — `id, name, unit, barcode, baseline_min_stock, current_price, storage_zone_id, is_perishable, expiry_warning_days, allergens: list[str], company_id, product_type` + resolvers: `storage_zone, current_stock`
- **Batch** (`@sp.type`) :73 — `id, ingredient_id, batch_number, quantity, expiry_date, status, received_at, supplier_id, invoice_number, storage_zone_id` + resolvers: `available_stock, is_expired, days_until_expiry, ingredient, supplier, storage_zone`
- **StockConsumptionLog** (`@strawberry.type`) :119 — `id, ingredient_id, batch_id, quantity, reason, production_order_id, notes, created_by, created_at` + resolvers: `ingredient, batch, creator`
- **FefoSuggestion** (`@strawberry.type`) :161 — `batch_id, batch_number, available_quantity, quantity_to_take, expiry_date, days_until_expiry`
- **InventoryItem** (`@strawberry.type`) :171 — `id, session_id, ingredient_id, ingredient_name, ingredient_unit, found_quantity, system_quantity, difference, adjusted`
- **InventorySession** (`@strawberry.type`) :198 — `id, company_id, started_by, started_at, completed_at, status, protocol_number, notes` + resolver: `items`

### NAP Report Types — `types/nap_reports.py`
- **AnnualInsuranceEmployee** :5 — `egn, name, contract_type, base_salary, insurance_base, doo_employee, zo_employee, dzpo_employee, total_contributions, sick_days, worked_months`
- **AnnualInsuranceSummary** :20 — `total_employees, total_doo, total_zo, total_dzpo, total_contributions`
- **AnnualInsuranceReport** :29 — `year, company_id, report_type, generated_at, employees, summary`
- **IncomeEntry** :39 — `type, date, gross, tax, net`
- **IncomeReportEmployee** :48 — `egn, name, incomes`
- **IncomeReportSummary** :55 — `total_employees, total_gross, total_tax`
- **IncomeReportByType** :62 — `year, company_id, report_type, generated_at, employees, summary`
- **ServiceBookPeriod** :72 — `year, month, gross, net`
- **ServiceBookContract** :80 — `type, start_date, end_date, position, base_salary, hours_per_week, status`
- **ServiceBookEmployee** :91 — `egn, name, contracts, periods`
- **ServiceBookExport** :99 — `year, company_id, report_type, generated_at, employees`
- **MonthlyDeclarationEntry** :108 — `egn, name, income_type, gross, insurance, tax, period`
- **MonthlyDeclarationSummary** :119 — `total_gross, total_insurance, total_tax`
- **MonthlyDeclarationReport** :126 — `year, month, company_id, report_type, generated_at, declarations, summary`

### Notification Types — `types/notifications.py`
- **Notification** (`@sp.type`) :11 — `id, user_id, message, is_read, created_at`
- **SmtpSettings** (`@sp.type`) :20 — `smtp_server, smtp_port, smtp_username, smtp_password, sender_email, use_tls`
- **NotificationSetting** (`@sp.type`) :30 — `id, company_id, event_type, email_enabled, push_enabled, email_template, recipients, interval_minutes, enabled, last_sent_at, created_at, updated_at`
- **MaintenanceStatus** (`@strawberry.type`) :46 — `enabled, scheduled_at, reason, minutes_until, updated_by`
- **UpdateScheduleType** (`@strawberry.type`) :65 — `id, enabled, schedule_type, scheduled_at, day_of_week, hour, minute, notify_email, last_run_at, last_run_status, last_run_output, created_at, updated_at`

### Payroll Types — `types/payroll.py`
- **SalaryInstallments** :12 — `count, amount_per_installment`
- **PayrollSummaryItem** :18 — `user_id, email, full_name, gross_amount, net_amount, tax_amount, insurance_amount, bonus_amount, advances, loan_deductions, total_deductions, net_payable, contract_type, installments`
- **PayrollLegalSettings** :36 — `max_insurance_base, employee_insurance_rate, income_tax_rate, civil_contract_costs_rate, noi_compensation_percent, employer_paid_sick_days, default_tax_resident, trz_compliance_strict_mode`
- **Payroll** (`@sp.type`) :48 — `id, hourly_rate, monthly_salary, overtime_multiplier, standard_hours_per_day, currency, annual_leave_days, tax_percent, health_insurance_percent, has_tax_deduction, has_health_insurance, user_id, position_id` + resolver: `user`
- **Payslip** (`@sp.type`) :70 — `id, user_id, period_start, period_end, total_regular_hours, total_overtime_hours, regular_amount, overtime_amount, bonus_amount, night_work_amount, trip_amount, voucher_amount, benefit_amount, sick_leave_amount, tax_amount, insurance_amount, sick_days, leave_days, doo_employee, doo_employer, zo_employee, zo_employer, dzpo_employee, dzpo_employer, tzpb_employer, gross_salary, taxable_base, income_tax, standard_deduction, total_amount, payment_status, actual_payment_date, payment_method, generated_at` + resolver: `user`
- **GlobalPayrollConfig** :112 — `id, hourly_rate, monthly_salary, overtime_multiplier, standard_hours_per_day, currency, annual_leave_days, tax_percent, health_insurance_percent, has_tax_deduction, has_health_insurance, qr_regen_interval_minutes`
- **Bonus** (`@sp.type`) :128 — `id, user_id, amount, date, description` + resolver: `user`
- **AdvancePayment** (`@sp.type`) :141 — `id, user_id, amount, payment_date, description, is_processed, created_at`
- **ServiceLoan** (`@sp.type`) :152 — `id, user_id, total_amount, installment_amount, remaining_amount, installments_count, installments_paid, start_date, description, is_active, created_at`
- **DepartmentForecast** :167 — `department_name, amount`
- **PayrollForecast** :173 — `total_amount, by_department`
- **LoanDetail** :179 — `loan_id, amount, description, remaining_before, remaining_after, date`

### Production Types — `types/production.py`
- **Workstation** (`@sp.type`) :13 — `id, name, description, company_id`
- **RecipeIngredient** (`@sp.type`) :21 — `id, recipe_id, section_id, ingredient_id, workstation_id, quantity_gross, quantity_net, waste_percentage` + resolvers: `ingredient, workstation`
- **RecipeStep** (`@sp.type`) :45 — `id, section_id, recipe_id, workstation_id, name, step_order, estimated_duration_minutes` + resolver: `workstation`
- **RecipeSection** (`@sp.type`) :61 — `id, recipe_id, section_type, name, shelf_life_days, waste_percentage, section_order` + resolvers: `ingredients, steps`
- **Recipe** (`@sp.type`) :86 — `id, name, category, description, yield_quantity, yield_unit, shelf_life_days, shelf_life_frozen_days, default_pieces, production_time_days, production_deadline_days, standard_quantity, instructions, company_id, selling_price, cost_price, markup_percentage, premium_amount, portions, last_price_update, price_calculated_at` + resolvers: `markup_amount, final_price, portion_price, sections, ingredients, steps`
- **PriceHistory** (`@sp.type`) :152 — `id, recipe_id, old_price, new_price, old_cost, new_cost, old_markup, new_markup, old_premium, new_premium, changed_by, changed_at, reason` + resolvers: `recipe, user`
- **RecipeCostResult** :179 — `recipe_id, recipe_name, cost_price, markup_amount, premium_amount, final_price, portion_price`
- **RecalculateResult** :190 — `recipe_id, recipe_name, cost_price, markup_amount, final_price, portion_price`
- **ProductionTask** (`@sp.type`) :200 — `id, order_id, workstation_id, step_id, name, status, started_at, completed_at, assigned_user_id` + resolvers: `workstation, assigned_user`
- **ProductionScrapLog** (`@sp.type`) :223 — `id, task_id, user_id, quantity, reason, created_at`
- **TerminalTask** :233 — `id, name, quantity, status`
- **TerminalOrder** :250 — `id, order_number, product_name, quantity, status, recipe_name, instructions, tasks`
- **ProductionOrder** (`@sp.type`) :275 — `id, recipe_id, quantity, due_date, production_deadline, status, notes, created_at, created_by, company_id, confirmed_at, confirmed_by` + resolvers: `recipe, tasks`
- **LabelData** :301 — `product_name, batch_number, production_date, expiry_date, allergens, storage_conditions, qr_code_content, quantity`
- **ProductionRecordIngredient** (`@sp.type`) :313 — `id, ingredient_id, batch_number, expiry_date, quantity_used, unit`
- **ProductionRecordWorker** (`@sp.type`) :323 — `id, user_id, workstation_id, started_at, completed_at`
- **ProductionRecord** (`@sp.type`) :332 — `id, order_id, confirmed_by, confirmed_at, expiry_date, notes, created_at` + resolvers: `ingredients, workers`

### Shift Types — `types/shifts.py`
- **Shift** (`@sp.type`) :13 — `id, name, start_time, end_time, overnight, tolerance_minutes, break_duration_minutes, pay_multiplier, shift_type`
- **WorkSchedule** (`@sp.type`) :26 — `id, date, user_id, shift_id` + resolvers: `user, shift`
- **TemplatePreviewItem** :45 — `date, shift_id, shift_name, day_index`
- **ScheduleStat** :53 — `user_id, user_name, assigned_days, work_days_norm, is_complete`
- **ShiftSwapRequest** (`@sp.type`) :62 — `id, requestor_id, target_user_id, requestor_schedule_id, target_schedule_id, status, created_at, updated_at` + resolvers: `requestor, target_user, requestor_schedule, target_schedule`
- **ScheduleTemplateItem** (`@sp.type`) :94 — `id, day_index, shift_id` + resolver: `shift`
- **ScheduleTemplate** (`@sp.type`) :110 — `id, company_id, name, description, created_at` + resolver: `items`

### Stats Types — `types/stats.py`
- **DailyStat** :10 — `date, total_worked_hours, regular_hours, overtime_hours, is_work_day, shift_name, actual_arrival, actual_departure`
- **WeeklySummary** :22 — `start_date, end_date, total_regular_hours, total_overtime_hours, target_hours, debt_hours, surplus_hours, status_message`
- **MonthlyWorkDays** (`@sp.type`) :34 — `id, year, month, days_count`
- **OvertimeStat** :42 — `month, amount`
- **LatenessStat** :48 — `user_name, count`
- **ManagementStats** :54 — `overtime_by_month, lateness_by_user`

### System Types — `types/system.py`
- **GoogleCalendarSyncSettings** (`@sp.type`) :12 — `id, account_id, calendar_id, sync_work_schedules, sync_time_logs, sync_leave_requests, sync_public_holidays, sync_direction, sync_frequency_minutes, privacy_level`
- **KioskSecuritySettings** :25 — `require_gps, require_same_network`
- **GoogleCalendarAccount** (`@sp.type`) :30 — `id, email, is_active` + resolver: `sync_settings`
- **AuditLog** (`@sp.type`) :48 — `id, user_id, action, target_type, target_id, details, created_at` + resolver: `user`
- **AuditLogEdge** :66 — `node, cursor`
- **AuditLogConnection** :71 — `edges, page_info, total_count`
- **PageInfo** :78 — `has_next_page, has_previous_page, start_cursor, end_cursor`
- **APIKey** (`@sp.type`) :86 — `id, user_id, name, key_prefix, permissions, is_active, created_at, last_used_at`
- **Webhook** (`@sp.type`) :98 — `id, url, description, events, is_active, created_at`
- **Module** (`@sp.type`) :108 — `id, code, is_enabled, name, description`
- **PasswordSettings** (`@sp.type`) :117 — `min_length, max_length, require_upper, require_lower, require_digit, require_special`
- **DeployStatus** :127 — `is_deploying, status, progress, version, output`
- **PresenceStatus** (enum) :139 — `OFF_DUTY, ON_DUTY, SICK_LEAVE, PAID_LEAVE, LATE, ABSENT`
- **OfficeLocation** :149 — `latitude, longitude, radius, entry_enabled, exit_enabled`
- **GlobalSetting** (`@sp.type`) :158 — `key, value`

### Time Tracking Types — `types/time_tracking.py`
- **TimeLog** (`@sp.type`) :9 — `id, start_time, end_time, is_manual, break_duration_minutes, type, notes, latitude, longitude, user_id` + resolver: `user`

### TRZ Types — `types/trz.py`
- **BusinessTripStatus** (enum) :11 — `PENDING, APPROVED, REJECTED, PAID`
- **NightWorkBonus** (`@sp.type`) :19 — `id, user_id, period_id, date, hours, hourly_rate, amount, is_paid, notes, created_at, updated_at` + resolver: `user`
- **OvertimeWork** (`@sp.type`) :38 — `id, user_id, period_id, date, hours, hourly_rate, multiplier, amount, is_paid, notes, created_at, updated_at` + resolver: `user`
- **BusinessTrip** (`@sp.type`) :58 — `id, user_id, period_id, department_id, destination, start_date, end_date, daily_allowance, accommodation, transport, other_expenses, total_amount, status, approved_by_id, approved_at, approved_notes, notes, created_at, updated_at` + resolvers: `user, approved_by`
- **WorkExperience** (`@sp.type`) :91 — `id, user_id, company_id, company_name, position, start_date, end_date, years, months, class_level, is_current, notes, created_at, updated_at` + resolver: `user`

### User Types — `types/user.py`
- **User** (`@sp.type`) :15 — `id, email, username, first_name, surname, last_name, phone_number, address, egn, birth_date, iban, is_active, role_id, company_id, department_id, position_id, created_at, last_login, qr_token, password_force_change, profile_picture` + resolvers: `pin, payrolls, role, company, department, position, company_name, department_name, job_title, employment_contract, is_smtp_configured, leave_balance, timelogs`
- **UserPresence** :159 — `user, shift_start, shift_end, actual_arrival, actual_departure, status: PresenceStatus, is_on_duty`
- **UserSession** (`@sp.type`) :170 — `id, user_id, ip_address, user_agent, device_type, is_active, created_at, expires_at, last_used_at` + resolver: `user`
- **PaginatedUsers** :189 — `users: list[User], total_count: int`

### Vehicle Types — `types/vehicle.py`
- **VehicleStatus** (enum) :10 — `ACTIVE, IN_REPAIR, OUT_OF_SERVICE, SOLD`
- **FuelType** (enum) :18 — `BENZIN, DIZEL, ELECTRIC, HYBRID, LNG, CNG`
- **VehicleDocumentType** (enum) :28 — `INVOICE, POLICY, INSPECTION, CONTRACT, OTHER`
- **InsuranceType** (enum) :37 — `CIVIL, KASKO, BORDER`
- **InspectionResult** (enum) :44 — `PASSED, FAILED, PENDING`
- **PreTripStatus** (enum) :51 — `PASSED, FAILED`
- **ExpenseType** (enum) :57 — `FUEL, REPAIR, INSURANCE, INSPECTION, VIGNETTE, TOLL, TAX, OTHER`
- **VehicleType** (`@sp.type`) :69 — `id, name, code`
- **VehicleDocument** (`@sp.type`) :76 — `id, vehicle_id, document_type, title, file_url, issue_date, expiry_date, notes, created_at`
- **VehicleFuelCard** (`@sp.type`) :89 — `id, vehicle_id, card_number, provider, pin, limit, is_active, expiry_date, created_at`
- **VehicleVignette** (`@sp.type`) :102 — `id, vehicle_id, vignette_type, purchase_date, valid_from, valid_until, price, provider, document_url, created_at`
- **VehicleToll** (`@sp.type`) :116 — `id, vehicle_id, route, toll_amount, toll_date, section, document_url, created_at`
- **VehicleMileage** (`@sp.type`) :128 — `id, vehicle_id, date, mileage, source, notes, created_at`
- **VehicleFuel** (`@sp.type`) :139 — `id, vehicle_id, date, fuel_type, quantity, price_per_liter, total_amount, mileage, location, invoice_number, fuel_card_id, driver_id, created_at`
- **VehicleService** (`@sp.type`) :156 — `id, name, address, phone, email, contact_person, notes, created_at`
- **VehicleRepair** (`@sp.type`) :168 — `id, vehicle_id, repair_date, repair_type, description, parts: JSONScalar|None, labor_hours, labor_cost, parts_cost, total_cost, mileage, vehicle_service_id, warranty_months, next_service_km, notes, created_at`
- **VehicleSchedule** (`@sp.type`) :188 — `id, vehicle_id, schedule_type, interval_km, interval_months, last_service_date, last_service_km, next_service_date, next_service_km, vehicle_service_id, notes, created_at, updated_at`
- **VehicleInsurance** (`@sp.type`) :205 — `id, vehicle_id, insurance_type, policy_number, insurance_company, start_date, end_date, premium, coverage_amount, payment_type, document_url, notes, created_at`
- **VehicleInspection** (`@sp.type`) :222 — `id, vehicle_id, inspection_date, valid_until, result, mileage, inspector, certificate_number, next_inspection_date, notes, created_at`
- **VehiclePreTripInspection** (`@sp.type`) :237 — `id, vehicle_id, driver_id, inspection_date, tires_condition, tires_pressure, tires_tread, brakes_condition, brakes_parking, lights_headlights, lights_brake, lights_turn, lights_warning, fluids_oil, fluids_coolant, fluids_washer, fluids_brake, mirrors, wipers, horn, seatbelts, first_aid_kit, fire_extinguisher, warning_triangle, overall_status, notes, photos: JSONScalar|None, created_at`
- **VehicleDriver** (`@sp.type`) :269 — `id, vehicle_id, user_id, assigned_from, assigned_to, is_primary, created_at`
- **VehicleTrip** (`@sp.type`) :280 — `id, vehicle_id, driver_id, delivery_id, start_address, end_address, start_time, end_time, distance_km, purpose, expenses, notes, created_at, updated_at`
- **VehicleExpense** (`@sp.type`) :298 — `id, vehicle_id, expense_type, expense_date, amount, vat_amount, total_amount, description, reference_id, reference_type, is_deductible, cost_center_id, company_id, created_at`
- **Vehicle** (`@sp.type`) :316 — `id, registration_number, vin, make, model, year, vehicle_type_id, fuel_type, engine_number, chassis_number, color, initial_mileage, is_company, owner_name, status, notes, company_id, created_at, updated_at` + resolvers: `type, documents, fuel_cards, vignettes, tolls, mileages, fuel_records, repairs, schedules, inspections, pre_trip_inspections, drivers, trips, expenses`

### Behavioral Analysis Types — `modules/behavioral_analysis/graphql/types.py`
- **BehavioralProfileType** :7 — `id, user_id, company_id, period_start, period_end, employee_type, tenure_days, probation_mode, data_completeness, punctuality_score, efficiency_score, overtime_score, burnout_risk, financial_stress_score, engagement_score, scrap_rate, peer_group_percentile, trend_direction, status, confidence_score, contribution_factors: JSONScalar|None, rule_engine_version, computed_at, version`
- **BehavioralAnomalyType** :37 — `id, profile_id, user_id, anomaly_type, severity, metric_name, actual_value, expected_value, deviation, confidence_score, suppressed, suppression_reason, description, context_summary: JSONScalar|None, detected_at`
- **BehavioralRuleType** :56 — `id, name, description, rule_type, is_system, is_active, shadow_mode, company_id, condition_type, condition_config: JSONScalar, recommendation_template: JSONScalar, auto_execute_action, auto_execute, effectiveness_score, false_positive_rate, trigger_count, accepted_count, effective_count, false_positive_count, created_by, created_at, updated_at`
- **BehavioralRecommendationType** :82 — `id, rule_id, user_id, anomaly_id, type, priority, title, description, suggested_action, explanation, coaching_tips: JSONScalar|None, confidence_score, status, auto_executed, throttled, aggregated_count, dispute_reason, dispute_notes, created_at, expires_at`
- **BehavioralSettingsType** :106 — `id, company_id, raw_profile_days, aggregated_profile_months, recommendation_months, feedback_months, audit_log_months, auto_cleanup_enabled, cleanup_schedule, anonymize_instead_of_delete, updated_by, updated_at`
- **OrganizationalHealthType** :122 — `department_id, department_name, avg_burnout_risk, avg_engagement, avg_efficiency, avg_punctuality, anomaly_count, employee_count, turnover_rate, trend, is_systemic_issue`
- **RecommendationFeedbackType** :137 — `id, recommendation_id, manager_id, manager_action, manager_notes, action_taken_at, outcome, outcome_measured_at, days_to_outcome, metric_before: JSONScalar|None, metric_after: JSONScalar|None, improvement_delta`
- **BiasReportType** :153 — `id, company_id, period_start, period_end, findings: JSONScalar, overall_bias_detected, generated_at`
- **BehavioralSystemHealthType** :164 — `id, company_id, last_computation_at, last_computation_status, last_computation_duration_seconds, employees_processed, employees_failed, circuit_breaker_open, circuit_breaker_failure_count, last_successful_profile_date, triggered_alerts_today, last_bias_check`
