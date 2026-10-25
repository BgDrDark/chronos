import asyncio
import logging
from collections.abc import Callable
from typing import Any

from graphql import OperationType
from strawberry.extensions import SchemaExtension

from backend.auth.rbac_service import PermissionService, api_key_allows
from backend.exceptions import PermissionDeniedException

logger = logging.getLogger(__name__)


def _api_key_scopes(info: Any) -> set[str] | None:
    """Return the API key scopes of the request, or ``None`` for JWT sessions."""
    request = info.context.get("request")
    scopes = getattr(getattr(request, "state", None), "api_key_permissions", None)
    if isinstance(scopes, set | frozenset | list | tuple):
        return set(scopes)
    return None

# Mutations, които са съзнателно публични (без login).
# Празно по подразбиране: GraphQL не бива да има публични mutation-и.
PUBLIC_MUTATIONS: frozenset[str] = frozenset()

# Mutations, които изискват само автентикация (действие върху собствени данни).
AUTH_ONLY_MUTATIONS: frozenset[str] = frozenset({
    "changePassword",
    "regenerateMyQrCode",
    "subscribeToPush",
    "deleteNotification",
    # Self-service behavioral actions (own profile / own survey)
    "submitPersonalityTest",
    "submitPulseSurvey",
})

PERMISSION_MAPPING = {
    # Time Tracking & Shifts
    "clockIn": "timelogs:create_own",
    "clockOut": "timelogs:update_own",
    "adminClockIn": "timelogs:admin_create",
    "adminClockOut": "timelogs:admin_create",
    "createManualTimeLog": "timelogs:create",
    "deleteTimeLog": "timelogs:delete",
    "updateTimeLog": "timelogs:update",
    "setMonthlyWorkDays": "payroll:update",
    
    # Shift Swaps
    "createSwapRequest": "shifts:create",
    "approveSwap": "shifts:manage",
    "respondToSwap": "shifts:update_own",
    
    # Schedules
    "setWorkSchedule": "schedules:create",
    "bulkSetSchedule": "schedules:create",
    "bulkDeleteSchedules": "schedules:delete",
    "deleteWorkSchedule": "schedules:delete",
    "copySchedulesFromMonth": "schedules:manage",
    "createScheduleTemplate": "schedules:create",
    "updateScheduleTemplate": "schedules:update",
    "applyScheduleTemplate": "schedules:create",
    "deleteScheduleTemplate": "schedules:delete",
    "createShift": "schedules:create",
    "updateShift": "schedules:update",
    "deleteShift": "schedules:delete",
    
    # Shift Swaps
    
    # Payroll
    "generatePayslip": "payroll:create",
    "generateMyPayslip": "payroll:read_own",
    "addBonus": "payroll:update",
    "removeBonus": "payroll:update",
    "updateUserPayroll": "payroll:update",
    "updateGlobalPayrollConfig": "system:manage_settings",
    "generateDailySummary": "payroll:read",
    "generateMonthlySummary": "payroll:read",
    "generateYearlySummary": "payroll:read",
    "markPayslipAsPaid": "payroll:update",
    "bulkMarkPayslipsAsPaid": "payroll:update",
    "generateSepaXml": "payroll:export",
    
    # Leave Management
    "requestLeave": "leaves:create_own",
    "approveLeave": "leaves:approve",
    "rejectLeave": "leaves:approve",
    "cancelLeaveRequest": "leaves:update",
    "deleteLeaveRequest": "leaves:delete",
    "updateLeaveRequestStatus": "leaves:approve",
    "attachLeaveDocument": "leaves:update",
    
    # User Management
    "createUser": "users:create",
    "updateUser": "users:update",
    "deleteUser": "users:delete",
    "invalidateUserSession": "users:manage_sessions",
    "bulkUpdateUserAccess": "users:manage_access",
    
    # Company Management
    "createCompany": "companies:create",
    "updateCompany": "companies:update",
    "createDepartment": "companies:manage_users",
    "updateDepartment": "companies:manage_users",
    "createPosition": "companies:manage_users",
    "updatePosition": "companies:manage_users",
    "deletePosition": "companies:manage_users",
    
    # Access Control
    "createAccessZone": "system:manage_settings",
    "updateAccessZone": "system:manage_settings",
    "deleteAccessZone": "system:manage_settings",
    "createAccessDoor": "system:manage_settings",
    "deleteAccessDoor": "system:manage_settings",
    "updateDoorTerminal": "system:manage_settings",
    "createAccessCode": "system:manage_settings",
    "deleteAccessCode": "system:manage_settings",
    "revokeAccessCode": "system:manage_settings",
    "assignZoneToUser": "system:manage_settings",
    "removeZoneFromUser": "system:manage_settings",
    "openDoor": "system:manage_settings",
    "syncGatewayConfig": "system:manage_settings",
    
    # Accounting
    "createInvoice": "accounting:create",
    "updateInvoice": "accounting:update",
    "deleteInvoice": "accounting:delete",
    "createBankAccount": "accounting:create",
    "updateBankAccount": "accounting:update",
    "deleteBankAccount": "accounting:delete",
    "createBankTransaction": "accounting:create",
    "updateBankTransaction": "accounting:update",
    "deleteBankTransaction": "accounting:delete",
    "matchBankTransaction": "accounting:update",
    "unmatchBankTransaction": "accounting:update",
    "autoMatchBankTransactions": "accounting:update",
    "createCashJournalEntry": "accounting:create",
    "deleteCashJournalEntry": "accounting:delete",
    "createCashReceipt": "accounting:create",
    "updateCashReceipt": "accounting:update",
    "deleteCashReceipt": "accounting:delete",
    "createAccount": "accounting:create",
    "updateAccount": "accounting:update",
    "deleteAccount": "accounting:delete",
    "createAccountingEntry": "accounting:create",
    "deleteAccountingEntry": "accounting:delete",
    "createAdvancePayment": "accounting:create",
    "createInvoiceCorrection": "accounting:create",
    "createInvoiceFromBatch": "accounting:create",
    "createProformaInvoice": "accounting:create",
    "convertProformaToInvoice": "accounting:update",
    "createCreditNote": "accounting:create",
    "generateSaftFile": "accounting:export",
    "generateVatRegister": "accounting:export",
    "getInvoicePdfUrl": "accounting:read",
    "validateSaftXml": "accounting:read",
    "updateCompanyAccountingSettings": "accounting:update",
    
    # Contracts & HR Documents
    "addSectionToAnnexTemplate": "hr:manage_contracts",
    "addSectionToContractTemplate": "hr:manage_contracts",
    "signContractAnnex": "hr:manage_contracts",
    "signEmploymentContract": "hr:manage_contracts",
    "rejectContractAnnex": "hr:manage_contracts",
    "restoreContractTemplateVersion": "hr:manage_contracts",
    "linkEmploymentContractToUser": "hr:manage_contracts",
    
    # Logistics & Suppliers
    "approveBusinessTrip": "logistics:requests:approve",
    "createServiceLoan": "payroll:create",
    
    # Inventory & Warehouse
    "createIngredient": "inventory:create",
    "updateIngredient": "inventory:update",
    "addBatch": "inventory:create",
    "updateBatch": "inventory:update",
    "updateBatchStatus": "inventory:update",
    "consumeFromBatch": "inventory:update",
    "bulkAddBatches": "inventory:create",
    "startInventorySession": "inventory:create",
    "addInventoryItem": "inventory:update",
    "completeInventorySession": "inventory:update",
    "createSupplier": "logistics:suppliers:create",
    "updateSupplier": "logistics:suppliers:update",
    "createStorageZone": "inventory:create",
    "updateStorageZone": "inventory:update",
    "markTaskScrap": "inventory:update",
    
    # Production & Recipes
    "createRecipe": "production:recipes:create",
    "deleteRecipe": "production:recipes:delete",
    "updateRecipePrice": "production:recipes:update",
    "calculateRecipeCost": "production:recipes:read",
    "recalculateAllRecipeCosts": "production:recipes:update",
    "createWorkstation": "production:workstations:create",
    "createProductionOrder": "production:orders:create",
    "updateProductionOrderStatus": "production:orders:update",
    "updateProductionOrderQuantity": "production:orders:update",
    "recalculateProductionDeadline": "production:orders:update",
    "confirmProductionOrder": "production:orders:confirm",
    "updateProductionTaskStatus": "production:tasks:update",
    "reassignTaskWorkstation": "production:tasks:update",
    "scrapTask": "production:tasks:scrap",
    "getScrapLogs": "production:tasks:read",
    "generateLabel": "production:orders:read",
    "createQuickSale": "production:sales:create",
    
    # Logistics
    
    # Fleet Management
    "createVehicle": "fleet:vehicles:create",
    "updateVehicle": "fleet:vehicles:update",
    "deleteVehicle": "fleet:vehicles:delete",
    "createVehicleMileage": "fleet:mileage:create",
    "updateVehicleMileage": "fleet:mileage:update",
    "deleteVehicleMileage": "fleet:mileage:delete",
    "createVehicleRepair": "fleet:repairs:create",
    "updateVehicleRepair": "fleet:repairs:update",
    "deleteVehicleRepair": "fleet:repairs:delete",
    "createVehicleInsurance": "fleet:insurances:create",
    "updateVehicleInsurance": "fleet:insurances:update",
    "deleteVehicleInsurance": "fleet:insurances:delete",
    "createVehicleInspection": "fleet:inspections:create",
    "updateVehicleInspection": "fleet:inspections:update",
    "deleteVehicleInspection": "fleet:inspections:delete",
    "createVehicleDriver": "fleet:drivers:create",
    "updateVehicleDriver": "fleet:drivers:update",
    "deleteVehicleDriver": "fleet:drivers:delete",
    "createVehicleTrip": "fleet:trips:create",
    "updateVehicleTrip": "fleet:trips:update",
    "deleteVehicleTrip": "fleet:trips:delete",
    "createCostCenter": "fleet:costcenters:create",
    "updateCostCenter": "fleet:costcenters:update",
    "deleteCostCenter": "fleet:costcenters:delete",
    
    # HR & Contracts
    "createEmploymentContract": "users:create",
    "updateEmploymentContract": "users:update",
    "createContractAnnex": "users:update",
    "createContractTemplate": "users:create",
    "updateContractTemplate": "users:update",
    "deleteContractTemplate": "users:delete",
    "createClauseTemplate": "users:create",
    "updateClauseTemplate": "users:update",
    "deleteClauseTemplate": "users:delete",
    "createAnnexTemplate": "users:create",
    "deleteAnnexTemplate": "users:delete",
    "deleteSectionFromAnnexTemplate": "users:delete",
    "deleteSectionFromContractTemplate": "users:delete",
    "updateSectionInAnnexTemplate": "users:update",
    "updateSectionInContractTemplate": "users:update",
    "generateContractNumber": "users:update",
    "getContractPdfUrl": "users:read",
    "getAnnexPdfUrl": "users:read",
    "createWorkExperience": "users:create",
    
    # Settings & System
    "setGlobalSetting": "system:manage_settings",
    "updateSmtpSettings": "system:manage_settings",
    "updatePasswordSettings": "system:manage_settings",
    "updateSecurityConfig": "system:manage_settings",
    "updateOfficeLocation": "system:manage_settings",
    "updatePayrollLegalSettings": "system:manage_settings",
    
    # Roles & Permissions
    "createRole": "system:manage_roles",
    "updateRole": "system:manage_roles",
    "deleteRole": "system:manage_roles",
    "assignRoleToUser": "users:manage_roles",
    
    # Notifications
    "saveNotificationSetting": "system:manage_settings",
    "testNotification": "system:manage_settings",
    "scheduleMaintenance": "system:manage_settings",
    "cancelMaintenance": "system:manage_settings",
    "setUpdateSchedule": "system:manage_settings",
    "runUpdateNow": "system:manage_settings",
    "markNotificationRead": "notifications:read",
    "markAllNotificationsRead": "notifications:read",
    
    # Integrations
    
    # Kiosk & Terminal
    "updateGateway": "kiosk:manage",
    "updateTerminal": "kiosk:manage",
    "deleteTerminal": "kiosk:manage",
    
    # Calendar
    "syncHolidays": "system:manage_settings",
    "syncOrthodoxHolidays": "system:manage_settings",
    
    # Documents
    
    # Behavioral Analysis
    "createBehavioralRule": "behavioral:manage",
    "updateBehavioralRule": "behavioral:manage",
    "deleteBehavioralRule": "behavioral:manage",
    "updateRecommendationStatus": "behavioral:manage",
    "updateBehavioralSettings": "behavioral:manage",
    # --- Phase 1 completion (audit 23.10) ---
    "addDoorToFloorPlan": "system:manage_settings",
    "addItemsToBatch": "inventory:update",
    "assignAccessLevelToUser": "users:manage_access",
    "assignLevelToZone": "system:manage_settings",
    "bulkEmergencyAction": "system:emergency_action",
    "cancelPaymentBatch": "accounting:update",
    "completePaymentBatch": "accounting:update",
    "createAccessLevel": "system:manage_settings",
    "createAccessSchedule": "system:manage_settings",
    "createBusinessTrip": "leaves:create",
    "createDocumentationArticle": "system:manage_settings",
    "createDocumentationCategory": "system:manage_settings",
    "createElevatorFloor": "system:manage_settings",
    "createElevatorGroup": "system:manage_settings",
    "createFloorPlan": "system:manage_settings",
    "createNightWorkBonus": "payroll:create",
    "createOvertimeWork": "payroll:create",
    "createPaymentBatch": "accounting:create",
    "createTimeLog": "timelogs:create",
    "createVehicleAccident": "fleet:vehicles:update",
    "createVehicleFuel": "fleet:fuel:create",
    "deleteAccessLevel": "system:manage_settings",
    "deleteAccessSchedule": "system:manage_settings",
    "deleteDocumentationArticle": "system:manage_settings",
    "deleteDocumentationCategory": "system:manage_settings",
    "deleteElevatorFloor": "system:manage_settings",
    "deleteElevatorGroup": "system:manage_settings",
    "deleteFloorPlan": "system:manage_settings",
    "deleteVehicleFuel": "fleet:fuel:delete",
    "disconnectGoogleCalendar": "integrations:manage",
    "generateAllPayslips": "payroll:create",
    "generateAnnualInsuranceReport": "payroll:read",
    "generateIncomeReportByType": "reports:read",
    "generateMonthlyDeclaration": "payroll:read",
    "generatePin": "users:update",
    "generateServiceBookExport": "users:read",
    "reissuePin": "users:update",
    "removeAccessLevelFromUser": "users:manage_access",
    "removeDoorFromFloorPlan": "system:manage_settings",
    "removeLevelFromZone": "system:manage_settings",
    "resolveEmergency": "system:emergency_action",
    "revealPin": "users:manage_access",
    "triggerEmergency": "system:emergency_action",
    "updateAccessLevel": "system:manage_settings",
    "updateAccessSchedule": "system:manage_settings",
    "updateDocumentationArticle": "system:manage_settings",
    "updateDocumentationCategory": "system:manage_settings",
    "updateDoorOnFloorPlan": "system:manage_settings",
    "updateElevatorFloor": "system:manage_settings",
    "updateElevatorGroup": "system:manage_settings",
    "updateFloorPlan": "system:manage_settings",
    "updateGoogleCalendarSettings": "integrations:manage",
    "updateKioskSecuritySettings": "kiosk:manage",
    "updateLeaveRequest": "leaves:update",
    "updatePositionPayroll": "payroll:update",
    "updateSessionSettings": "system:manage_settings",
    "updateVehicleFuel": "fleet:fuel:update",
    "updateZoneEmergencySettings": "system:manage_settings",
    # --- Behavioral analysis completion (audit 23.10) ---
    "assignPersonalityTest": "behavioral:manage",
    "computeBiasReport": "behavioral:manage",
    "computeManagerEffectiveness": "behavioral:manage",
    "computeOrganizationalHealth": "behavioral:manage",
    "createPersonalityTemplate": "behavioral:manage",
    "deletePersonalityTemplate": "behavioral:manage",
    "reassignPersonalityTest": "behavioral:manage",
    "recordRecommendationFeedback": "behavioral:manage",
    "updatePersonalityTemplate": "behavioral:manage",
}

COMPANY_SCOPED_OPERATIONS = {
    # Operations that require company scoping
    "clockIn", "clockOut", "adminClockIn", "adminClockOut",
    "createManualTimeLog", "deleteTimeLog", "updateTimeLog",
    "setMonthlyWorkDays",
    "createSwapRequest", "approveSwap", "respondToSwap",
    "setWorkSchedule", "bulkSetSchedule", "bulkDeleteSchedules", "deleteWorkSchedule",
    "copySchedulesFromMonth", "createScheduleTemplate", "updateScheduleTemplate",
    "applyScheduleTemplate", "deleteScheduleTemplate",
    "createShift", "updateShift", "deleteShift",
    "calculatePayroll", "generatePayslip", "addBonus", "removeBonus",
    "updateUserPayroll", "updateGlobalPayrollConfig",
    "generateDailySummary", "generateMonthlySummary", "generateYearlySummary",
    "markPayslipAsPaid", "bulkMarkPayslipsAsPaid", "generateSepaXml",
    "requestLeave", "approveLeave", "rejectLeave",
    "cancelLeaveRequest", "deleteLeaveRequest", "updateLeaveRequestStatus",
    "attachLeaveDocument",
    "createUser", "updateUser", "deleteUser",
    "invalidateUserSession", "bulkUpdateUserAccess",
    "createDepartment", "updateDepartment", "deleteDepartment",
    "createPosition", "updatePosition", "deletePosition",
    "createInvoice", "updateInvoice", "deleteInvoice",
    "createTransaction", "updateTransaction", "deleteTransaction",
    "createReceipt", "updateReceipt", "deleteReceipt",
    "createJournalEntry", "updateJournalEntry", "deleteJournalEntry",
    "createBankAccount", "updateBankAccount", "deleteBankAccount",
    "createBankTransaction", "updateBankTransaction", "deleteBankTransaction",
    "matchBankTransaction", "unmatchBankTransaction", "autoMatchBankTransactions",
    "createCashJournalEntry", "deleteCashJournalEntry",
    "createCashReceipt", "updateCashReceipt", "deleteCashReceipt",
    "createAccount", "updateAccount", "deleteAccount",
    "createAccountingEntry", "deleteAccountingEntry",
    "createAdvancePayment", "createInvoiceCorrection", "createInvoiceFromBatch",
    "createProformaInvoice", "convertProformaToInvoice", "createCreditNote",
    "updateCompanyAccountingSettings",
    "addBatch", "updateBatch", "updateBatchStatus", "consumeFromBatch",
    "startInventorySession", "addInventoryItem", "completeInventorySession",
    "createSupplier", "updateSupplier", "deleteSupplier",
    "createStorageZone", "updateStorageZone", "deleteStorageZone",
    "createPurchaseRequest", "updatePurchaseRequest", "deletePurchaseRequest",
    "approvePurchaseRequest", "rejectPurchaseRequest",
    "createPurchaseOrder", "updatePurchaseOrder", "deletePurchaseOrder",
    "createDelivery", "updateDelivery", "deleteDelivery",
    "createVehicle", "updateVehicle", "deleteVehicle",
    "createVehicleDocument", "updateVehicleDocument", "deleteVehicleDocument",
    "createFuelCard", "updateFuelCard", "deleteFuelCard",
    "createVignette", "updateVignette", "deleteVignette",
    "createToll", "updateToll", "deleteToll",
    "createVehicleMileage", "updateVehicleMileage", "deleteVehicleMileage",
    "createFuelLog", "updateFuelLog", "deleteFuelLog",
    "createVehicleRepair", "updateVehicleRepair", "deleteVehicleRepair",
    "createVehicleInsurance", "updateVehicleInsurance", "deleteVehicleInsurance",
    "createVehicleInspection", "updateVehicleInspection", "deleteVehicleInspection",
    "createVehicleDriver", "updateVehicleDriver", "deleteVehicleDriver",
    "createVehicleTrip", "updateVehicleTrip", "deleteVehicleTrip",
    "approveVehicleTrip",
    "createFleetExpense", "updateFleetExpense", "deleteFleetExpense",
    "createCostCenter", "updateCostCenter", "deleteCostCenter",
    "createProductionOrder", "updateProductionOrder", "deleteProductionOrder",
    "createProductionTask", "updateProductionTask", "deleteProductionTask",
    "createRecipe", "updateRecipe", "deleteRecipe",
    "confirmProductionOrder", "startProductionTask", "completeProductionTask",
    "createEmploymentContract", "updateEmploymentContract", "deleteEmploymentContract",
    "createContractAnnex", "updateContractAnnex", "deleteContractAnnex",
    "createBonus", "updateBonus", "deleteBonus",
    "createPenalty", "updatePenalty", "deletePenalty",
    "createTraining", "updateTraining", "deleteTraining",
    "createCertification", "updateCertification", "deleteCertification",
    "createAccessZone", "updateAccessZone", "deleteAccessZone",
    "createAccessDoor", "updateAccessDoor", "deleteAccessDoor", "updateDoorTerminal",
    "createAccessCode", "updateAccessCode", "deleteAccessCode", "revokeAccessCode",
    "assignZoneToUser", "removeZoneFromUser",
    "openDoor", "triggerDoorRemote", "syncGatewayConfig",
    "createCalendarEvent", "updateCalendarEvent", "deleteCalendarEvent",
    "uploadDocument", "deleteDocument",
    "approveBusinessTrip", "createServiceLoan",
}


def extract_target_company_id(kwargs: dict) -> int | None:
    """Extract the target company from resolver kwargs.

    Handles all shapes used by the schema: ``company_id``, ``input`` dict and
    ``user_input``/``userInput`` dicts. Returns ``None`` when the operation is
    not company-scoped.
    """
    explicit = kwargs.get("company_id")
    if explicit is not None:
        return explicit

    for key in ("input", "user_input", "userInput"):
        payload = kwargs.get(key)
        if isinstance(payload, dict):
            value = payload.get("company_id")
            if value is not None:
                return value

    return None


class PermissionGuardMiddleware(SchemaExtension):
    """
    Middleware that enforces RBAC permissions for all GraphQL mutations.
    
    This middleware:
    1. Checks if the operation requires a permission (via PERMISSION_MAPPING)
    2. Verifies the user has the required permission
    3. Applies company scoping for company-specific operations
    4. Logs all permission decisions for audit trail
    """

    @staticmethod
    async def _call(next_: Callable, root: Any, info: Any, *args, **kwargs) -> Any:
        """Invoke the next resolver, awaiting it when necessary."""
        result = next_(root, info, *args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def _resolve_query(self, next_, root, info, *args, **kwargs):
        """Enforce (or log-only) read permissions for GraphQL queries."""
        from backend.chronos_graphql.query_permissions import (
            PUBLIC_QUERIES,
            resolve_query_permission,
        )
        from backend.config import settings

        field_name = info.field_name
        if field_name in PUBLIC_QUERIES:
            return await self._call(next_, root, info, *args, **kwargs)

        current_user = info.context.get("current_user")
        if not current_user:
            raise PermissionDeniedException(
                detail="Authentication required",
                context={"operation": field_name},
            )

        permission = resolve_query_permission(field_name)
        if permission is None:
            raise PermissionDeniedException(
                detail="Заявката не е разрешена",
                context={"operation": field_name, "reason": "missing_query_permission"},
            )

        db = info.context.get("db")
        if not db:
            logger.error("No database session available for query check: %s", field_name)
            raise PermissionDeniedException(
                detail="System error: database unavailable",
                context={"operation": field_name},
            )

        allowed = await PermissionService(db).check_permission(
            user_id=current_user.id,
            permission=permission,
            company_id=current_user.company_id,
        )

        # API key scopes are an extra ceiling on top of role permissions (A9).
        scopes = _api_key_scopes(info)
        if allowed and scopes is not None:
            allowed = api_key_allows(scopes, permission)

        if not allowed and settings.RBAC_QUERY_ENFORCEMENT:
            raise PermissionDeniedException(
                detail=f"Нямате разрешение за: {field_name}",
                context={"operation": field_name, "required_permission": permission},
            )

        if not allowed:
            logger.warning(
                "RBAC query would be denied (log-only): %s needs %s",
                field_name,
                permission,
            )

        return await self._call(next_, root, info, *args, **kwargs)

    async def resolve(self, next_: Callable, root: Any, info: Any, *args, **kwargs) -> Any:
        if info.operation.operation == OperationType.QUERY:
            return await self._resolve_query(next_, root, info, *args, **kwargs)

        # Only check mutations (queries are handled above)
        if info.operation.operation != OperationType.MUTATION:
            return await self._call(next_, root, info, *args, **kwargs)

        field_name = info.field_name
        current_user = info.context.get("current_user")

        # Explicitly public mutations only (empty by design).
        if field_name in PUBLIC_MUTATIONS:
            return await self._call(next_, root, info, *args, **kwargs)

        # Everything else requires authentication.
        if not current_user:
            raise PermissionDeniedException(
                detail="Authentication required",
                context={"operation": field_name},
            )

        # Auth-only mutations act on the caller's own data.
        if field_name in AUTH_ONLY_MUTATIONS:
            return await self._call(next_, root, info, *args, **kwargs)

        # Fail closed: an unmapped mutation is denied, never silently public.
        if field_name not in PERMISSION_MAPPING:
            logger.error("Mutation without permission mapping: %s", field_name)
            raise PermissionDeniedException(
                detail="Операцията не е разрешена",
                context={
                    "operation": field_name,
                    "reason": "missing_permission_mapping",
                },
            )
        
        # Get required permission
        required_permission = PERMISSION_MAPPING[field_name]
        
        # Get database session
        db = info.context.get("db")
        if not db:
            logger.error(f"No database session available for permission check: {field_name}")
            raise PermissionDeniedException(
                detail="System error: database unavailable",
                context={"operation": field_name},
            )

        permission_service = PermissionService(db)

        # Permission-based super admin (audit 23.10, D9): no name checks.
        is_super_admin = await permission_service.check_permission(
            user_id=current_user.id,
            permission="system:super_admin",
        )

        # Determine company_id for company-scoped operations
        company_id = None
        if field_name in COMPANY_SCOPED_OPERATIONS:
            if is_super_admin:
                # Super admins can access all companies
                company_id = None  # No company restriction
            else:
                # Regular users are restricted to their company
                company_id = current_user.company_id
                
                # Check if operation targets a different company
                target_company_id = extract_target_company_id(kwargs)
                if target_company_id and target_company_id != current_user.company_id:
                    await PermissionService(db).log_permission_decision(
                        user_id=current_user.id,
                        permission=required_permission,
                        decision=False,
                        resource_type="company",
                        resource_id=target_company_id,
                        context={"reason": "cross_company_access_denied"},
                    )
                    raise PermissionDeniedException(
                        detail="Нямате достъп до данни на друга компания",
                        context={
                            "operation": field_name,
                            "user_company_id": current_user.company_id,
                            "target_company_id": target_company_id,
                        },
                    )

        # Self-scoped operations: the resolver always acts on current_user.
        # Check the `_own` permission directly; stripping `_own` turned this
        # into a base-permission check (audit R6).
        if field_name in ("clockIn", "clockOut"):
            permissions = await permission_service.get_user_permissions(
                user_id=current_user.id,
                company_id=company_id,
            )
            has_permission = required_permission in permissions
        else:
            resource_id = kwargs.get("id") or kwargs.get("user_id")
            has_permission = await permission_service.check_permission(
                user_id=current_user.id,
                permission=required_permission,
                company_id=company_id,
                resource_id=resource_id,
            )

        # API key scopes are an extra ceiling on top of role permissions (A9).
        scopes = _api_key_scopes(info)
        if has_permission and scopes is not None:
            has_permission = api_key_allows(scopes, required_permission)
        
        # Log permission decision
        await permission_service.log_permission_decision(
            user_id=current_user.id,
            permission=required_permission,
            decision=has_permission,
            resource_type="mutation",
            resource_id=None,
            context={
                "operation": field_name,
                "company_id": company_id,
                "ip_address": info.context.get("ip_address"),
            },
        )
        
        if not has_permission:
            raise PermissionDeniedException(
                detail=f"Нямате разрешение за: {field_name}",
                context={
                    "operation": field_name,
                    "required_permission": required_permission,
                    "user_id": current_user.id,
                    "company_id": company_id,
                },
            )
        
        # Permission granted - execute the operation
        return await self._call(next_, root, info, *args, **kwargs)
