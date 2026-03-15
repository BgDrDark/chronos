"""
NAP Reports Generator
Generates required reports for National Revenue Agency (НАП):
1. Annual insurance report (Годишна справка за осигурени лица)
2. Income report by type (Справка по чл. 73, ал. 6 ЗДДФЛ)
"""
from decimal import Decimal
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from backend.database.models import User, EmploymentContract, Payslip, SickLeaveRecord, LeaveRequest


class NAPReportsGenerator:
    """Generates reports for National Revenue Agency"""
    
    def __init__(self, db: AsyncSession, company_id: int, year: int):
        self.db = db
        self.company_id = company_id
        self.year = year
    
    async def generate_annual_insurance_report(self) -> Dict[str, Any]:
        """
        Генерира годишна справка за осигурени лица.
        Съдържа информация за всички осигурени служители за годината.
        """
        # Вземи всички активни договори
        result = await self.db.execute(
            select(EmploymentContract).where(
                and_(
                    EmploymentContract.company_id == self.company_id,
                    EmploymentContract.is_active == True
                )
            )
        )
        contracts = result.scalars().all()
        
        employees_data = []
        
        for contract in contracts:
            user = contract.user
            
            # Вземи заплатите за годината
            payslips_result = await self.db.execute(
                select(Payslip).where(
                    and_(
                        Payslip.user_id == user.id,
                        func.extract('year', Payslip.period_start) == self.year
                    )
                )
            )
            payslips = payslips_result.scalars().all()
            
            # Сумирај осигуровките
            total_doo = sum(float(p.doo_employee or 0) for p in payslips)
            total_zo = sum(float(p.zo_employee or 0) for p in payslips)
            total_dzpo = sum(float(p.dzpo_employee or 0) for p in payslips)
            
            # Вземи болничните дни
            sick_result = await self.db.execute(
                select(SickLeaveRecord).where(
                    and_(
                        SickLeaveRecord.user_id == user.id,
                        func.extract('year', SickLeaveRecord.start_date) == self.year
                    )
                )
            )
            sick_records = sick_result.scalars().all()
            total_sick_days = sum(r.total_days for r in sick_records)
            
            employees_data.append({
                "egn": user.egn or "",
                "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                "contract_type": contract.contract_type or "full_time",
                "base_salary": float(contract.base_salary or 0),
                "insurance_base": float(contract.base_salary or 0) * 12,  # Годишна база
                "doo_employee": total_doo,
                "zo_employee": total_zo,
                "dzpo_employee": total_dzpo,
                "total_contributions": total_doo + total_zo + total_dzpo,
                "sick_days": total_sick_days,
                "worked_months": len(set(p.period_start.month for p in payslips))
            })
        
        return {
            "year": self.year,
            "company_id": self.company_id,
            "report_type": "annual_insurance",
            "generated_at": datetime.now().isoformat(),
            "employees": employees_data,
            "summary": {
                "total_employees": len(employees_data),
                "total_doo": sum(e["doo_employee"] for e in employees_data),
                "total_zo": sum(e["zo_employee"] for e in employees_data),
                "total_dzpo": sum(e["dzpo_employee"] for e in employees_data),
                "total_contributions": sum(e["total_contributions"] for e in employees_data)
            }
        }
    
    async def generate_income_report_by_type(self) -> Dict[str, Any]:
        """
        Генерира справка за доходите по видове (чл. 73, ал. 6 ЗДДФЛ).
        """
        # Вземи всички заплати за годината
        result = await self.db.execute(
            select(Payslip).where(
                and_(
                    func.extract('year', Payslip.period_start) == self.year,
                    Payslip.payment_status == 'paid'
                )
            )
        )
        payslips = result.scalars().all()
        
        income_by_employee = {}
        
        for payslip in payslips:
            user_id = payslip.user_id
            
            if user_id not in income_by_employee:
                user = await self.db.get(User, user_id)
                income_by_employee[user_id] = {
                    "egn": user.egn or "",
                    "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                    "incomes": []
                }
            
            # Добави дохода
            income_by_employee[user_id]["incomes"].append({
                "type": "01",  # Трудово възнаграждение
                "date": payslip.period_end.strftime("%Y-%m-%d"),
                "gross": float(payslip.gross_salary or payslip.total_amount),
                "tax": float(payslip.income_tax or 0),
                "net": float(payslip.total_amount) - float(payslip.income_tax or 0)
            })
        
        return {
            "year": self.year,
            "company_id": self.company_id,
            "report_type": "income_by_type_73_6",
            "generated_at": datetime.now().isoformat(),
            "employees": income_by_employee,
            "summary": {
                "total_employees": len(income_by_employee),
                "total_gross": sum(
                    sum(i["gross"] for i in e["incomes"]) 
                    for e in income_by_employee.values()
                ),
                "total_tax": sum(
                    sum(i["tax"] for i in e["incomes"]) 
                    for e in income_by_employee.values()
                )
            }
        }
    
    async def generate_service_book_export(self) -> Dict[str, Any]:
        """
        Генерира експорт за електронната трудова книжка.
        Съдържа цялата история на заетостта.
        """
        result = await self.db.execute(
            select(EmploymentContract).where(
                EmploymentContract.company_id == self.company_id
            )
        )
        contracts = result.scalars().all()
        
        employees_data = []
        
        for contract in contracts:
            user = contract.user
            
            # История на договорите
            contract_history = []
            
            # Основен договор
            contract_history.append({
                "type": "employment",
                "start_date": contract.start_date.strftime("%Y-%m-%d") if contract.start_date else None,
                "end_date": contract.end_date.strftime("%Y-%m-%d") if contract.end_date else None,
                "position": contract.position.name if contract.position else "",
                "base_salary": float(contract.base_salary or 0),
                "hours_per_week": contract.work_hours_per_week,
                "status": "active" if contract.is_active else "terminated"
            })
            
            # Вземи заплатите
            payslips_result = await self.db.execute(
                select(Payslip).where(
                    and_(
                        Payslip.user_id == user.id,
                        func.extract('year', Payslip.period_start) >= contract.start_date.year if contract.start_date else True
                    )
                )
            )
            payslips = payslips_result.scalars().all()
            
            employees_data.append({
                "egn": user.egn or "",
                "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                "contracts": contract_history,
                "periods": [
                    {
                        "year": p.period_start.year,
                        "month": p.period_start.month,
                        "gross": float(p.gross_salary or p.total_amount),
                        "net": float(p.total_amount)
                    }
                    for p in payslips
                ]
            })
        
        return {
            "year": self.year,
            "company_id": self.company_id,
            "report_type": "service_book",
            "generated_at": datetime.now().isoformat(),
            "employees": employees_data
        }
    
    async def generate_monthly_declaration(self, month: int) -> Dict[str, Any]:
        """
        Генерира месечна декларация за НАП.
        """
        # Вземи всички заплати за месеца
        result = await self.db.execute(
            select(Payslip).where(
                and_(
                    func.extract('year', Payslip.period_start) == self.year,
                    func.extract('month', Payslip.period_start) == month,
                    Payslip.payment_status == 'paid'
                )
            )
        )
        payslips = result.scalars().all()
        
        declarations = []
        
        for payslip in payslips:
            user = await self.db.get(User, payslip.user_id)
            
            declarations.append({
                "egn": user.egn or "",
                "name": f"{user.firstName or ''} {user.lastName or ''}".strip(),
                "income_type": "01",  # Трудово
                "gross": float(payslip.gross_salary or payslip.total_amount),
                "insurance": float(payslip.doo_employee or 0) + float(payslip.zo_employee or 0),
                "tax": float(payslip.income_tax or 0),
                "period": f"{self.year}-{month:02d}"
            })
        
        return {
            "year": self.year,
            "month": month,
            "company_id": self.company_id,
            "report_type": "monthly_declaration",
            "generated_at": datetime.now().isoformat(),
            "declarations": declarations,
            "summary": {
                "total_gross": sum(d["gross"] for d in declarations),
                "total_insurance": sum(d["insurance"] for d in declarations),
                "total_tax": sum(d["tax"] for d in declarations)
            }
        }
