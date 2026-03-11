"""
Калкулатор за нощен труд
"""
from datetime import time, date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any


class NightWorkCalculator:
    """
    Калкулатор за изчисляване на нощен труд спред българското законодателство.
    
    Нощен труд е трудът, положен между 22:00 и 06:00 часа.
    За нощен труд се полага 50% надбавка към основната заплата.
    """
    
    NIGHT_START = time(22, 0)  # 22:00
    NIGHT_END = time(6, 0)    # 06:00
    
    DEFAULT_NIGHT_RATE = Decimal("0.5")  # 50% надбавка
    
    def calculate_night_hours(self, start_time: time, end_time: time) -> float:
        """
        Изчислява броя нощни часове между две времена.
        
        Args:
            start_time: Начално време
            end_time: Крайно време
            
        Returns:
            Брой нощни часове
        """
        if start_time == end_time:
            return 0.0
            
        # Ако началният час е преди полунощ
        if start_time >= self.NIGHT_START:
            # Цялата смяна е нощна ако започва след 22:00
            if end_time <= time(23, 59):
                # През нощта до края на деня
                end_dt = datetime.combine(date.today(), end_time)
                start_dt = datetime.combine(date.today(), start_time)
                night_hours = (end_dt - start_dt).seconds / 3600
                return float(night_hours)
            else:
                # През нощта и след полунощ
                # До полунощ
                midnight = datetime.combine(date.today() + timedelta(days=1), time(0, 0))
                start_dt = datetime.combine(date.today(), start_time)
                first_part = (midnight - start_dt).seconds / 3600
                
                # След полунощ до 06:00
                if end_time <= self.NIGHT_END:
                    second_part = datetime.combine(date.today() + timedelta(days=1), end_time) - midnight
                    return float(first_part + second_part.seconds / 3600)
                else:
                    # След 06:00 - само до 06:00
                    morning_end = datetime.combine(date.today() + timedelta(days=1), self.NIGHT_END)
                    second_part = (morning_end - midnight).seconds / 3600
                    return float(first_part + second_part)
        
        # Ако началният час е след полунощ (нощна смяна)
        if start_time < self.NIGHT_END and end_time <= self.NIGHT_END:
            end_dt = datetime.combine(date.today(), end_time)
            start_dt = datetime.combine(date.today(), start_time)
            return float((end_dt - start_dt).seconds / 3600)
        
        # Ако началният час е преди 06:00 но крайният е след 06:00
        if start_time < self.NIGHT_END and end_time > self.NIGHT_END:
            # До 06:00
            morning_end = datetime.combine(date.today(), self.NIGHT_END)
            start_dt = datetime.combine(date.today(), start_time)
            return float((morning_end - start_dt).seconds / 3600)
        
        return 0.0
    
    def calculate_night_hours_simple(self, shift_start: time, shift_end: time) -> float:
        """
        Опростен метод за изчисляване на нощни часове.
        
        Args:
            shift_start: Начало на смяната
            shift_end: Край на смяната
            
        Returns:
            Брой нощни часове
        """
        night_hours = 0.0
        
        # Проверяваме всеки час от смяната
        current = shift_start
        while current < shift_end:
            # Проверяваме дали текущия час е в нощния период
            if current >= self.NIGHT_START or current < self.NIGHT_END:
                night_hours += 1
            # Минаваме на следващия час
            hour = current.hour + 1
            if hour >= 24:
                hour = 0
            current = time(hour, 0)
        
        return night_hours
    
    def calculate_amount(
        self, 
        hours: Decimal, 
        hourly_rate: Decimal, 
        night_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява сумата за нощен труд.
        
        Args:
            hours: Брой часове
            hourly_rate: Почасова ставка
            night_rate: Процент надбавка (по подразбиране 50%)
            
        Returns:
            Сума за нощен труд
        """
        if night_rate is None:
            night_rate = self.DEFAULT_NIGHT_RATE
            
        # Сума = часове * ставка * (1 + надбавка)
        base_amount = hours * hourly_rate
        night_bonus = base_amount * night_rate
        
        return base_amount + night_bonus
    
    def calculate_from_shift(
        self,
        shift_start: time,
        shift_end: time,
        hourly_rate: Decimal,
        break_minutes: int = 0
    ) -> Dict[str, Any]:
        """
        Изчислява нощния труд от дадена смяна.
        
        Args:
            shift_start: Начало на смяната
            shift_end: Край на смяната
            hourly_rate: Почасова ставка
            break_minutes: Почивка в минути
            
        Returns:
            Речник с данни за нощния труд
        """
        # Изчисляваме общите часове
        if shift_start <= shift_end:
            shift_hours = (datetime.combine(date.today(), shift_end) - 
                          datetime.combine(date.today(), shift_start)).seconds / 3600
        else:
            # През полунощ
            shift_hours = ((datetime.combine(date.today() + timedelta(days=1), shift_end) - 
                          datetime.combine(date.today(), shift_start)).seconds) / 3600
        
        # Изваждаме почивката
        net_hours = shift_hours - (break_minutes / 60)
        
        # Изчисляваме нощните часове
        night_hours = self.calculate_night_hours(shift_start, shift_end)
        
        # Изчисляваме сумата
        amount = self.calculate_amount(Decimal(str(night_hours)), hourly_rate)
        
        return {
            "total_hours": Decimal(str(net_hours)),
            "night_hours": Decimal(str(night_hours)),
            "hourly_rate": hourly_rate,
            "amount": amount,
            "night_rate": self.DEFAULT_NIGHT_RATE
        }


class OvertimeCalculator:
    """
    Калкулатор за изчисляване на извънреден труд спред българското законодателство.
    
    Извънреден е трудът:
    - След 8 часа дневно (при 5-дневна работна седмица)
    - След 7.5 часа дневно (при 6-дневна работна седмица)
    - След 12 часа нощна смяна
    - По празнични дни
    
    Заплащане:
    - Първите 2 часа: 50% надбавка (множител 1.5)
    - Над 2 часа: 100% надбавка (множител 2.0)
    """
    
    DEFAULT_FIRST_2H_MULTIPLIER = Decimal("1.5")  # 50%
    DEFAULT_ADDITIONAL_MULTIPLIER = Decimal("2.0")  # 100%
    DEFAULT_HOLIDAY_MULTIPLIER = Decimal("2.0")   # 100%
    
    # Законови лимити
    MONTHLY_OVERTIME_LIMIT = 32  # часа месечно
    YEARLY_OVERTIME_LIMIT = 150  # часа годишно
    
    def is_overtime(
        self,
        daily_hours: float,
        standard_hours: float = 8.0
    ) -> bool:
        """
        Проверява дали дадените часове са извънредни.
        
        Args:
            daily_hours: Брой часове за деня
            standard_hours: Стандартен брой часове (по подразбиране 8)
            
        Returns:
            True ако има извънреден труд
        """
        return daily_hours > standard_hours
    
    def calculate_overtime_hours(
        self,
        total_hours: float,
        standard_hours: float = 8.0
    ) -> float:
        """
        Изчислява броя извънредни часове.
        
        Args:
            total_hours: Общ брой часове
            standard_hours: Стандартен брой часове
            
        Returns:
            Брой извънредни часове
        """
        overtime = total_hours - standard_hours
        return max(0, overtime)
    
    def calculate_with_multiplier(
        self,
        hours: Decimal,
        hourly_rate: Decimal,
        first_2h_multiplier: Optional[Decimal] = None,
        additional_multiplier: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява сумата за извънреден труд с различни множители.
        
        Първите 2 часа се плащат с 50% надбавка,
        а следващите - с 100% надбавка.
        
        Args:
            hours: Брой извънредни часове
            hourly_rate: Почасова ставка
            first_2h_multiplier: Множител за първите 2 часа
            additional_multiplier: Множител за над 2 часа
            
        Returns:
            Сума за извънреден труд
        """
        if first_2h_multiplier is None:
            first_2h_multiplier = self.DEFAULT_FIRST_2H_MULTIPLIER
        if additional_multiplier is None:
            additional_multiplier = self.DEFAULT_ADDITIONAL_MULTIPLIER
            
        # Разделяме часовете на първи 2 и останали
        first_2_hours = min(hours, Decimal("2"))
        additional_hours = max(Decimal("0"), hours - Decimal("2"))
        
        # Изчисляваме сумата
        first_amount = first_2_hours * hourly_rate * first_2h_multiplier
        additional_amount = additional_hours * hourly_rate * additional_multiplier
        
        return first_amount + additional_amount
    
    def calculate_holiday_overtime(
        self,
        hours: Decimal,
        hourly_rate: Decimal,
        multiplier: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява сумата за извънреден труд по празници.
        
        По закон, трудът по празнични дни се заплаща с 100% надбавка.
        
        Args:
            hours: Брой часове
            hourly_rate: Почасова ставка
            multiplier: Множител (по подразбиране 2.0)
            
        Returns:
            Сума за труд по празник
        """
        if multiplier is None:
            multiplier = self.DEFAULT_HOLIDAY_MULTIPLIER
            
        return hours * hourly_rate * multiplier
    
    def check_monthly_limit(self, current_overtime: float) -> float:
        """
        Проверява дали не е надхвърлен месечния лимит.
        
        Args:
            current_overtime: Текущ брой извънредни часове
            
        Returns:
            Брой часове, които могат да се ползват (в рамките на лимита)
        """
        return min(current_overtime, self.MONTHLY_OVERTIME_LIMIT)
    
    def calculate_from_daily_logs(
        self,
        daily_logs: List[Dict[str, Any]],
        standard_daily_hours: float = 8.0,
        hourly_rate: Decimal = Decimal("10.00")
    ) -> Dict[str, Any]:
        """
        Изчислява извънреден труд от дневни записи.
        
        Args:
            daily_logs: Списък с дневни записи (всеки съдържа 'hours' и 'date')
            standard_daily_hours: Стандартен дневен брой часове
            hourly_rate: Почасова ставка
            
        Returns:
            Речник с данни за извънредния труд
        """
        total_regular_hours = 0.0
        total_overtime_hours = 0.0
        total_amount = Decimal("0")
        
        for log in daily_logs:
            hours = float(log.get('hours', 0))
            total_regular_hours += min(hours, standard_daily_hours)
            
            overtime = self.calculate_overtime_hours(hours, standard_daily_hours)
            if overtime > 0:
                total_overtime_hours += overtime
                amount = self.calculate_with_multiplier(
                    Decimal(str(overtime)), 
                    hourly_rate
                )
                total_amount += amount
        
        return {
            "total_regular_hours": Decimal(str(total_regular_hours)),
            "total_overtime_hours": Decimal(str(total_overtime_hours)),
            "hourly_rate": hourly_rate,
            "total_amount": total_amount,
            "first_2h_multiplier": self.DEFAULT_FIRST_2H_MULTIPLIER,
            "additional_multiplier": self.DEFAULT_ADDITIONAL_MULTIPLIER
        }


class BusinessTripCalculator:
    """
    Калкулатор за командировки.
    """
    
    DEFAULT_DAILY_ALLOWANCE = Decimal("40.00")  # Дневни в лева
    REDUCTION_DAYS = 30  # След колко дни започва намаление
    
    def calculate_days(self, start_date: date, end_date: date) -> int:
        """
        Изчислява броя дни командировка.
        
        Args:
            start_date: Начална дата
            end_date: Крайна дата
            
        Returns:
            Брой дни
        """
        return (end_date - start_date).days + 1
    
    def calculate_daily_allowance(
        self,
        start_date: date,
        end_date: date,
        daily_rate: Decimal,
        reduction_after_days: Optional[int] = None,
        reduction_multiplier: Optional[Decimal] = None
    ) -> Decimal:
        """
        Изчислява дневните за командировка.
        
        Args:
            start_date: Начална дата
            end_date: Крайна дата
            daily_rate: Дневна ставка
            reduction_after_days: След колко дни започва намаление
            reduction_multiplier: Множител на намаление
            
        Returns:
            Обща сума за дневни
        """
        days = self.calculate_days(start_date, end_date)
        
        if reduction_after_days is None:
            reduction_after_days = self.REDUCTION_DAYS
        if reduction_multiplier is None:
            reduction_multiplier = Decimal("0.5")
            
        if days <= reduction_after_days:
            return Decimal(str(days)) * daily_rate
        else:
            # Първите X дни с пълна ставка
            first_period = Decimal(str(reduction_after_days)) * daily_rate
            # Останалите дни с намаление
            remaining_days = days - reduction_after_days
            second_period = Decimal(str(remaining_days)) * daily_rate * reduction_multiplier
            
            return first_period + second_period
    
    def calculate_total(
        self,
        destination: str,
        start_date: date,
        end_date: date,
        daily_allowance: Decimal,
        accommodation: Decimal = Decimal("0"),
        transport: Decimal = Decimal("0"),
        other_expenses: Decimal = Decimal("0")
    ) -> Decimal:
        """
        Изчислява общата стойност на командировка.
        
        Args:
            destination: Дестинация
            start_date: Начална дата
            end_date: Крайна дата
            daily_allowance: Дневни
            accommodation: Нощувки
            transport: Транспорт
            other_expenses: Други разходи
            
        Returns:
            Обща сума
        """
        daily = self.calculate_daily_allowance(start_date, end_date, daily_allowance)
        return daily + accommodation + transport + other_expenses
