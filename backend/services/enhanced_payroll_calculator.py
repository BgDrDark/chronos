from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from backend.services.payroll_calculator import PayrollCalculator
from backend.database.models import (
    User, WorkSchedule, TimeLog, LeaveRequest, PublicHoliday, 
    Payroll, Payslip, PayrollPaymentSchedule, PayrollDeduction,
    SickLeaveRecord, NOIPaymentDays, EmploymentContract, PayrollPeriod, Payment,
    AdvancePayment, ServiceLoan
)
from backend.database.models import sofia_now


class EnhancedPayrollCalculator(PayrollCalculator):
    """
    Enhanced Payroll Calculator with support for:
    - Employment contracts (labor vs civil)
    - Payment schedules
    - Additional deductions
    - Sick leave calculations per Bulgarian law
    - NOI payment days
    - Company-specific policies
    """
    
    def __init__(self, db_session: AsyncSession, company_id: int, user_id: int, calculation_period: Dict[str, date], preloaded_data: Optional[Dict[str, Any]] = None):
        super().__init__(db_session)
        self.company_id = company_id
        self.user_id = user_id
        self.calculation_period = calculation_period
        self.preloaded_data = preloaded_data
        self.payment_schedule = None
        self.additional_deductions = []
        self.sick_leave_records = []
        self.employment_contract = None
        self.noi_payment_days = None
        self.advance_payments = []
        self.active_loans = []
        
    async def calculate_enhanced_payroll(self) -> Dict[str, Any]:
        """Calculate complete payroll with all new components"""
        base_calculation = await self.calculate(
            self.user_id, 
            self.calculation_period['start_date'], 
            self.calculation_period['end_date']
        )
        
        # Load additional components (from preloaded data if available)
        if self.preloaded_data:
            await self._apply_preloaded_data()
        else:
            await self._load_additional_components()
        
        # Add payment date
        payment_date = await self._get_payment_date()
        
        # Calculate additional deductions
        additional_deductions = await self._calculate_additional_deductions()
        
        # Calculate sick leave payments
        sick_payments = await self._calculate_sick_leave_payments()
        
        # Calculate NOI payments (employer contribution)
        noi_payments = await self._calculate_noi_payments()
        
        # Calculate base salary from contract
        base_salary = await self._get_base_salary()
        
        # Calculate gross/net based on contract settings
        gross_amount, net_amount = await self._calculate_gross_net(
            base_salary, base_calculation
        )
        
        # Final calculations
        total_deductions_base = base_calculation.get('total_deductions', Decimal('0')) + additional_deductions
        
        # 1. Advance Payments for the period
        total_advances = sum([Decimal(str(ap.amount)) for ap in self.advance_payments])
        
        # 2. Loan Installments
        loan_deductions = Decimal('0')
        loan_details = []
        for loan in self.active_loans:
            amount = min(Decimal(str(loan.installment_amount)), Decimal(str(loan.remaining_amount)))
            loan_deductions += amount
            loan_details.append({
                "loan_id": loan.id,
                "amount": float(amount),
                "description": loan.description,
                "remaining_before": float(loan.remaining_amount)
            })

        # Net Payable is after taxes, insurance, and ALL deductions/advances
        net_payable = net_amount - additional_deductions - loan_deductions - total_advances + sick_payments
        
        # Salary Installments logic
        installments_count = 1
        if self.employment_contract and self.employment_contract.salary_installments_count:
            installments_count = max(1, self.employment_contract.salary_installments_count)
            
        installment_amount = net_payable / Decimal(str(installments_count))
        
        return {
            **base_calculation,
            'payment_date': payment_date,
            'additional_deductions': float(additional_deductions),
            'sick_leave_payments': float(sick_payments),
            'total_deductions': float(total_deductions_base + loan_deductions + total_advances),
            'gross_amount': float(gross_amount),
            'net_amount': float(net_amount),
            'net_payable': float(net_payable),
            'advances': float(total_advances),
            'loan_deductions': float(loan_deductions),
            'loan_details': loan_details,
            'installments': {
                'count': installments_count,
                'amount_per_installment': float(installment_amount)
            },
            'contract_type': self.employment_contract.contract_type if self.employment_contract else 'unknown'
        }
    
    async def _apply_preloaded_data(self):
        """Map preloaded data to calculator attributes"""
        self.payment_schedule = self.preloaded_data.get('payment_schedule')
        self.employment_contract = self.preloaded_data.get('contracts', {}).get(self.user_id)
        self.additional_deductions = self.preloaded_data.get('deductions', [])
        self.sick_leave_records = self.preloaded_data.get('sick_records', {}).get(self.user_id, [])
        self.noi_payment_days = self.preloaded_data.get('noi_days', {}).get(self.user_id)
        self.advance_payments = self.preloaded_data.get('advances', {}).get(self.user_id, [])
        self.active_loans = self.preloaded_data.get('loans', {}).get(self.user_id, [])

    async def _load_additional_components(self):
        """Load all additional components for payroll calculation"""
        # Load payment schedule
        schedule_query = select(PayrollPaymentSchedule).where(
            PayrollPaymentSchedule.company_id == self.company_id,
            PayrollPaymentSchedule.active == True
        )
        schedule_result = await self.db.execute(schedule_query)
        self.payment_schedule = schedule_result.scalar_one_or_none()
        
        # Load employment contract
        contract_query = select(EmploymentContract).where(
            and_(
                EmploymentContract.user_id == self.user_id,
                EmploymentContract.company_id == self.company_id,
                EmploymentContract.is_active == True
            )
        )
        contract_result = await self.db.execute(contract_query)
        self.employment_contract = contract_result.scalar_one_or_none()
        
        # Load additional deductions
        deductions_query = select(PayrollDeduction).where(
            and_(
                PayrollDeduction.company_id == self.company_id,
                PayrollDeduction.is_active == True
            )
        )
        deductions_result = await self.db.execute(deductions_query)
        self.additional_deductions = deductions_result.scalars().all()
        
        # Load sick leave records
        sick_query = select(SickLeaveRecord).where(
            and_(
                SickLeaveRecord.user_id == self.user_id,
                SickLeaveRecord.start_date >= self.calculation_period['start_date'],
                SickLeaveRecord.end_date <= self.calculation_period['end_date']
            )
        )
        sick_result = await self.db.execute(sick_query)
        self.sick_leave_records = sick_result.scalars().all()
        
        # Load NOI payment days
        noi_query = select(NOIPaymentDays).where(
            and_(
                NOIPaymentDays.user_id == self.user_id,
                NOIPaymentDays.year == self.calculation_period['start_date'].year
            )
        )
        noi_result = await self.db.execute(noi_query)
        self.noi_payment_days = noi_result.scalar_one_or_none()

        # Load advances for this period
        adv_query = select(AdvancePayment).where(
            and_(
                AdvancePayment.user_id == self.user_id,
                AdvancePayment.payment_date >= self.calculation_period['start_date'],
                AdvancePayment.payment_date <= self.calculation_period['end_date'],
                AdvancePayment.is_processed == False
            )
        )
        adv_res = await self.db.execute(adv_query)
        self.advance_payments = adv_res.scalars().all()
        
        # Load active loans
        loan_query = select(ServiceLoan).where(
            and_(
                ServiceLoan.user_id == self.user_id,
                ServiceLoan.is_active == True,
                ServiceLoan.remaining_amount > 0,
                ServiceLoan.start_date <= self.calculation_period['end_date']
            )
        )
        loan_res = await self.db.execute(loan_query)
        self.active_loans = loan_res.scalars().all()
    
    async def _get_payment_date(self) -> date:
        """Determine payment date according to company settings"""
        if not self.payment_schedule:
            # Default: 25-то число на следващия месец
            next_month = self.calculation_period['end_date'].replace(day=1) + timedelta(days=32)
            return next_month.replace(day=25)
        
        target_day = self.payment_schedule.payment_day
        target_month = self.calculation_period['end_date'].month + self.payment_schedule.payment_month_offset
        target_year = self.calculation_period['end_date'].year
        
        if target_month > 12:
            target_month -= 12
            target_year += 1
        
        return date(target_year, target_month, target_day)
    
    async def _calculate_additional_deductions(self) -> Decimal:
        """Calculate all applicable additional deductions"""
        total_deduction = Decimal('0')
        
        for deduction in self.additional_deductions:
            if deduction.apply_to_all or (deduction.employee_ids and self.user_id in deduction.employee_ids):
                if deduction.deduction_type == 'fixed':
                    total_deduction += Decimal(str(deduction.amount))
                elif deduction.deduction_type == 'percentage':
                    base_salary = await self._get_base_salary()
                    if base_salary:
                        percentage_amount = base_salary * (Decimal(str(deduction.percentage)) / Decimal('100'))
                        total_deduction += percentage_amount
        
        return total_deduction
    
    async def _calculate_sick_leave_payments(self) -> Decimal:
        """Calculate sick leave payments according to Bulgarian law"""
        total_sick_payment = Decimal('0')
        
        for record in self.sick_leave_records:
            payment = await self._calculate_single_sick_leave_payment(record)
            total_sick_payment += payment
        
        return total_sick_payment
    
    async def _calculate_single_sick_leave_payment(self, sick_record: SickLeaveRecord) -> Decimal:
        """Calculate payment using dynamic legal settings from database"""
        from backend import crud
        daily_gross = await self._get_daily_gross_salary()
        if not daily_gross: return Decimal('0')
        
        # Load dynamic settings
        noi_perc_str = await crud.get_global_setting(self.db, "payroll_noi_compensation_percent")
        emp_days_str = await crud.get_global_setting(self.db, "payroll_employer_paid_sick_days")
        
        NOI_PERCENT = (Decimal(noi_perc_str) if noi_perc_str else Decimal('80.0')) / Decimal('100')
        EMPLOYER_DAYS = int(emp_days_str) if emp_days_str else 3
        
        total_payment = Decimal('0')
        
        if sick_record.sick_leave_type == 'general':
            # 1. Employer days (usually first 3)
            employer_days = min(EMPLOYER_DAYS, sick_record.total_days)
            # Typically employer pays 70% or 75% for these days in BG
            emp_rate = Decimal(str(sick_record.employer_payment_percentage or 70.0)) / Decimal('100')
            total_payment += Decimal(str(employer_days)) * daily_gross * emp_rate
            
            # 2. NOI days (the rest)
            noi_days = max(0, sick_record.total_days - employer_days)
            noi_payment = Decimal(str(noi_days)) * daily_gross * NOI_PERCENT
            total_payment += noi_payment
            
            # 3. Employer Top-up (if requested)
            leave_req_query = select(LeaveRequest).where(
                and_(
                    LeaveRequest.user_id == self.user_id,
                    LeaveRequest.start_date == sick_record.start_date,
                    LeaveRequest.leave_type == 'sick_leave',
                    LeaveRequest.employer_top_up == True
                )
            )
            lr_res = await self.db.execute(leave_req_query)
            if lr_res.scalar_one_or_none():
                # Top up the difference to 100%
                full_potential = Decimal(str(sick_record.total_days)) * daily_gross
                total_payment = full_potential
                
        elif sick_record.sick_leave_type == 'work_related':
            total_payment = Decimal(str(sick_record.total_days)) * daily_gross
            
        return total_payment
    
    async def _calculate_noi_payments(self) -> Decimal:
        """Calculate employer contributions for NOI payment days"""
        if not self.noi_payment_days or self.noi_payment_days.employer_payment_percentage <= 0:
            return Decimal('0')
        
        # Ако са използвани НОЙ дни и има 75% плащане от работодателя
        if self.noi_payment_days.noi_days_used > 0:
            daily_salary = await self._get_daily_gross_salary()
            if daily_salary:
                employer_payment_percentage = Decimal(str(self.noi_payment_days.employer_payment_percentage)) / Decimal('100')
                return Decimal(str(self.noi_payment_days.noi_days_used)) * daily_salary * employer_payment_percentage
        
        return Decimal('0')
    
    async def _get_base_salary(self) -> Optional[Decimal]:
        """Get base salary from employment contract or payroll"""
        if self.employment_contract:
            return Decimal(str(self.employment_contract.base_salary)) if self.employment_contract.base_salary else None
        
        # Fallback to existing payroll configuration
        payroll_query = select(Payroll).where(
            and_(
                Payroll.user_id == self.user_id,
                Payroll.company_id == self.company_id
            )
        )
        payroll_result = await self.db.execute(payroll_query)
        payroll = payroll_result.scalar_one_or_none()
        
        if payroll:
            if payroll.monthly_salary:
                return Decimal(str(payroll.monthly_salary))
            elif payroll.hourly_rate:
                # Estimate monthly from hourly rate
                monthly_hours = Decimal('160')  # 40 hours/week * 4 weeks
                return payroll.hourly_rate * monthly_hours
        
        return None
    
    async def _get_daily_gross_salary(self) -> Optional[Decimal]:
        """Calculate daily gross salary"""
        base_salary = await self._get_base_salary()
        if not base_salary:
            return None
        
        # Standard: 21.67 working days per month (260 days / 12 months)
        daily_salary = base_salary / Decimal('21.67')
        return daily_salary
    
    async def _calculate_gross_net(self, base_salary: Optional[Decimal], base_calculation: Dict[str, Any]) -> tuple[Decimal, Decimal]:
        """Calculate gross and net amounts based on dynamic global settings"""
        if not base_salary:
            return Decimal('0'), Decimal('0')
        
        # Извличане на настройките от базата с дефолтни стойности по закон
        from backend import crud
        max_ins_str = await crud.get_global_setting(self.db, "payroll_max_insurance_base")
        ins_rate_str = await crud.get_global_setting(self.db, "payroll_employee_insurance_rate")
        tax_rate_str = await crud.get_global_setting(self.db, "payroll_income_tax_rate")
        civil_costs_str = await crud.get_global_setting(self.db, "payroll_civil_contract_costs_rate")

        MAX_INSURANCE_BASE = Decimal(max_ins_str) if max_ins_str else Decimal('3750.00')
        INSURANCE_RATE = (Decimal(ins_rate_str) if ins_rate_str else Decimal('13.78')) / Decimal('100')
        INCOME_TAX_RATE = (Decimal(tax_rate_str) if tax_rate_str else Decimal('10.00')) / Decimal('100')
        CIVIL_COSTS_RATE = (Decimal(civil_costs_str) if civil_costs_str else Decimal('25.00')) / Decimal('100')
        
        if not self.employment_contract:
            return base_salary, base_salary * (Decimal('1.0') - INCOME_TAX_RATE)
        
        contract_type = self.employment_contract.contract_type
        calculation_type = self.employment_contract.salary_calculation_type
        is_contributor = getattr(self.employment_contract, 'insurance_contributor', True)
        
        gross_amount = base_salary
        net_amount = base_salary
        
        if contract_type == 'civil_contract':
            if calculation_type == 'gross':
                # Признати разходи (напр. 25%)
                taxable_base = gross_amount * (Decimal('1.0') - CIVIL_COSTS_RATE)
                
                # ДОД се смята само ако е активиран за договора
                income_tax = Decimal('0')
                if getattr(self.employment_contract, 'has_income_tax', True):
                    income_tax = taxable_base * INCOME_TAX_RATE
                
                net_amount = gross_amount - income_tax
            else:
                # Приблизително изчисление за нето към бруто
                if getattr(self.employment_contract, 'has_income_tax', True):
                    divider = Decimal('1.0') - (Decimal('1.0') - CIVIL_COSTS_RATE) * INCOME_TAX_RATE
                    gross_amount = net_amount / divider
                else:
                    gross_amount = net_amount # No tax, Net = Gross
        
        elif contract_type in ['full_time', 'part_time']:
            if calculation_type == 'gross':
                # 1. Осигурителна база
                insurance_base = min(gross_amount, MAX_INSURANCE_BASE)
                
                # 2. Лични осигуровки
                insurance_contributions = Decimal('0')
                if is_contributor:
                    insurance_contributions = insurance_base * INSURANCE_RATE
                
                # 3. ДОД
                taxable_amount = gross_amount - insurance_contributions
                income_tax = taxable_amount * INCOME_TAX_RATE
                
                net_amount = gross_amount - insurance_contributions - income_tax
            else:
                # Използваме подобрената обратна калкулация с динамични стойности
                gross_amount = await self._reverse_calculate_gross_from_net(
                    net_amount, MAX_INSURANCE_BASE, INSURANCE_RATE, INCOME_TAX_RATE
                )
        
        else:  # contractor, internship, etc.
            # Minimal deductions for unknown types
            if calculation_type == 'gross':
                net_amount = gross_amount * (Decimal('1.0') - INCOME_TAX_RATE)
            else:
                gross_amount = net_amount / (Decimal('1.0') - INCOME_TAX_RATE)
        
        return gross_amount, net_amount
    
    async def _reverse_calculate_gross_from_net(self, net_amount: Decimal, max_base: Decimal, ins_rate: Decimal, tax_rate: Decimal) -> Decimal:
        """Обратна калкулация с динамични коефициенти"""
        max_ins_deduction = max_base * ins_rate
        net_threshold = max_base - max_ins_deduction - (max_base - max_ins_deduction) * tax_rate
        
        if self.employment_contract and self.employment_contract.contract_type == 'civil_contract':
            from backend import crud
            civil_costs_str = await crud.get_global_setting(self.db, "payroll_civil_contract_costs_rate")
            civil_rate = (Decimal(civil_costs_str) if civil_costs_str else Decimal('25.00')) / Decimal('100')
            divider = Decimal('1.0') - (Decimal('1.0') - civil_rate) * tax_rate
            return net_amount / divider
            
        if net_amount <= net_threshold:
            # Коефициент под прага: Net = Gross * (1 - ins_rate) * (1 - tax_rate)
            coef = (Decimal('1.0') - ins_rate) * (Decimal('1.0') - tax_rate)
            return net_amount / coef
        else:
            # Над прага: Net = Gross - max_ins_deduction - (Gross - max_ins_deduction) * tax_rate
            # Net = Gross * (1 - tax_rate) - max_ins_deduction * (1 - tax_rate)
            return (net_amount + max_ins_deduction * (Decimal('1.0') - tax_rate)) / (Decimal('1.0') - tax_rate)


def calculate_sick_leave_payment_by_law(
    daily_gross: Decimal, 
    total_days: int, 
    leave_type: str = 'general'
) -> Dict[str, Any]:
    """
    Calculate sick leave payment according to Bulgarian Labor Code
    
    General Sick Leave Rules:
    - Days 1-3: No payment
    - Days 4-30: 80% from National Insurance Fund (NOI)
    - Days 31+: 100% from employer
    
    Work-related Injury:
    - 100% from NOI from day 1
    
    Returns detailed breakdown of payments
    """
    unpaid_days = 0
    noi_payment_days = 0
    employer_payment_days = 0
    
    if leave_type == 'general':
        unpaid_days = min(3, total_days)
        noi_payment_days = max(0, min(27, total_days - 3))
        employer_payment_days = max(0, total_days - 30)
    elif leave_type == 'work_related':
        noi_payment_days = total_days  # 100% from NOI
    
    # Calculate payments
    unpaid_amount = Decimal(str(unpaid_days)) * daily_gross
    noi_payment = Decimal(str(noi_payment_days)) * daily_gross * Decimal('0.80')
    employer_payment = Decimal(str(employer_payment_days)) * daily_gross
    total_payment = noi_payment + employer_payment
    
    return {
        'unpaid_days': unpaid_days,
        'noi_payment_days': noi_payment_days,
        'employer_payment_days': employer_payment_days,
        'unpaid_amount': float(unpaid_amount),
        'noi_payment': float(noi_payment),
        'employer_payment': float(employer_payment),
        'total_payment': float(total_payment),
        'daily_gross': float(daily_gross),
        'leave_type': leave_type,
        'total_days': total_days
    }