import time
import asyncio
import logging
import strawberry
from typing import Any, Callable, Dict, Optional, Union, List
from strawberry.extensions import SchemaExtension
from graphql import GraphQLList, GraphQLNonNull, OperationType
from backend.auth.module_guard import verify_module_enabled, ModuleDisabledException

logger = logging.getLogger(__name__)

# Mapping of GraphQL fields to modules (Using GraphQL CamelCase names)
MODULE_MAPPING = {
    # Time Tracking & Shifts
    "clockIn": "shifts",
    "clockOut": "shifts",
    "adminClockIn": "shifts",
    "adminClockOut": "shifts",
    "activeTimeLog": "shifts",
    "timeLogs": "shifts",
    "createManualTimeLog": "shifts",
    "deleteTimeLog": "shifts",
    "mySchedules": "shifts",
    "workSchedules": "shifts",
    "setWorkSchedule": "shifts",
    "bulkSetSchedule": "shifts",
    "deleteWorkSchedule": "shifts",
    "createScheduleTemplate": "shifts",
    "applyScheduleTemplate": "shifts",
    
    # Payroll & Salaries
    "calculatePayroll": "salaries",
    "generatePayslip": "salaries",
    "generateMyPayslip": "salaries",
    "payrolls": "salaries",
    "payslips": "salaries",
    "bonuses": "salaries",
    "addBonus": "salaries",
    "removeBonus": "salaries",
    "updateUserPayroll": "salaries",
    "updateMyPayroll": "salaries",
    "updateGlobalPayrollConfig": "salaries",
    "payrollPeriods": "salaries",
    "payrollSummary": "salaries",
    
    # Kiosk
    "kioskDevices": "kiosk",
    "createKioskDevice": "kiosk",
    
    # Integrations
    "googleCalendarAccounts": "integrations",
    "syncGoogleCalendar": "integrations",
    "webhooks": "integrations",
    "createWebhook": "integrations",
    "apiKeys": "integrations",
    "createApiKey": "integrations",
    "attachLeaveDocument": "integrations", # Uses OCR

    # Notifications
    "smtpSettings": "notifications",
    "updateSmtpSettings": "notifications",
    "notificationSettings": "notifications",
    "notificationSetting": "notifications",
    "saveNotificationSetting": "notifications",
    "testNotification": "notifications",

    # Accounting / Invoicing
    "invoices": "accounting",
    "invoice": "accounting",
    "invoiceByNumber": "accounting",
    "createInvoice": "accounting",
    "updateInvoice": "accounting",
    "deleteInvoice": "accounting",
    "createInvoiceFromBatch": "accounting",

    # Warehouse / Confectionery
    "suppliers": "confectionery",
    "createSupplier": "confectionery",
    "updateSupplier": "confectionery",
    "storageZones": "confectionery",
    "createStorageZone": "confectionery",
    "updateStorageZone": "confectionery",
    "scrapTask": "confectionery",
    "getScrapLogs": "confectionery",
    "markTaskScrap": "confectionery",
}

# Throttling Configuration: {field_name: seconds_between_calls}
THROTTLE_CONFIG = {
    "generatePayslip": 10,
    "generateMyPayslip": 10,
    "calculatePayroll": 5,
    "payrollSummary": 10,
    "syncGoogleCalendar": 60,
}

class ModuleGuardMiddleware(SchemaExtension):
    _last_calls: Dict[str, float] = {}

    async def resolve(self, next_: Callable, root: Any, info: Any, **kwargs) -> Any:
        # field_name from GraphQLResolveInfo is in camelCase
        field_name = info.field_name
        current_user = info.context.get("current_user")
        user_id = current_user.id if current_user else "anonymous"
        
        # 1. Module Guard Check
        if field_name in MODULE_MAPPING:
            module_code = MODULE_MAPPING[field_name]
            db = info.context.get("db")
            if db:
                try:
                    await verify_module_enabled(module_code, db)
                except ModuleDisabledException as e:
                    # For mutations, always raise the error to provide a clear message
                    if info.operation.operation == OperationType.MUTATION:
                        raise e

                    # For queries, return appropriate empty value based on return type
                    return_type = info.return_type
                    
                    def is_list(t):
                        if isinstance(t, GraphQLNonNull):
                            return is_list(t.of_type)
                        return isinstance(t, GraphQLList)

                    if is_list(return_type):
                         return []
                    
                    return None
        
        # 2. Throttling Check
        if field_name in THROTTLE_CONFIG:
            throttle_key = f"{user_id}:{field_name}"
            now = time.time()
            last_call = self._last_calls.get(throttle_key, 0)
            
            if now - last_call < THROTTLE_CONFIG[field_name]:
                wait_time = int(THROTTLE_CONFIG[field_name] - (now - last_call)) + 1
                raise Exception(f"Твърде много заявки за '{field_name}'. Моля, изчакайте {wait_time} секунди.")
            
            self._last_calls[throttle_key] = now
        
        result = next_(root, info, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result