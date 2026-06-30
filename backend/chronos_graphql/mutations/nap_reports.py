import logging

import strawberry

from backend.exceptions import AuthenticationException
from backend.chronos_graphql import types
from backend.services.nap_reports import NAPReportsGenerator

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class NapReportMutation:

    @strawberry.mutation
    async def generate_annual_insurance_report(self, info: strawberry.Info, year: int) -> types.AnnualInsuranceReport:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        generator = NAPReportsGenerator(db, current_user.company_id, year)
        result = await generator.generate_annual_insurance_report()
        return types.AnnualInsuranceReport(
            year=result["year"],
            company_id=result["company_id"],
            report_type=result["report_type"],
            generated_at=result["generated_at"],
            employees=[types.AnnualInsuranceEmployee(**emp) for emp in result["employees"]],
            summary=types.AnnualInsuranceSummary(**result["summary"]),
        )

    @strawberry.mutation
    async def generate_income_report_by_type(self, info: strawberry.Info, year: int) -> types.IncomeReportByType:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        generator = NAPReportsGenerator(db, current_user.company_id, year)
        result = await generator.generate_income_report_by_type()
        employees = []
        for emp_data in result["employees"].values():
            employees.append(types.IncomeReportEmployee(
                egn=emp_data["egn"],
                name=emp_data["name"],
                incomes=[types.IncomeEntry(**inc) for inc in emp_data["incomes"]],
            ))
        return types.IncomeReportByType(
            year=result["year"],
            company_id=result["company_id"],
            report_type=result["report_type"],
            generated_at=result["generated_at"],
            employees=employees,
            summary=types.IncomeReportSummary(**result["summary"]),
        )

    @strawberry.mutation
    async def generate_service_book_export(self, info: strawberry.Info, year: int) -> types.ServiceBookExport:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        generator = NAPReportsGenerator(db, current_user.company_id, year)
        result = await generator.generate_service_book_export()
        employees = []
        for emp in result["employees"]:
            employees.append(types.ServiceBookEmployee(
                egn=emp["egn"],
                name=emp["name"],
                contracts=[types.ServiceBookContract(**c) for c in emp["contracts"]],
                periods=[types.ServiceBookPeriod(**p) for p in emp["periods"]],
            ))
        return types.ServiceBookExport(
            year=result["year"],
            company_id=result["company_id"],
            report_type=result["report_type"],
            generated_at=result["generated_at"],
            employees=employees,
        )

    @strawberry.mutation
    async def generate_monthly_declaration(self, info: strawberry.Info, year: int, month: int) -> types.MonthlyDeclarationReport:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)
        generator = NAPReportsGenerator(db, current_user.company_id, year)
        result = await generator.generate_monthly_declaration(month)
        return types.MonthlyDeclarationReport(
            year=result["year"],
            month=result["month"],
            company_id=result["company_id"],
            report_type=result["report_type"],
            generated_at=result["generated_at"],
            declarations=[types.MonthlyDeclarationEntry(**d) for d in result["declarations"]],
            summary=types.MonthlyDeclarationSummary(**result["summary"]),
        )
