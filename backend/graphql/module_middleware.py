import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from strawberry.extensions import SchemaExtension

from backend.auth.module_guard import ModuleDisabledException, verify_module_enabled
from backend.database.models import ThrottleLog, sofia_now
from graphql import GraphQLList, GraphQLNonNull, OperationType

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
    "terminals": "kiosk",
    "gateways": "kiosk",
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
    "getInvoicePdfUrl": "accounting",

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

    # Fleet (NEW - optional)
    "vehicles": "fleet",
    "vehicleDocuments": "fleet",
    "vehicleMileage": "fleet",
    "vehicleFuelLogs": "fleet",
    "vehicleRepairs": "fleet",
    "vehicleInsurances": "fleet",
    "vehicleInspections": "fleet",
    "vehicleDrivers": "fleet",
    "vehicleTrips": "fleet",
    "createVehicle": "fleet",
    "updateVehicle": "fleet",
    "createVehicleDriver": "fleet",
    "updateVehicleDriver": "fleet",
    "createVehicleTrip": "fleet",
    "updateVehicleTrip": "fleet",
    "fuelCards": "fleet",
    "createFuelCard": "fleet",
    "updateFuelCard": "fleet",
    "vignettes": "fleet",
    "createVignette": "fleet",
    "updateVignette": "fleet",
    "tolls": "fleet",
    "createToll": "fleet",
    "updateToll": "fleet",
    "fleetReports": "fleet",

    # Cost Centers (NEW - core)
    "costCenters": "cost_centers",
    "createCostCenter": "cost_centers",
    "updateCostCenter": "cost_centers",
    "deleteCostCenter": "cost_centers",

    # Inventory (NEW - optional)
    "batches": "inventory",
    "batch": "inventory",
    "addBatch": "inventory",
    "updateBatch": "inventory",
    "updateBatchStatus": "inventory",
    "consumeFromBatch": "inventory",
    "inventorySessions": "inventory",
    "inventorySessionItems": "inventory",
    "inventoryByBarcode": "inventory",
    "startInventorySession": "inventory",
    "addInventoryItem": "inventory",
    "completeInventorySession": "inventory",
    "stockConsumptionLogs": "inventory",

    # Behavioral Analysis (NEW - optional)
    "behavioralProfiles": "behavioral_analysis",
    "behavioralAnomalies": "behavioral_analysis",
    "behavioralRules": "behavioral_analysis",
    "createBehavioralRule": "behavioral_analysis",
    "updateBehavioralRule": "behavioral_analysis",
    "deleteBehavioralRule": "behavioral_analysis",
    "behavioralRecommendations": "behavioral_analysis",
    "updateRecommendationStatus": "behavioral_analysis",
    "behavioralSettings": "behavioral_analysis",
    "updateBehavioralSettings": "behavioral_analysis",
    "organizationalHealth": "behavioral_analysis",
    "biasReports": "behavioral_analysis",
    "computeBehavioralProfiles": "behavioral_analysis",
}

# Throttling Configuration: {field_name: seconds_between_calls}
THROTTLE_CONFIG = {
    # Payroll (heavy operations)
    "generatePayslip": 10,
    "generateMyPayslip": 10,
    "calculatePayroll": 5,
    "payrollSummary": 10,
    "addBonus": 5,
    "removeBonus": 5,
    "updateUserPayroll": 5,
    "updateMyPayroll": 5,
    "updateGlobalPayrollConfig": 10,

    # Integrations
    "syncGoogleCalendar": 60,

    # User & Company Management
    "createUser": 10,
    "updateUser": 5,
    "deleteUser": 10,
    "createCompany": 10,
    "updateCompany": 10,
    "createDepartment": 5,
    "updateDepartment": 5,
    "deleteDepartment": 10,
    "createPosition": 5,
    "updatePosition": 5,
    "deletePosition": 10,

    # Shifts & Schedules
    "createShift": 5,
    "updateShift": 5,
    "deleteShift": 10,
    "setWorkSchedule": 3,
    "bulkSetSchedule": 10,
    "deleteWorkSchedule": 5,
    "createScheduleTemplate": 10,
    "applyScheduleTemplate": 15,
    "deleteScheduleTemplate": 10,

    # Leave Management
    "requestLeave": 10,
    "approveLeave": 5,
    "rejectLeave": 5,
    "cancelLeaveRequest": 10,
    "deleteLeaveRequest": 10,
    "updateLeaveRequestStatus": 5,

    # Time Tracking
    "clockIn": 30,
    "clockOut": 30,
    "adminClockIn": 10,
    "adminClockOut": 10,
    "createManualTimeLog": 10,
    "deleteTimeLog": 10,
    "updateTimeLog": 10,

    # Production
    "createProductionOrder": 5,
    "updateProductionOrder": 5,
    "deleteProductionOrder": 10,
    "createProductionTask": 5,
    "updateProductionTask": 5,
    "deleteProductionTask": 10,
    "createBatch": 5,
    "updateBatch": 5,
    "deleteBatch": 10,
    "createRecipe": 10,
    "updateRecipe": 5,
    "deleteRecipe": 10,
    "confirmProductionOrder": 10,
    "startProductionTask": 5,
    "completeProductionTask": 5,
    "createInventorySession": 10,
    "completeInventorySession": 10,

    # Accounting
    "createInvoice": 5,
    "updateInvoice": 5,
    "deleteInvoice": 10,
    "createTransaction": 5,
    "updateTransaction": 5,
    "deleteTransaction": 10,
    "createReceipt": 5,
    "updateReceipt": 5,
    "deleteReceipt": 10,

    # Fleet
    "createVehicle": 10,
    "updateVehicle": 5,
    "deleteVehicle": 10,
    "createVehicleTrip": 5,
    "updateVehicleTrip": 5,
    "deleteVehicleTrip": 10,
    "approveVehicleTrip": 10,

    # Warehouse
    "createSupplier": 10,
    "updateSupplier": 5,
    "deleteSupplier": 10,

    # Access Control
    "createAccessZone": 10,
    "updateAccessZone": 5,
    "deleteAccessZone": 10,
    "createAccessDoor": 10,
    "updateAccessDoor": 5,
    "deleteAccessDoor": 10,
    "createAccessCode": 10,
    "updateAccessCode": 5,
    "deleteAccessCode": 10,

    # Settings
    "setGlobalSetting": 5,
    "updateSmtpSettings": 10,
    "updatePasswordSettings": 10,
    "updateSecurityConfig": 10,
    "updateOfficeLocation": 10,
    "updateKioskSettings": 10,
    "updatePayrollLegalSettings": 10,
    "updateVapidPublicKey": 10,

    # HR
    "createEmploymentContract": 10,
    "updateEmploymentContract": 5,
    "deleteEmploymentContract": 10,
    "createContractAnnex": 10,
    "updateContractAnnex": 5,
    "deleteContractAnnex": 10,

    # Roles & Permissions
    "createRole": 10,
    "updateRole": 5,
    "deleteRole": 10,

    # Shift Swap
    "createShiftSwapRequest": 10,
    "acceptShiftSwapRequest": 5,
    "rejectShiftSwapRequest": 5,
    "cancelShiftSwapRequest": 10,

    # Documents
    "uploadDocument": 5,
    "deleteDocument": 10,

    # Notifications
    "markNotificationRead": 3,
    "markAllNotificationsRead": 10,

    # Gateway & Terminal
    "registerGateway": 30,
    "updateGateway": 10,
    "deleteGateway": 30,
    "registerTerminal": 10,
    "updateTerminal": 5,
    "deleteTerminal": 10,
    "registerPrinter": 10,
    "updatePrinter": 5,
    "deletePrinter": 10,
    "testPrinter": 10,
    "syncAccessLogs": 5,
    "syncTerminalConfig": 10,
}

class ModuleGuardMiddleware(SchemaExtension):
    _last_calls: dict[str, float] = {}

    async def resolve(self, next_: Callable, root: Any, info: Any, *args, **kwargs) -> Any:
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

            db = info.context.get("db")
            if db:
                try:
                    ip_address = info.context.get("ip_address")
                    throttle_log = ThrottleLog(
                        user_id=current_user.id if current_user else 0,
                        field_name=field_name,
                        ip_address=ip_address,
                        called_at=sofia_now(),
                    )
                    db.add(throttle_log)
                except Exception as e:
                    logger.warning(f"Failed to log throttle: {e}")

        result = next_(root, info, *args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
