from backend.schemas.base import CustomBaseModel

from backend.schemas.auth import Token, LoginResponse, TokenData

from backend.schemas.user import (
    RoleBase, RoleCreate, Role,
    UserBase, UserCreate, UserUpdate, User,
)

from backend.schemas.company import (
    CompanyBase, CompanyCreate, CompanyUpdate, Company,
    DepartmentBase, DepartmentCreate, DepartmentUpdate, Department,
    PositionBase, PositionCreate, Position,
    GlobalSetting,
)

from backend.schemas.system import (
    ModuleBase, ModuleUpdate, Module,
    PasswordSettings, PasswordSettingsUpdate,
    ForgotPasswordRequest, ResetPasswordRequest,
    WorkplaceLocationBase, WorkplaceLocationCreate,
    AuditLog,
    APIKey,
    Webhook,
    GoogleCalendarSyncSettings,
    GoogleCalendarAccount,
)

from backend.schemas.production import (
    RecipeBase, RecipeCreate, Recipe,
    RecipeIngredient,
    RecipeSection,
    RecipeStep,
    PriceHistory,
    Workstation,
    ProductionTask,
    ProductionScrapLog,
    ProductionRecord,
    ProductionRecordIngredient,
    ProductionRecordWorker,
    ProductionOrderBase, ProductionOrderCreate, ProductionOrderUpdate, ProductionOrder,
)

from backend.schemas.notification import (
    SmtpSettings,
    Notification,
    NotificationSetting,
)

from backend.schemas.logistics import (
    StorageZoneBase, StorageZoneCreate, StorageZone,
    IngredientBase, IngredientCreate, Ingredient,
    BatchBase, BatchCreate, Batch,
    SupplierBase, Supplier,
)

from backend.schemas.shifts import (
    ShiftBase, Shift,
    WorkScheduleBase, WorkSchedule,
    ShiftSwapRequestBase, ShiftSwapRequest,
    ScheduleTemplateBase, ScheduleTemplate,
    ScheduleTemplateItemBase, ScheduleTemplateItem,
)

from backend.schemas.hardware import (
    GatewayBase, Gateway,
    TerminalBase, Terminal,
    PrinterBase, Printer,
)

from backend.schemas.time_tracking import (
    TimeLogBase, TimeLog,
)

from backend.schemas.cost_center import (
    VehicleCostCenterBase, VehicleCostCenter,
)

from backend.schemas.calendar import (
    PublicHolidayBase, PublicHoliday,
    OrthodoxHolidayBase, OrthodoxHoliday,
)

from backend.schemas.leave import (
    LeaveRequestBase, LeaveRequest,
    LeaveBalanceBase, LeaveBalance,
)

from backend.schemas.vehicle import (
    VehicleType,
    Vehicle,
    VehicleDocument,
    VehicleFuelCard,
    VehicleVignette,
    VehicleToll,
    VehicleMileage,
    VehicleFuel,
    VehicleService,
    VehicleRepair,
    VehicleSchedule,
    VehicleInsurance,
    VehicleInspection,
    VehiclePreTripInspection,
    VehicleDriver,
    VehicleTrip,
    VehicleExpense,
)

from backend.schemas.user import UserSessionBase, UserSession

from backend.schemas.accounting import (
    InvoiceItem,
    Invoice,
    CashJournalEntry,
    OperationLog,
    DailySummary,
    MonthlySummary,
    YearlySummary,
    InvoiceCorrection,
    CashReceipt,
    BankAccount,
    BankTransaction,
    Account,
    AccountingEntry,
    VATRegister,
)

from backend.schemas.access_control import (
    AccessZone,
    AccessDoor,
    AccessCode,
    AccessLog,
)

from backend.schemas.trz import (
    NightWorkBonus,
    OvertimeWork,
    BusinessTrip,
    WorkExperience,
)

from backend.schemas.payroll import (
    Payroll,
    Payslip,
    Bonus,
    AdvancePayment,
    ServiceLoan,
)

from backend.schemas.stats import (
    MonthlyWorkDays,
)

from backend.schemas.contract import (
    EmploymentContract,
    ContractAnnex,
    ContractTemplateSection,
    ContractTemplateVersion,
    ContractTemplate,
    AnnexTemplateSection,
    AnnexTemplateVersion,
    AnnexTemplate,
    ClauseTemplate,
)
