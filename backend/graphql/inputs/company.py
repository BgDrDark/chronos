import strawberry


@strawberry.input
class CompanyCreateInput:
    name: str
    eik: str | None = None
    bulstat: str | None = None
    vat_number: str | None = None
    address: str | None = None
    mol_name: str | None = None


@strawberry.input
class CompanyUpdateInput:
    id: int
    name: str | None = None
    eik: str | None = None
    bulstat: str | None = None
    vat_number: str | None = None
    address: str | None = None
    mol_name: str | None = None
    default_sales_account_id: int | None = None
    default_expense_account_id: int | None = None
    default_vat_account_id: int | None = None
    default_customer_account_id: int | None = None
    default_supplier_account_id: int | None = None
    default_cash_account_id: int | None = None
    default_bank_account_id: int | None = None


@strawberry.input
class CompanyAccountingSettingsInput:
    company_id: int
    default_sales_account_id: int | None = None
    default_expense_account_id: int | None = None
    default_vat_account_id: int | None = None
    default_customer_account_id: int | None = None
    default_supplier_account_id: int | None = None
    default_cash_account_id: int | None = None
    default_bank_account_id: int | None = None


@strawberry.input
class DepartmentCreateInput:
    name: str
    company_id: int
    manager_id: int | None = None


@strawberry.input
class DepartmentUpdateInput:
    id: int
    name: str | None = None
    manager_id: int | None = None


@strawberry.input
class PositionCreateInput:
    title: str
    department_id: int


@strawberry.input
class RoleCreateInput:
    name: str
    description: str | None = None
