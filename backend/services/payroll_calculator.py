import calendar
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import date
from decimal import Decimal
from datetime import datetime
import calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.models import TimeLog, Payroll, Payslip, sofia_now, MonthlyWorkDays, Bonus


def _get_crud():
    """Lazy import to avoid circular import"""
    from backend import crud
    return crud

def get_standard_working_days(year: int, month: int) -> List[date]:
    """Връща списък от всички делнични дни (Пон-Пет) в месеца."""
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, d) for d in range(1, num_days + 1) if date(year, month, d).weekday() < 5]

class PayrollCalculator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._working_days_cache = {} # (user_id, year, month) -> total_days

    async def get_total_working_days_for_month(self, user_id: int, year: int, month: int) -> int:
        cache_key = (user_id, year, month)
        if cache_key in self._working_days_cache:
            return self._working_days_cache[cache_key]
        
        # 0. Check for Manual Override in MonthlyWorkDays
        res = await self.db.execute(
            select(MonthlyWorkDays)
            .where(MonthlyWorkDays.year == year)
            .where(MonthlyWorkDays.month == month)
        )
        override = res.scalars().first()
        if override:
            self._working_days_cache[cache_key] = override.days_count
            return override.days_count

        # 1. Fetch Holidays for this month
        from backend.database.models import PublicHoliday
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        
        hol_result = await self.db.execute(
            select(PublicHoliday.date)
            .where(PublicHoliday.date >= month_start)
            .where(PublicHoliday.date <= month_end)
        )
        holidays_set = {row[0] for r in hol_result.all() for row in [r]}

        # 2. Get User Schedule (Weekends worked)
        from backend.database.models import WorkSchedule
        sched_result = await self.db.execute(
            select(WorkSchedule.date)
            .where(WorkSchedule.user_id == user_id)
            .where(WorkSchedule.date >= month_start)
            .where(WorkSchedule.date <= month_end)
        )
        scheduled_dates = {row[0] for r in sched_result.all() for row in [r]}
        
        total_days = 0
        num_days = calendar.monthrange(year, month)[1]
        
        # Logic for Rate Calculation:
        # Return strict business days (Mon-Fri minus Holidays).
        
        total_business_days = 0
        for d in range(1, num_days + 1):
            curr_date = date(year, month, d)
            if curr_date.weekday() < 5 and curr_date not in holidays_set:
                total_business_days += 1
                
        self._working_days_cache[cache_key] = total_business_days
        return total_business_days

    async def calculate(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Calculates the payroll for a user within a given period using Interval Logic and Smart Break Deduction.
        """
        crud = _get_crud()
        
        # 1. Get Payroll Config
        config = await crud.get_payroll_config(self.db, user_id)
        if not config:
            # Provide default values if no config found to prevent crashing
            from types import SimpleNamespace
            config = SimpleNamespace(
                hourly_rate=0.0,
                monthly_salary=0.0,
                overtime_multiplier=1,
                standard_hours_per_day=8,
                currency="EUR"
            )

        # 2. Get TimeLogs and Schedules
        logs = await crud.get_timelogs_by_user_and_period(self.db, user_id, start_date, end_date)
        
        # Robust handling of both date and datetime
        sd_date = start_date if isinstance(start_date, date) else start_date.date()
        ed_date = end_date if isinstance(end_date, date) else end_date.date()
        
        schedules = await crud.get_user_schedules(self.db, user_id, sd_date, ed_date)
        schedule_map = {s.date: s for s in schedules}

        logs_by_day: Dict[date, List[TimeLog]] = {}
        for log in logs:
            if not log.end_time: continue 
            day = log.start_time.date()
            if day not in logs_by_day: logs_by_day[day] = []
            logs_by_day[day].append(log)

        total_reg_hours = 0.0
        total_ot_hours = 0.0
        regular_amount = 0.0
        overtime_amount = 0.0
        
        sick_days_count = 0
        leave_days_count = 0
        
        # Iterate over all relevant dates
        all_dates = set(logs_by_day.keys()) | set(schedule_map.keys())
        sorted_dates = sorted(list(all_dates))

        from backend.database.models import ShiftType

        for day in sorted_dates:
            day_logs = logs_by_day.get(day, [])
            
            # --- Determine Shift Window ---
            shift_start_dt = None
            shift_end_dt = None
            shift_type = ShiftType.REGULAR.value
            multiplier = 1.0
            break_hours = 0.0
            daily_standard = float(config.standard_hours_per_day) if config.standard_hours_per_day else 8.0

            if day in schedule_map and schedule_map[day].shift:
                s = schedule_map[day].shift
                shift_type = s.shift_type
                multiplier = float(s.pay_multiplier) if s.pay_multiplier is not None else 1.0
                break_hours = (s.break_duration_minutes or 0) / 60.0
                
                # Construct shift timestamps
                shift_start_dt = datetime.combine(day, s.start_time)
                shift_end_dt = datetime.combine(day, s.end_time)
                if shift_end_dt < shift_start_dt:
                    shift_end_dt += timedelta(days=1)
                
                # Recalculate daily standard based on shift definition (Net work hours)
                raw_shift_duration = (shift_end_dt - shift_start_dt).total_seconds() / 3600.0
                daily_standard = max(0, raw_shift_duration - break_hours)

            # --- Special Shift Types (Leaves) ---
            if shift_type == ShiftType.SICK_LEAVE.value:
                sick_days_count += 1
                shift_start_dt = None 
                shift_end_dt = None
            elif shift_type == ShiftType.UNPAID_LEAVE.value:
                shift_start_dt = None 
                shift_end_dt = None
            elif shift_type in [ShiftType.PAID_LEAVE.value, ShiftType.DAY_OFF.value]:
                 if shift_type == ShiftType.PAID_LEAVE.value:
                     leave_days_count += 1
                 # Treated as full day for base pay, work is OT
                 pass
            
            # --- Interval Calculation ---
            daily_raw_overlap = 0.0 # Hours INSIDE shift
            daily_pure_ot = 0.0     # Hours OUTSIDE shift
            
            # Auto-fill for Paid Leave if NO logs
            if shift_type == ShiftType.PAID_LEAVE.value and not day_logs:
                daily_raw_overlap = daily_standard # We assume standard fulfilled
            
            for log in day_logs:
                l_start = log.start_time
                l_end = log.end_time
                
                duration = (l_end - l_start).total_seconds() / 3600.0
                manual_break = (getattr(log, 'break_duration_minutes', 0) or 0) / 60.0
                effective_duration = max(0, duration - manual_break)
                
                if shift_start_dt and shift_end_dt and shift_type == ShiftType.REGULAR.value:
                    # Calculate Intersection
                    overlap_start = max(l_start, shift_start_dt)
                    overlap_end = min(l_end, shift_end_dt)
                    
                    if overlap_end > overlap_start:
                        overlap_seconds = (overlap_end - overlap_start).total_seconds()
                        overlap_hours = overlap_seconds / 3600.0
                        
                        # We attribute manual break to regular time first
                        reg_part = max(0, overlap_hours - manual_break)
                        ot_part = max(0, effective_duration - reg_part)
                        
                        daily_raw_overlap += reg_part
                        daily_pure_ot += ot_part
                    else:
                        # No overlap -> All OT
                        daily_pure_ot += effective_duration
                else:
                    # No active working shift (or Leave with work) -> All is OT
                    daily_pure_ot += effective_duration

            # --- Smart Break Deduction (The User's Logic) ---
            final_daily_reg = daily_raw_overlap
            
            if shift_type == ShiftType.REGULAR.value and break_hours > 0 and day_logs:
                # 1. Calculate Total Span (First In to Last Out)
                first_in = min(l.start_time for l in day_logs)
                last_out = max(l.end_time for l in day_logs)
                total_span_hours = (last_out - first_in).total_seconds() / 3600.0
                
                # 2. Calculate Actual Work Sum (Net of manual breaks stored in DB)
                total_worked_net = sum([
                    max(0, ((l.end_time - l.start_time).total_seconds()/3600.0) - ((getattr(l, 'break_duration_minutes', 0) or 0)/60.0))
                    for l in day_logs
                ])
                
                # 3. Check for Mandatory Break Deduction
                gap_taken = max(0, total_span_hours - total_worked_net)
                
                if gap_taken < 0.1: 
                     if total_worked_net > 4.0:
                         deduction = min(final_daily_reg, break_hours)
                         final_daily_reg -= deduction
                else:
                    missing_break = max(0, break_hours - gap_taken)
                    deduction = min(final_daily_reg, missing_break)
                    final_daily_reg -= deduction

            # Finalize Totals
            total_reg_hours += final_daily_reg
            total_ot_hours += daily_pure_ot

            # --- Financial Calculation for Day ---
            working_days_count = await self.get_total_working_days_for_month(user_id, day.year, day.month)
            monthly_salary = float(config.monthly_salary) if config.monthly_salary else 0.0
            hourly_rate = float(config.hourly_rate) if config.hourly_rate else 0.0
            
            day_pay = 0.0
            
            # Regular Pay
            if working_days_count > 0 and monthly_salary > 0:
                daily_rate = monthly_salary / working_days_count
                if daily_standard > 0:
                    fraction = min(1.0, final_daily_reg / daily_standard)
                    day_pay = daily_rate * fraction
            elif hourly_rate > 0:
                 day_pay = final_daily_reg * hourly_rate
            
            day_pay *= multiplier
            regular_amount += day_pay
            
            # Overtime Pay
            ot_mult = float(config.overtime_multiplier) if config.overtime_multiplier else 1
            overtime_amount += daily_pure_ot * hourly_rate * ot_mult

        # --- 3. Calculate Bonuses ---
        # Fetch bonuses that fall within the requested period
        bonus_result = await self.db.execute(
            select(Bonus)
            .where(Bonus.user_id == user_id)
            .where(Bonus.date >= sd_date)
            .where(Bonus.date <= ed_date)
        )
        bonuses = bonus_result.scalars().all()
        bonus_amount = sum(float(b.amount) for b in bonuses)

        gross_salary = regular_amount + overtime_amount + bonus_amount
        
        # --- 4. Deductions (Tax & Health) ---
        tax_pct = float(config.tax_percent) if hasattr(config, 'tax_percent') and config.tax_percent is not None else 10.0
        health_pct = float(config.health_insurance_percent) if hasattr(config, 'health_insurance_percent') and config.health_insurance_percent is not None else 13.78
        
        has_tax = getattr(config, 'has_tax_deduction', True)
        has_health = getattr(config, 'has_health_insurance', True)
        
        deductions = 0.0
        
        # 4.1 Health Insurance (Deducted from Gross)
        health_amount = 0.0
        if has_health:
            health_amount = gross_salary * (health_pct / 100.0)
            deductions += health_amount
            
        # 4.2 Taxable Base = Gross - Health Insurance
        taxable_base = max(0.0, gross_salary - health_amount)
        
        # 4.3 Income Tax (Deducted from Taxable Base)
        tax_amount = 0.0
        if has_tax:
            tax_amount = taxable_base * (tax_pct / 100.0)
            deductions += tax_amount
            
        net_salary = gross_salary - deductions

        return {
            "user_id": user_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_regular_hours": round(total_reg_hours, 2),
            "total_overtime_hours": round(total_ot_hours, 2),
            "regular_amount": round(regular_amount, 2),
            "overtime_amount": round(overtime_amount, 2),
            "bonus_amount": round(bonus_amount, 2),
            "tax_amount": round(tax_amount, 2),
            "insurance_amount": round(health_amount, 2),
            "sick_days": sick_days_count,
            "leave_days": leave_days_count,
            "total_amount": round(net_salary, 2),
            "hourly_rate": float(config.hourly_rate) if config.hourly_rate else 0.0
        }

    async def generate_and_save_payslip(self, user_id: int, start_date: datetime, end_date: datetime) -> Payslip:
        """
        Calculates payroll and saves it as a Payslip record.
        """
        result = await self.calculate(user_id, start_date, end_date)
        
        payslip_data = {
            "user_id": result["user_id"],
            "period_start": result["period_start"],
            "period_end": result["period_end"],
            "total_regular_hours": result["total_regular_hours"],
            "total_overtime_hours": result["total_overtime_hours"],
            "regular_amount": result["regular_amount"],
            "overtime_amount": result["overtime_amount"],
            "bonus_amount": result["bonus_amount"],
            "tax_amount": result["tax_amount"],
            "insurance_amount": result["insurance_amount"],
            "sick_days": result["sick_days"],
            "leave_days": result["leave_days"],
            "total_amount": result["total_amount"],
            "generated_at": sofia_now()
        }
        
        payslip = await crud.create_payslip(self.db, payslip_data)
        return payslip

    async def get_weekly_summary(self, user_id: int, ref_date: date, target_weekly_hours: float = 40.0) -> Dict[str, Any]:
        """
        Calculates Net Balance (Overtime - Debt) in real-time based on Schedule vs Actual Logs.
        """
        crud = _get_crud()
        start_of_week = ref_date - timedelta(days=ref_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        now = sofia_now()
        now_date = now.date()
        
        # 1. Get Actual Worked Hours (Logs)
        # We fetch logs for the whole week
        start_dt = datetime.combine(start_of_week, time.min)
        end_dt = datetime.combine(end_of_week, time.max)
        
        # Use calculate() to get precise worked hours (handling breaks, multiple logs, etc.)
        stats = await self.calculate(user_id, start_dt, end_dt)
        actual_reg_hours = float(stats["total_regular_hours"])
        actual_ot_hours = float(stats["total_overtime_hours"])
        total_worked_hours = actual_reg_hours + actual_ot_hours

        # 2. Calculate Expected (Target) Hours up to NOW based on Schedule
        expected_hours_so_far = 0.0
        
        schedules = await crud.get_user_schedules(self.db, user_id, start_of_week, end_of_week)
        sched_map = {s.date: s for s in schedules}
        
        loop_date = start_of_week
        
        # Iterate only until today (inclusive)
        while loop_date <= end_of_week and loop_date <= now_date:
            schedule = sched_map.get(loop_date)
            daily_expected = 0.0
            
            if schedule and schedule.shift and schedule.shift.shift_type == 'regular':
                # Parse shift times
                s_start = datetime.combine(loop_date, schedule.shift.start_time)
                s_end = datetime.combine(loop_date, schedule.shift.end_time)
                if s_end < s_start: s_end += timedelta(days=1) # Overnight shift
                
                break_dur_hours = (schedule.shift.break_duration_minutes or 0) / 60.0
                full_shift_hours = (s_end - s_start).total_seconds() / 3600.0
                net_shift_hours = max(0, full_shift_hours - break_dur_hours)
                
                if loop_date < now_date:
                    # Past day: Expect full shift
                    daily_expected = net_shift_hours
                elif loop_date == now_date:
                    # Today: Calculate elapsed expectation
                    if now >= s_end.replace(tzinfo=now.tzinfo):
                         daily_expected = net_shift_hours
                    elif now > s_start.replace(tzinfo=now.tzinfo):
                        elapsed = (now.replace(tzinfo=None) - s_start).total_seconds() / 3600.0
                        daily_expected = max(0, elapsed)
                        if daily_expected > net_shift_hours:
                            daily_expected = net_shift_hours
            
            expected_hours_so_far += daily_expected
            loop_date += timedelta(days=1)

        # 3. Calculate Net Balance
        # Balance = Actual Regular - Expected
        # (Overtime is handled separately as surplus)
        
        balance = total_worked_hours - expected_hours_so_far
        
        debt = 0.0
        surplus = 0.0
        status_message = ""
        
        if balance < -0.02:
            debt = abs(balance)
            h = int(debt)
            m = int((debt - h) * 60)
            status_message = f"Дължите {h}ч {m}м"
        elif balance > 0.02:
            surplus = balance
            h = int(surplus)
            m = int((surplus - h) * 60)
            status_message = f"Извънредни: {h}ч {m}м"
        else:
            status_message = "Графикът е изпълнен точно"

        return {
            "start_date": start_of_week,
            "end_date": end_of_week,
            "total_regular_hours": actual_reg_hours, 
            "total_overtime_hours": actual_ot_hours, # Real OT from logs
            "target_hours": expected_hours_so_far,
            "debt_hours": debt,
            "surplus_hours": surplus, # This is the Net Balance
            "status_message": status_message
        }

    async def get_daily_stats(self, user_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        crud = _get_crud()
        stats_list = []
        loop_date = start_date
        while loop_date <= end_date:
            start_dt = datetime.combine(loop_date, time.min)
            end_dt = datetime.combine(loop_date, time.max)
            
            day_stats = await self.calculate(user_id, start_dt, end_dt)
            
            # Get Logs for this day to find arrival/departure
            logs = await crud.get_timelogs_by_user_and_period(self.db, user_id, start_dt, end_dt)
            arrival = None
            departure = None
            if logs:
                sorted_logs = sorted(logs, key=lambda l: l.start_time)
                arrival = sorted_logs[0].start_time
                # Only show departure if last log is closed
                if sorted_logs[-1].end_time:
                    departure = sorted_logs[-1].end_time

            # Get Shift Name for UI
            schedules = await crud.get_user_schedules(self.db, user_id, loop_date, loop_date)
            shift_name = None
            if schedules and schedules[0].shift:
                shift_name = schedules[0].shift.name

            stats_list.append({
                "date": loop_date,
                "total_worked_hours": day_stats["total_regular_hours"] + day_stats["total_overtime_hours"],
                "regular_hours": day_stats["total_regular_hours"],
                "overtime_hours": day_stats["total_overtime_hours"],
                "is_work_day": day_stats["total_regular_hours"] > 0 or day_stats["total_overtime_hours"] > 0,
                "shift_name": shift_name,
                "actual_arrival": arrival,
                "actual_departure": departure
            })
            loop_date += timedelta(days=1)
            
        return stats_list

    async def calculate_forecast(self, user_id: int, year: int, month: int) -> float:
        """
        Calculates forecasted NET salary for a user for a specific month.
        Combines actual data (past) + scheduled data (future).
        """
        start_date = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        now = sofia_now()
        
        # 1. Past Data (Actual)
        # Calculate up to yesterday or now
        calc_end = min(end_date, now)
        if calc_end < start_date:
             # Future month
             calc_end = start_date # Effectively no actuals
             actual_stats = {
                 "regular_amount": 0.0, "overtime_amount": 0.0, "bonus_amount": 0.0
             }
        else:
            actual_stats = await self.calculate(user_id, start_date, calc_end)
        
        forecast_regular_pay = actual_stats["regular_amount"]
        forecast_ot_pay = actual_stats["overtime_amount"]
        
        # 2. Future Data (Scheduled)
        if end_date > now:
            future_start = max(start_date, now + timedelta(seconds=1))
            # Just look at schedule, assume perfect attendance
            fs_date = future_start if isinstance(future_start, date) else future_start.date()
            ed_date_forecast = end_date if isinstance(end_date, date) else end_date.date()
            schedules = await crud.get_user_schedules(self.db, user_id, fs_date, ed_date_forecast)
            config = await crud.get_payroll_config(self.db, user_id)
            
            # Basic defaults
            hourly_rate = float(config.hourly_rate) if config and config.hourly_rate else 0.0
            monthly_salary = float(config.monthly_salary) if config and config.monthly_salary else 0.0
            work_days = await self.get_total_working_days_for_month(user_id, year, month)
            daily_rate = (monthly_salary / work_days) if work_days and monthly_salary else 0.0
            
            from backend.database.models import ShiftType

            for sched in schedules:
                if not sched.shift: continue
                
                # Check for Leave
                if sched.shift.shift_type == ShiftType.PAID_LEAVE.value:
                    # Paid leave counts as worked for salary
                    if monthly_salary > 0: forecast_regular_pay += daily_rate
                    elif hourly_rate > 0: forecast_regular_pay += (8 * hourly_rate) # Assume 8h
                
                elif sched.shift.shift_type == ShiftType.REGULAR.value:
                    # Regular Shift
                    # Calculate net hours
                    s_start = datetime.combine(sched.date, sched.shift.start_time)
                    s_end = datetime.combine(sched.date, sched.shift.end_time)
                    if s_end < s_start: s_end += timedelta(days=1)
                    
                    break_h = (sched.shift.break_duration_minutes or 0) / 60.0
                    duration = (s_end - s_start).total_seconds() / 3600.0
                    net_h = max(0, duration - break_h)
                    
                    if monthly_salary > 0:
                        # Fraction of day if needed, or full day
                        # Simplification: Full day pay if hours match standard
                        forecast_regular_pay += daily_rate
                    elif hourly_rate > 0:
                        forecast_regular_pay += (net_h * hourly_rate)

        # 3. Finalize
        # Add future bonuses if we want? For now, just actuals.
        gross = forecast_regular_pay + forecast_ot_pay + actual_stats["bonus_amount"]
        
        # Deductions (re-using logic)
        config = await crud.get_payroll_config(self.db, user_id)
        if not config: return 0.0

        tax_pct = float(config.tax_percent) if config.tax_percent is not None else 10.0
        health_pct = float(config.health_insurance_percent) if config.health_insurance_percent is not None else 13.78
        
        deductions = 0.0
        if getattr(config, 'has_health_insurance', True):
            deductions += gross * (health_pct / 100.0)
        
        taxable = max(0.0, gross - (gross * (health_pct / 100.0) if getattr(config, 'has_health_insurance', True) else 0))
        
        if getattr(config, 'has_tax_deduction', True):
            deductions += taxable * (tax_pct / 100.0)
            
        return round(gross - deductions, 2)

        
                    
        
        