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
    AdvancePayment, ServiceLoan, NightWorkBonus, OvertimeWork, WorkOnHoliday, BusinessTrip
)
from backend.database.models import sofia_now
from backend.services.trz_calculators import NightWorkCalculator, OvertimeCalculator, BusinessTripCalculator
from backend import crud


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
        
        # ТРЗ компоненти
        self.night_work_records = []
        self.overtime_records = []
        self.business_trips = []
        self.work_on_holidays = []
        
        # Калкулатори
        self.night_work_calc = NightWorkCalculator()
        self.overtime_calc = OvertimeCalculator()
        self.business_trip_calc = BusinessTripCalculator()
        
    async def calculate_enhanced_payroll(self) -> Dict[str, Any]:
        """Calculate complete payroll with all new components"""
        start_date = datetime.combine(self.calculation_period['start_date'], datetime.min.time())
        end_date = datetime.combine(self.calculation_period['end_date'], datetime.max.time())
        base_calculation = await self.calculate(
            self.user_id, 
            start_date, 
            end_date
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
        
        # ==================== ТРЗ: Изчисления ====================
        
        # Calculate night work amount
        night_work_amount = await self._calculate_night_work()
        
        # Calculate overtime amount
        overtime_amount = await self._calculate_overtime()
        
        # Calculate work on holidays amount
        holiday_amount = await self._calculate_work_on_holidays()
        
        # Calculate business trip amount
        trip_amount = await self._calculate_business_trips()
        
        # Calculate base salary from contract
        base_salary = await self._get_base_salary()
        
        # Calculate experience bonus (Class)
        experience_bonus = await self._calculate_experience_bonus(base_salary or Decimal('0'))
        
        # Calculate gross/net based on contract settings (include class bonus in gross)
        gross_amount, net_amount = await self._calculate_gross_net(
            (base_salary or Decimal('0')) + experience_bonus, base_calculation
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
            'contract_type': self.employment_contract.contract_type if self.employment_contract else 'unknown',
            # ТРЗ компоненти
            'experience_bonus': float(experience_bonus),
            'night_work_amount': float(night_work_amount),
            'overtime_amount': float(overtime_amount),
            'holiday_amount': float(holiday_amount),
            'trip_amount': float(trip_amount),
            'night_work_count': len(self.night_work_records),
            'overtime_hours': sum(float(r.hours) for r in self.overtime_records),
            'holiday_hours': sum(float(r.hours) for r in self.work_on_holidays),
            'business_trip_count': len(self.business_trips),
        }
    
    async def _apply_preloaded_data(self):
        """Map preloaded data to calculator attributes"""
        if not self.preloaded_data:
            return
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
        from sqlalchemy.orm import selectinload
        contract_query = select(EmploymentContract).options(
            selectinload(EmploymentContract.user)
        ).where(
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
        
        # ==================== ТРЗ: Зареждане на записи ====================
        
        # Load night work bonuses
        night_query = select(NightWorkBonus).where(
            and_(
                NightWorkBonus.user_id == self.user_id,
                NightWorkBonus.date >= self.calculation_period['start_date'],
                NightWorkBonus.date <= self.calculation_period['end_date'],
                NightWorkBonus.is_paid == False
            )
        )
        night_res = await self.db.execute(night_query)
        self.night_work_records = night_res.scalars().all()
        
        # Load overtime works
        overtime_query = select(OvertimeWork).where(
            and_(
                OvertimeWork.user_id == self.user_id,
                OvertimeWork.date >= self.calculation_period['start_date'],
                OvertimeWork.date <= self.calculation_period['end_date'],
                OvertimeWork.is_paid == False
            )
        )
        overtime_res = await self.db.execute(overtime_query)
        self.overtime_records = overtime_res.scalars().all()
        
        # Load work on holidays
        holiday_query = select(WorkOnHoliday).where(
            and_(
                WorkOnHoliday.user_id == self.user_id,
                WorkOnHoliday.date >= self.calculation_period['start_date'],
                WorkOnHoliday.date <= self.calculation_period['end_date'],
                WorkOnHoliday.is_paid == False
            )
        )
        holiday_res = await self.db.execute(holiday_query)
        self.work_on_holidays = holiday_res.scalars().all()
        
        # Load approved business trips
        trip_query = select(BusinessTrip).where(
            and_(
                BusinessTrip.user_id == self.user_id,
                BusinessTrip.start_date >= self.calculation_period['start_date'],
                BusinessTrip.end_date <= self.calculation_period['end_date'],
                BusinessTrip.status == 'approved'
            )
        )
        trip_res = await self.db.execute(trip_query)
        self.business_trips = trip_res.scalars().all()
    
    async def _get_payment_date(self) -> date:
        """Determine payment date according to company/contract settings"""
        # Приоритет 1: Ден в индивидуалния договор
        if self.employment_contract and self.employment_contract.payment_day:
            target_day = self.employment_contract.payment_day
            target_month = self.calculation_period['end_date'].month + 1
        elif self.payment_schedule:
            # Приоритет 2: Фирмен график
            target_day = self.payment_schedule.payment_day
            target_month = self.calculation_period['end_date'].month + self.payment_schedule.payment_month_offset
        else:
            # Default: 25-то число на следващия месец
            target_day = 25
            end_month = self.calculation_period['end_date'].month
            target_month = (int(end_month) if hasattr(end_month, '__int__') else end_month) + 1
            
        end_year = self.calculation_period['end_date'].year
        target_year = int(end_year) if hasattr(end_year, '__int__') else end_year
        
        month_val = int(target_month) if hasattr(target_month, '__int__') else target_month
        if month_val > 12:
            target_month = month_val - 12
            target_year += 1
        
        # Предпазване от невалидни дати (напр. 31 февруари)
        import calendar
        year_val = int(target_year) if hasattr(target_year, '__int__') else target_year
        month_val2 = int(target_month) if hasattr(target_month, '__int__') else target_month
        last_day = calendar.monthrange(year_val, month_val2)[1]
        target_day = min(target_day, last_day)
        
        return date(target_year, target_month, target_day)
    
    async def _calculate_additional_deductions(self) -> Decimal:
        """Calculate all applicable additional deductions"""
        total_deduction = Decimal('0')
        
        for deduction in self.additional_deductions:
            if bool(deduction.apply_to_all) is True or (deduction.employee_ids is not None and self.user_id in deduction.employee_ids):
                if str(deduction.deduction_type) == 'fixed':
                    total_deduction += Decimal(str(deduction.amount))
                elif str(deduction.deduction_type) == 'percentage':
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
        
        if str(sick_record.sick_leave_type) == 'general':
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
                
        elif str(sick_record.sick_leave_type) == 'work_related':
            total_payment = Decimal(str(sick_record.total_days)) * daily_gross
            
        return total_payment
    
    async def _calculate_noi_payments(self) -> Decimal:
        """Calculate employer contributions for NOI payment days"""
        if not self.noi_payment_days or float(str(self.noi_payment_days.employer_payment_percentage or 0)) <= 0:
            return Decimal('0')
        
        # Ако са използвани НОЙ дни и има 75% плащане от работодателя
        if str(self.noi_payment_days.noi_days_used) > '0':
            daily_salary = await self._get_daily_gross_salary()
            if daily_salary:
                employer_payment_percentage = Decimal(str(self.noi_payment_days.employer_payment_percentage)) / Decimal('100')
                return Decimal(str(self.noi_payment_days.noi_days_used)) * daily_salary * employer_payment_percentage
        
        return Decimal('0')
    
    # --- Осигуровки (Фаза 1) ---
    
    async def _get_insurance_base(self, gross_amount: Decimal) -> Decimal:
        """
        Изчислява осигурителната база (минимум/максимум).
        """
        # Вземи лимитите от GlobalSettings или подразбиране
        from backend import crud
        
        max_insurable_base_str = await crud.get_global_setting(self.db, "payroll_max_insurable_base")
        min_insurable_base_str = await crud.get_global_setting(self.db, "payroll_min_wage")
        
        max_base = Decimal(max_insurable_base_str) if max_insurable_base_str else Decimal('4100')
        min_base = Decimal(min_insurable_base_str) if min_insurable_base_str else Decimal('1213')
        
        # Осигурителната база е между мин и макс
        return max(min(gross_amount, max_base), min_base)
    
    async def _calculate_doo(self, gross_amount: Decimal) -> dict:
        """
        Изчислява ДОО (Държавно обществено осигуряване).
        Зависи от годината на раждане на служителя.
        """
        from backend import crud
        from datetime import datetime
        
        insurance_base = await self._get_insurance_base(gross_amount)
        
        # Вземи годината на раждане от employment contract
        birth_year = None
        if self.employment_contract and self.employment_contract.user:
            if hasattr(self.employment_contract.user, 'birth_date') and self.employment_contract.user.birth_date:
                birth_year = self.employment_contract.user.birth_date.year
        
        # Ако е роден преди 1960 - по-висока ставка
        if birth_year and birth_year < 1960:
            rates = await crud.get_insurance_rate(self.db, 
                self.calculation_period['start_date'].year, 
                self.calculation_period['start_date'].month, 
                "doo_older"
            )
        else:
            rates = await crud.get_insurance_rate(self.db,
                self.calculation_period['start_date'].year,
                self.calculation_period['start_date'].month,
                "doo"
            )
        
        employee_rate = Decimal(str(rates.get('employee_rate', 14.3)))
        employer_rate = Decimal(str(rates.get('employer_rate', 14.3)))
        
        employee_contribution = insurance_base * employee_rate / Decimal('100')
        employer_contribution = insurance_base * employer_rate / Decimal('100')
        
        return {
            "base": float(insurance_base),
            "employee_rate": float(employee_rate),
            "employer_rate": float(employer_rate),
            "employee_amount": float(employee_contribution),
            "employer_amount": float(employer_contribution)
        }
    
    async def _calculate_zo(self, gross_amount: Decimal) -> dict:
        """Изчислява ЗО (Здравно осигуряване)."""
        from backend import crud
        
        insurance_base = await self._get_insurance_base(gross_amount)
        
        rates = await crud.get_insurance_rate(self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month,
            "zo"
        )
        
        employee_rate = Decimal(str(rates.get('employee_rate', 3.2)))
        employer_rate = Decimal(str(rates.get('employer_rate', 4.8)))
        
        employee_contribution = insurance_base * employee_rate / Decimal('100')
        employer_contribution = insurance_base * employer_rate / Decimal('100')
        
        return {
            "base": float(insurance_base),
            "employee_rate": float(employee_rate),
            "employer_rate": float(employer_rate),
            "employee_amount": float(employee_contribution),
            "employer_amount": float(employer_contribution)
        }
    
    async def _calculate_dzpo(self, gross_amount: Decimal) -> dict:
        """Изчислява ДЗПО (Допълнително пенсионно осигуряване)."""
        from backend import crud
        
        # ДЗПО е само за родени след 1959
        birth_year = None
        if self.employment_contract and self.employment_contract.user:
            if hasattr(self.employment_contract.user, 'birth_date') and self.employment_contract.user.birth_date:
                birth_year = self.employment_contract.user.birth_date.year
        
        if birth_year and birth_year >= 1960:
            insurance_base = await self._get_insurance_base(gross_amount)
            
            rates = await crud.get_insurance_rate(self.db,
                self.calculation_period['start_date'].year,
                self.calculation_period['start_date'].month,
                "dzpo"
            )
            
            employee_rate = Decimal(str(rates.get('employee_rate', 2.2)))
            employer_rate = Decimal(str(rates.get('employer_rate', 2.8)))
            
            employee_contribution = insurance_base * employee_rate / Decimal('100')
            employer_contribution = insurance_base * employer_rate / Decimal('100')
        else:
            # За родени преди 1960 - няма ДЗПО
            return {
                "base": 0,
                "employee_rate": 0,
                "employer_rate": 0,
                "employee_amount": 0,
                "employer_amount": 0
            }
        
        return {
            "base": float(insurance_base),
            "employee_rate": float(employee_rate),
            "employer_rate": float(employer_rate),
            "employee_amount": float(employee_contribution),
            "employer_amount": float(employer_contribution)
        }
    
    async def _calculate_tzpb(self, gross_amount: Decimal) -> dict:
        """Изчислява ТЗПБ (Трудова злополука и професионална болест) - само за работодател."""
        from backend import crud
        
        insurance_base = await self._get_insurance_base(gross_amount)
        
        rates = await crud.get_insurance_rate(self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month,
            "tzpb"
        )
        
        employer_rate = Decimal(str(rates.get('employer_rate', 0.4)))
        
        employer_contribution = insurance_base * employer_rate / Decimal('100')
        
        return {
            "base": float(insurance_base),
            "employer_rate": float(employer_rate),
            "employer_amount": float(employer_contribution)
        }
    
    async def calculate_all_insurances(self, gross_amount: Decimal) -> dict:
        """
        Изчислява всички осигуровки.
        """
        doo = await self._calculate_doo(gross_amount)
        zo = await self._calculate_zo(gross_amount)
        dzpo = await self._calculate_dzpo(gross_amount)
        tzpb = await self._calculate_tzpb(gross_amount)
        
        return {
            "doo": doo,
            "zo": zo,
            "dzpo": dzpo,
            "tzpb": tzpb,
            "total_employee": doo["employee_amount"] + zo["employee_amount"] + dzpo["employee_amount"],
            "total_employer": doo["employer_amount"] + zo["employer_amount"] + dzpo["employer_amount"] + tzpb["employer_amount"]
        }
    
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
            if payroll.monthly_salary is not None:
                return Decimal(str(payroll.monthly_salary))
            elif payroll.hourly_rate is not None:
                monthly_hours = Decimal('160')
                return Decimal(str(payroll.hourly_rate)) * monthly_hours
        
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
        
        # Използвай новите функции за данъци (Фаза 2)
        tax_rate_data = await crud.get_tax_rate(
            self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month
        )
        tax_rate = Decimal(str(tax_rate_data.get('rate', 10.0))) / Decimal('100')
        
        # Вземи стандартното подобрения
        deduction_data = await crud.get_tax_deduction(
            self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month,
            "standard"
        )
        standard_deduction = Decimal(str(deduction_data.get('amount', 500.0)))
        
        # Вземи осигуровките
        insurances = await self.calculate_all_insurances(base_salary)
        total_insurance_employee = Decimal(str(insurances.get('total_employee', 0)))
        
        # Изчисление на ДДФЛ
        # Данъчна база = Бруто - Осигуровки - Стандартно подобрения
        taxable_base = max(Decimal('0'), base_salary - total_insurance_employee - standard_deduction)
        income_tax = taxable_base * tax_rate
        
        # Нето = Бруто - Осигуровки - Данък
        net_amount = base_salary - total_insurance_employee - income_tax
        
        return base_salary, net_amount
    
    # --- Нови методи за данъци (Фаза 2) ---
    
    async def calculate_tax_details(self, gross_amount: Decimal) -> dict:
        """
        Изчислява детайлите за данъците.
        """
        from backend import crud
        
        # Вземи ставката
        tax_rate_data = await crud.get_tax_rate(
            self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month
        )
        tax_rate = Decimal(str(tax_rate_data.get('rate', 10.0)))
        
        # Вземи стандартното подобрения
        deduction_data = await crud.get_tax_deduction(
            self.db,
            self.calculation_period['start_date'].year,
            self.calculation_period['start_date'].month,
            "standard"
        )
        standard_deduction = Decimal(str(deduction_data.get('amount', 500.0)))
        
        # Вземи осигуровките
        insurances = await self.calculate_all_insurances(gross_amount)
        total_insurance_employee = Decimal(str(insurances.get('total_employee', 0)))
        
        # Данъчна база
        taxable_base = max(Decimal('0'), gross_amount - total_insurance_employee - standard_deduction)
        
        # Данък
        income_tax = taxable_base * (tax_rate / Decimal('100'))
        
        return {
            "gross_salary": float(gross_amount),
            "standard_deduction": float(standard_deduction),
            "insurance_employee_total": float(total_insurance_employee),
            "taxable_base": float(taxable_base),
            "tax_rate": float(tax_rate),
            "income_tax": float(income_tax),
            "tax_rate_source": tax_rate_data.get('source', 'settings'),
            "deduction_source": deduction_data.get('source', 'settings')
        }
    
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
        self,
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

        # ==================== ТРЗ Калкулатори ====================
    
    async def _is_trz_feature_enabled(self, feature_key: str) -> bool:
        """Проверява дали ТРЗ функцията е включена"""
        from backend import crud
        value = await crud.get_global_setting(self.db, feature_key)
        return value.lower() == "true" if value else False
    
    async def _calculate_night_work(self) -> Decimal:
        """Изчислява сумата за нощен труд"""
        # Проверяваме дали функцията е включена
        if not self._is_trz_feature_enabled("trz_night_work_enabled"):
            return Decimal('0')
        
        total_amount = Decimal('0')
        
        # Вземаме ставката от договора или използваме подразбиращата се
        night_rate = Decimal('0.5')  # 50% надбавка
        if self.employment_contract and self.employment_contract.night_work_rate:
            night_rate = self.employment_contract.night_work_rate
        
        for record in self.night_work_records:
            # Сума = часове * ставка * (1 + надбавка)
            hours = Decimal(str(record.hours))
            rate = Decimal(str(record.hourly_rate))
            amount = hours * rate * (Decimal('1') + night_rate)
            total_amount += amount
        
        return total_amount
    
    async def _calculate_overtime(self) -> Decimal:
        """Изчислява сумата за извънреден труд"""
        # Проверяваме дали функцията е включена
        if not self._is_trz_feature_enabled("trz_overtime_enabled"):
            return Decimal('0')
        
        total_amount = Decimal('0')
        
        for record in self.overtime_records:
            hours = Decimal(str(record.hours))
            rate = Decimal(str(record.hourly_rate))
            multiplier = Decimal(str(record.multiplier))
            amount = hours * rate * multiplier
            total_amount += amount
        
        return total_amount
    
    async def _calculate_work_on_holidays(self) -> Decimal:
        """Изчислява сумата за труд по празници"""
        # Проверяваме дали функцията е включена
        if not self._is_trz_feature_enabled("trz_holiday_work_enabled"):
            return Decimal('0')
        
        total_amount = Decimal('0')
        
        for record in self.work_on_holidays:
            hours = Decimal(str(record.hours))
            rate = Decimal(str(record.hourly_rate))
            multiplier = Decimal(str(record.multiplier))
            amount = hours * rate * multiplier
            total_amount += amount
        
        return total_amount
    
    async def _calculate_business_trips(self) -> Decimal:
        """Изчислява сумата за командировки"""
        # Проверяваме дали функцията е включена
        if not self._is_trz_feature_enabled("trz_business_trips_enabled"):
            return Decimal('0')
        
        total_amount = Decimal('0')
        
        for trip in self.business_trips:
            total_amount += Decimal(str(trip.total_amount))
        
        return total_amount
    
    async def calculate_trz_for_period(self) -> Dict[str, Any]:
        """
        Изчислява всички ТРЗ компоненти за период.
        Използва се за справки.
        """
        return {
            'night_work': {
                'count': len(self.night_work_records),
                'total_hours': sum(float(r.hours) for r in self.night_work_records),
                'total_amount': float(await self._calculate_night_work()),
                'records': [
                    {
                        'date': r.date,
                        'hours': float(r.hours),
                        'amount': float(r.amount)
                    }
                    for r in self.night_work_records
                ]
            },
            'overtime': {
                'count': len(self.overtime_records),
                'total_hours': sum(float(r.hours) for r in self.overtime_records),
                'total_amount': float(await self._calculate_overtime()),
                'records': [
                    {
                        'date': r.date,
                        'hours': float(r.hours),
                        'amount': float(r.amount)
                    }
                    for r in self.overtime_records
                ]
            },
            'holidays': {
                'count': len(self.work_on_holidays),
                'total_hours': sum(float(r.hours) for r in self.work_on_holidays),
                'total_amount': float(await self._calculate_work_on_holidays()),
                'records': [
                    {
                        'date': r.date,
                        'hours': float(r.hours),
                        'amount': float(r.amount)
                    }
                    for r in self.work_on_holidays
                ]
            },
            'business_trips': {
                'count': len(self.business_trips),
                'total_amount': float(await self._calculate_business_trips()),
                'records': [
                    {
                        'destination': t.destination,
                        'start_date': t.start_date,
                        'end_date': t.end_date,
                        'total_amount': float(str(t.total_amount)) if t.total_amount is not None else 0.0
                    }
                    for t in self.business_trips
                ]
            }
        }

    async def _calculate_experience_bonus(self, base_salary: Decimal) -> Decimal:
        """
        Изчислява добавка за трудов стаж и професионален опит (чл. 12 НСОРЗ).
        Минимум 0.6% за всяка година стаж.
        """
        if not self.employment_contract or not self.employment_contract.experience_start_date:
            return Decimal('0')
            
        # Изчисляваме годините стаж към края на периода
        end_date = self.calculation_period['end_date']
        start_date = self.employment_contract.experience_start_date
        
        years = end_date.year - start_date.year
        if (end_date.month, end_date.day) < (start_date.month, start_date.day):
            years -= 1
            
        if years <= 0:
            return Decimal('0')
            
        # Процентът може да е специфичен за договора или дефолт 0.6%
        # В модела добавихме work_class като текст, но за изчисленията ни трябва число
        # Ако няма специфичен процент в договора, ползваме 0.6%
        rate_per_year = Decimal('0.6') 
        
        total_percent = Decimal(str(years)) * rate_per_year
        bonus_amount = base_salary * (total_percent / 100)
        
        return bonus_amount.quantize(Decimal('0.01'))
    
    # --- Pro-rata изчисления (Фаза 4) ---
    
    async def get_contract_segments_for_period(
        self,
        contract_id: int
    ) -> list:
        """
        Връща списък от сегменти на договора за периода.
        Всеки сегмент има начална дата, крайна дата и заплата.
        """
        from backend.database.models import ContractAnnex
        from sqlalchemy import and_
        
        period_start = self.calculation_period['start_date']
        period_end = self.calculation_period['end_date']
        
        segments = []
        
        # Първият сегмент е от началото на периода
        current_start = period_start
        
        # Търсим анексите за този договор в периода
        result = await self.db.execute(
            select(ContractAnnex).where(
                and_(
                    ContractAnnex.contract_id == contract_id,
                    ContractAnnex.effective_date <= period_end,
                    ContractAnnex.is_signed == True
                )
            ).order_by(ContractAnnex.effective_date)
        )
        annexes = result.scalars().all()
        
        # Добави основния договор като първи сегмент
        if self.employment_contract:
            base_salary = self.employment_contract.base_salary or Decimal('0')
            segments.append({
                'start_date': period_start,
                'end_date': period_end,
                'salary': base_salary,
                'source': 'contract',
                'annex_id': None
            })
        
        # Ако има анекси, разделяме периода
        for annex in annexes:
            if annex.effective_date > period_start:
                # Намери предишния сегмент и го скъси
                for seg in segments:
                    if seg['end_date'] == period_end and seg['start_date'] == period_start:
                        seg['end_date'] = annex.effective_date - timedelta(days=1)
                        break
                
                # Добави нов сегмент от датата на анекса
                new_salary = annex.base_salary if annex.base_salary else (
                    self.employment_contract.base_salary if self.employment_contract else Decimal('0')
                )
                
                # Намери крайната дата на този сегмент
                next_annex_date = period_end
                for next_annex in annexes:
                    if next_annex.effective_date > annex.effective_date:
                        next_annex_date = next_annex.effective_date - timedelta(days=1)
                        break
                
                segments.append({
                    'start_date': annex.effective_date,
                    'end_date': min(next_annex_date, period_end),
                    'salary': new_salary,
                    'source': 'annex',
                    'annex_id': annex.id
                })
        
        return segments
    
    async def calculate_pro_rata_salary(self) -> dict:
        """
        Изчислява пропорционалната заплата за периода.
        Ако има промени в договора (анекси) през периода,
        разделяме периода на сегменти и изчисляваме пропорционално.
        """
        if not self.employment_contract:
            return {
                'base_salary': 0,
                'pro_rata_salary': 0,
                'segments': [],
                'has_changes': False
            }
        
        contract_id = self.employment_contract.id
        
        # Вземи всички сегменти за периода
        segments = await self.get_contract_segments_for_period(contract_id)
        
        if len(segments) <= 1:
            # Няма промени - връщаме стандартната заплата
            base_salary = self.employment_contract.base_salary or Decimal('0')
            return {
                'base_salary': float(base_salary),
                'pro_rata_salary': float(base_salary),
                'segments': segments,
                'has_changes': False
            }
        
        # Има промени - изчисляваме пропорционално
        period_start = self.calculation_period['start_date']
        period_end = self.calculation_period['end_date']
        total_days = (period_end - period_start).days + 1
        
        pro_rata_total = Decimal('0')
        
        for seg in segments:
            seg_start = seg['start_date']
            seg_end = seg['end_date']
            seg_days = (seg_end - seg_start).days + 1
            
            # Пропорционална заплата за сегмента
            seg_salary = Decimal(str(seg['salary'])) * Decimal(str(seg_days)) / Decimal(str(total_days))
            pro_rata_total += seg_salary
            
            seg['pro_rata_amount'] = float(seg_salary)
            seg['days'] = seg_days
        
        return {
            'base_salary': float(self.employment_contract.base_salary or Decimal('0')),
            'pro_rata_salary': float(pro_rata_total),
            'segments': segments,
            'has_changes': True
        }
    
    # --- Отпуски и болнични (Фаза 5) ---
    
    async def calculate_maternity_leave(
        self, 
        leave_request: "LeaveRequest"
    ) -> dict:
        """
        Изчислява обезщетението за майчинство (чл. 163 КТ).
        410 дни - 135 дни преди раждане, 275 дни след раждане.
        Обезщетение: 90% от среднодневния брутен осигурителен доход.
        """
        from backend import crud
        
        maternity_days_str = await crud.get_global_setting(self.db, "payroll_maternity_days")
        maternity_days = int(maternity_days_str) if maternity_days_str else 410
        
        # Изчисли среднодневния брутен осигурителен доход
        daily_gross = await self._get_daily_gross_salary()
        if not daily_gross:
            return {
                'total_days': maternity_days,
                'daily_amount': 0,
                'total_amount': 0,
                'type': 'maternity'
            }
        
        # 90% от среднодневния доход
        daily_amount = daily_gross * Decimal("0.90")
        total_amount = daily_amount * Decimal(str(maternity_days))
        
        return {
            'total_days': maternity_days,
            'daily_amount': float(daily_amount),
            'total_amount': float(total_amount),
            'type': 'maternity',
            'start_date': leave_request.start_date if leave_request else None,
            'end_date': leave_request.end_date if leave_request else None
        }
    
    async def calculate_paternity_leave(
        self, 
        leave_request: "LeaveRequest"
    ) -> dict:
        """
        Изчислява обезщетението за бащинство.
        15 дни - платени от работодателя.
        """
        from backend import crud
        
        paternity_days_str = await crud.get_global_setting(self.db, "payroll_paternity_days")
        paternity_days = int(paternity_days_str) if paternity_days_str else 15
        
        # Бащинството е 100% платено от работодателя
        daily_gross = await self._get_daily_gross_salary()
        if not daily_gross:
            return {
                'total_days': paternity_days,
                'daily_amount': 0,
                'total_amount': 0,
                'type': 'paternity'
            }
        
        total_amount = daily_gross * Decimal(str(paternity_days))
        
        return {
            'total_days': paternity_days,
            'daily_amount': float(daily_gross),
            'total_amount': float(total_amount),
            'type': 'paternity',
            'employer_paid': True
        }
    
    async def calculate_leave_details(
        self, 
        leave_requests: List["LeaveRequest"]
    ) -> dict:
        """
        Изчислява всички отпуски за периода.
        """
        annual_leave = Decimal("0")
        sick_leave = Decimal("0")
        maternity_leave = Decimal("0")
        paternity_leave = Decimal("0")
        unpaid_leave = Decimal("0")
        
        annual_days = 0
        sick_days = 0
        
        for leave in leave_requests:
            if leave.leave_type == "annual_paid":
                # Заплаща се от работодателя
                annual_days += (leave.end_date - leave.start_date).days + 1
                
            elif leave.leave_type == "sick":
                sick_days += (leave.end_date - leave.start_date).days + 1
                payment = await self._calculate_single_sick_leave_payment(
                    SickLeaveRecord(
                        start_date=leave.start_date,
                        end_date=leave.end_date,
                        sick_leave_type="general",
                        total_days=(leave.end_date - leave.start_date).days + 1
                    )
                )
                sick_leave += payment
                
            elif leave.leave_type == "maternity":
                details = await self.calculate_maternity_leave(leave)
                maternity_leave += Decimal(str(details['total_amount']))
                
            elif leave.leave_type == "paternity":
                details = await self.calculate_paternity_leave(leave)
                paternity_leave += Decimal(str(details['total_amount']))
                
            elif leave.leave_type == "unpaid":
                unpaid_days = (leave.end_date - leave.start_date).days + 1
                unpaid_leave += Decimal(str(unpaid_days)) * (await self._get_daily_gross_salary() or Decimal("0"))
        
        return {
            'annual_leave_days': annual_days,
            'annual_leave_amount': float(annual_leave),
            'sick_leave_days': sick_days,
            'sick_leave_amount': float(sick_leave),
            'maternity_leave_amount': float(maternity_leave),
            'paternity_leave_amount': float(paternity_leave),
            'unpaid_leave_days': unpaid_leave,
            'total_leave_amount': float(
                annual_leave + sick_leave + maternity_leave + paternity_leave
            )
        }