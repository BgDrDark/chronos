from backend.schemas.access_control import (
    AccessCode,
    AccessDoor,
    AccessLog,
    AccessZone,
)
from backend.schemas.accounting import (
    Account,
    AccountingEntry,
    BankAccount,
    BankTransaction,
    CashJournalEntry,
    CashReceipt,
    DailySummary,
    Invoice,
    InvoiceCorrection,
    InvoiceItem,
    MonthlySummary,
    OperationLog,
    VATRegister,
    YearlySummary,
)
from backend.schemas.auth import LoginResponse, Token, TokenData
from backend.schemas.base import CustomBaseModel
from backend.schemas.calendar import (
    OrthodoxHoliday,
    OrthodoxHolidayBase,
    PublicHoliday,
    PublicHolidayBase,
)
from backend.schemas.company import (
    Company,
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    Department,
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    GlobalSetting,
    Position,
    PositionBase,
    PositionCreate,
)
from backend.schemas.contract import (
    AnnexTemplate,
    AnnexTemplateSection,
    AnnexTemplateVersion,
    ClauseTemplate,
    ContractAnnex,
    ContractTemplate,
    ContractTemplateSection,
    ContractTemplateVersion,
    EmploymentContract,
)
from backend.schemas.cost_center import (
    VehicleCostCenter,
    VehicleCostCenterBase,
)
from backend.schemas.hardware import (
    Gateway,
    GatewayBase,
    Printer,
    PrinterBase,
    Terminal,
    TerminalBase,
)
from backend.schemas.leave import (
    LeaveBalance,
    LeaveBalanceBase,
    LeaveRequest,
    LeaveRequestBase,
)
from backend.schemas.logistics import (
    Batch,
    BatchBase,
    BatchCreate,
    Ingredient,
    IngredientBase,
    IngredientCreate,
    StorageZone,
    StorageZoneBase,
    StorageZoneCreate,
    Supplier,
    SupplierBase,
)
from backend.schemas.notification import (
    Notification,
    NotificationSetting,
    SmtpSettings,
)
from backend.schemas.payroll import (
    AdvancePayment,
    Bonus,
    Payroll,
    Payslip,
    ServiceLoan,
)
from backend.schemas.production import (
    PriceHistory,
    ProductionOrder,
    ProductionOrderBase,
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionRecord,
    ProductionRecordIngredient,
    ProductionRecordWorker,
    ProductionScrapLog,
    ProductionTask,
    Recipe,
    RecipeBase,
    RecipeCreate,
    RecipeIngredient,
    RecipeSection,
    RecipeStep,
    Workstation,
)
from backend.schemas.shifts import (
    ScheduleTemplate,
    ScheduleTemplateBase,
    ScheduleTemplateItem,
    ScheduleTemplateItemBase,
    Shift,
    ShiftBase,
    ShiftSwapRequest,
    ShiftSwapRequestBase,
    WorkSchedule,
    WorkScheduleBase,
)
from backend.schemas.stats import (
    MonthlyWorkDays,
)
from backend.schemas.system import (
    APIKey,
    AuditLog,
    ForgotPasswordRequest,
    GoogleCalendarAccount,
    GoogleCalendarSyncSettings,
    Module,
    ModuleBase,
    ModuleUpdate,
    PasswordSettings,
    PasswordSettingsUpdate,
    ResetPasswordRequest,
    Webhook,
    WorkplaceLocationBase,
    WorkplaceLocationCreate,
)
from backend.schemas.time_tracking import (
    TimeLog,
    TimeLogBase,
)
from backend.schemas.trz import (
    BusinessTrip,
    NightWorkBonus,
    OvertimeWork,
    WorkExperience,
)
from backend.schemas.user import (
    Role,
    RoleBase,
    RoleCreate,
    User,
    UserBase,
    UserCreate,
    UserSession,
    UserSessionBase,
    UserUpdate,
)
from backend.schemas.vehicle import (
    Vehicle,
    VehicleAccident,
    VehicleDocument,
    VehicleDriver,
    VehicleExpense,
    VehicleFuel,
    VehicleFuelCard,
    VehicleInspection,
    VehicleInsurance,
    VehicleMileage,
    VehiclePreTripInspection,
    VehicleRepair,
    VehicleSchedule,
    VehicleService,
    VehicleToll,
    VehicleTrip,
    VehicleType,
    VehicleVignette,
)
