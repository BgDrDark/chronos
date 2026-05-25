
import strawberry


@strawberry.type
class AnnualInsuranceEmployee:
    egn: str
    name: str
    contract_type: str
    base_salary: float
    insurance_base: float
    doo_employee: float
    zo_employee: float
    dzpo_employee: float
    total_contributions: float
    sick_days: int
    worked_months: int


@strawberry.type
class AnnualInsuranceSummary:
    total_employees: int
    total_doo: float
    total_zo: float
    total_dzpo: float
    total_contributions: float


@strawberry.type
class AnnualInsuranceReport:
    year: int
    company_id: int
    report_type: str
    generated_at: str
    employees: list[AnnualInsuranceEmployee]
    summary: AnnualInsuranceSummary


@strawberry.type
class IncomeEntry:
    type: str
    date: str
    gross: float
    tax: float
    net: float


@strawberry.type
class IncomeReportEmployee:
    egn: str
    name: str
    incomes: list[IncomeEntry]


@strawberry.type
class IncomeReportSummary:
    total_employees: int
    total_gross: float
    total_tax: float


@strawberry.type
class IncomeReportByType:
    year: int
    company_id: int
    report_type: str
    generated_at: str
    employees: list[IncomeReportEmployee]
    summary: IncomeReportSummary


@strawberry.type
class ServiceBookPeriod:
    year: int
    month: int
    gross: float
    net: float


@strawberry.type
class ServiceBookContract:
    type: str
    start_date: str | None
    end_date: str | None
    position: str
    base_salary: float
    hours_per_week: int | None
    status: str


@strawberry.type
class ServiceBookEmployee:
    egn: str
    name: str
    contracts: list[ServiceBookContract]
    periods: list[ServiceBookPeriod]


@strawberry.type
class ServiceBookExport:
    year: int
    company_id: int
    report_type: str
    generated_at: str
    employees: list[ServiceBookEmployee]


@strawberry.type
class MonthlyDeclarationEntry:
    egn: str
    name: str
    income_type: str
    gross: float
    insurance: float
    tax: float
    period: str


@strawberry.type
class MonthlyDeclarationSummary:
    total_gross: float
    total_insurance: float
    total_tax: float


@strawberry.type
class MonthlyDeclarationReport:
    year: int
    month: int
    company_id: int
    report_type: str
    generated_at: str
    declarations: list[MonthlyDeclarationEntry]
    summary: MonthlyDeclarationSummary
