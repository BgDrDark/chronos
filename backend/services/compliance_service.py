from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import WorkSchedule, Shift, User
from backend import crud

class ComplianceService:
    """
    Сървис за съответствие с Трудовото законодателство на РБ (Кодекс на труда).
    Валидира работни графици и смени.
    """

    @staticmethod
    async def is_strict_mode_enabled(db: AsyncSession) -> bool:
        """Проверява дали е активиран строгият режим на съответствие."""
        strict_mode = await crud.get_global_setting(db, "trz_compliance_strict_mode")
        return strict_mode.lower() == "true" if strict_mode else False

    @classmethod
    async def validate_schedule_change(
        cls, db: AsyncSession, user_id: int, target_date: date, shift_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Валидира нова смяна или промяна в графика спрямо КТ.
        Връща (is_valid, error_message).
        """
        if not await cls.is_strict_mode_enabled(db):
            return True, None

        # 1. Извличаме новата смяна и околните смени на служителя
        new_shift = await db.get(Shift, shift_id)
        if not new_shift:
            return False, "Невалидна смяна"

        # Взимаме смените за предходния и следващия ден
        prev_date = target_date - timedelta(days=1)
        next_date = target_date + timedelta(days=1)

        stmt = select(WorkSchedule).where(
            and_(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date.in_([prev_date, next_date])
            )
        )
        res = await db.execute(stmt)
        surrounding_schedules = res.scalars().all()
        
        prev_schedule = next((s for s in surrounding_schedules if s.date == prev_date), None)
        next_schedule = next((s for s in surrounding_schedules if s.date == next_date), None)

        # ПРОВЕРКА 1: Междудневна почивка (чл. 152 КТ - мин. 12 часа)
        if prev_schedule:
            prev_shift = await db.get(Shift, prev_schedule.shift_id)
            if prev_shift:
                # Време от края на вчерашната до началото на днешната
                # (Ако вчерашната свършва в 22:00, а днешната почва в 06:00 = 8ч < 12ч)
                # Изчисляваме интервала
                rest_hours = cls._calculate_rest_between_shifts(prev_shift, new_shift, days_gap=1)
                if rest_hours < 12:
                    return False, f"Нарушение на чл. 152 КТ: Междудневната почивка е {rest_hours}ч (минимум 12ч)."

        if next_schedule:
            next_shift = await db.get(Shift, next_schedule.shift_id)
            if next_shift:
                rest_hours = cls._calculate_rest_between_shifts(new_shift, next_shift, days_gap=1)
                if rest_hours < 12:
                    return False, f"Нарушение на чл. 152 КТ: Междудневната почивка към следващия ден е {rest_hours}ч (минимум 12ч)."

        # ПРОВЕРКА 2: Седмична почивка (чл. 153 КТ - мин. 48 часа)
        # Тази проверка е по-сложна - изисква преглед на целия седмичен цикъл
        is_weekly_ok, weekly_msg = await cls._check_weekly_rest(db, user_id, target_date, new_shift)
        if not is_weekly_ok:
            return False, weekly_msg

        return True, None

    @staticmethod
    def _calculate_rest_between_shifts(first_shift: Shift, second_shift: Shift, days_gap: int) -> float:
        """Изчислява часовете почивка между края на първата и началото на втората смяна."""
        # Моделираме времената
        # first_shift.end_time (Day 0) -> second_shift.start_time (Day 1)
        
        # За опростяване приемаме, че смените са в рамките на едно денонощие
        # Ако смяната е нощна и свършва на следващия ден, трябва да се съобрази
        
        start_dt = datetime.combine(date.today(), first_shift.end_time)
        end_dt = datetime.combine(date.today() + timedelta(days=days_gap), second_shift.start_time)
        
        # Ако първата смяна свършва след като е почнала (нощна смяна в същия ден)
        if first_shift.end_time < first_shift.start_time:
            # Смяната е преминала в следващия ден
            start_dt += timedelta(days=1)
            
        diff = end_dt - start_dt
        return diff.total_seconds() / 3600

    @classmethod
    async def _check_weekly_rest(cls, db: AsyncSession, user_id: int, target_date: date, new_shift: Shift) -> Tuple[bool, Optional[str]]:
        """Проверява за наличие на 48-часова седмична почивка."""
        # Намираме началото и края на седмицата (Понеделник - Неделя)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        stmt = select(WorkSchedule).where(
            and_(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date >= start_of_week,
                WorkSchedule.date <= end_of_week
            )
        ).order_by(WorkSchedule.date)
        
        res = await db.execute(stmt)
        schedules = {s.date: s for s in res.scalars().all()}
        schedules[target_date] = WorkSchedule(date=target_date, shift_id=new_shift.id) # Симулираме новата смяна
        
        # Търсим най-големия интервал без работа в седмицата
        # (За опростен анализ проверяваме дали има поне 2 последователни дни без смени)
        # В България при 5-дневна седмица почивката е 48ч, при сумирано изчисляване - 36ч.
        
        consecutive_free_days = 0
        max_free_days = 0
        
        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            if current_day not in schedules:
                consecutive_free_days += 1
            else:
                max_free_days = max(max_free_days, consecutive_free_days)
                consecutive_free_days = 0
        
        max_free_days = max(max_free_days, consecutive_free_days)
        
        if max_free_days < 2:
            # Ако няма 2 цели почивни дни, проверяваме реалните часове между последната смяна и следващата
            # Тук може да се добави по-прецизна логика за 48 часа.
            # За целите на Фаза 2 ще сигнализираме, ако липсва уикенд или 2 дни почивка.
            return False, "Нарушение на чл. 153 КТ: Липсва 48-часова седмична почивка (2 последователни почивни дни)."
            
        return True, None
