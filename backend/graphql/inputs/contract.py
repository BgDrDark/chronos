import datetime

import strawberry


@strawberry.input
class EmploymentContractCreateInput:
    employee_name: str
    employee_egn: str
    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None
    template_id: int | None = None
    user_id: int | None = None
    contract_type: str
    contract_number: str | None = None
    start_date: datetime.date
    end_date: datetime.date | None = None
    base_salary: float | None = None
    work_hours_per_week: int = 40
    job_description: str | None = None
    probation_months: int | None = None
    salary_calculation_type: str | None = "gross"
    payment_day: int | None = 25
    night_work_rate: float | None = 0.5
    overtime_rate: float | None = 1.5
    holiday_rate: float | None = 2.0
    work_class: str | None = None
    clause_ids: str | None = None


@strawberry.input
class EmploymentContractUpdateInput:
    employee_name: str | None = None
    employee_egn: str | None = None
    company_id: int | None = None
    department_id: int | None = None
    position_id: int | None = None
    template_id: int | None = None
    contract_number: str | None = None
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    base_salary: float | None = None
    work_hours_per_week: int | None = None
    job_description: str | None = None
    probation_months: int | None = None
    salary_calculation_type: str | None = None
    payment_day: int | None = None
    night_work_rate: float | None = None
    overtime_rate: float | None = None
    holiday_rate: float | None = None
    work_class: str | None = None


@strawberry.input
class ContractTemplateSectionInput:
    title: str
    content: str
    order_index: int = 0
    is_required: bool = False


@strawberry.input
class ContractTemplateSectionUpdateInput:
    title: str | None = None
    content: str | None = None
    order_index: int | None = None
    is_required: bool | None = None


@strawberry.input
class AnnexTemplateSectionInput:
    title: str
    content: str
    order_index: int = 0
    is_required: bool = False


@strawberry.input
class AnnexTemplateSectionUpdateInput:
    title: str | None = None
    content: str | None = None
    order_index: int | None = None
    is_required: bool | None = None
