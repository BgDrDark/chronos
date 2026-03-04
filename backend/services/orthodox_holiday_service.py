import datetime
from datetime import date, timedelta
from typing import List, Tuple


class OrthodoxHolidayService:
    """Service for calculating Bulgarian Orthodox holidays"""
    
    @staticmethod
    def easter_date(year: int) -> date:
        """
        Calculate Orthodox Easter (Pascha) using the Julian calendar algorithm.
        Returns the date of Orthodox Easter for a given year.
        """
        # Julian calendar calculation
        a = year % 4
        b = year % 7
        c = year % 19
        d = (19 * c + 15) % 30
        e = (2 * a + 4 * b - d + 28) % 7
        
        month = 3 + (d + e) / 28
        day = d + e - (d + e) / 28 * 28 + 1
        
        if month > 12:
            month -= 12
            year += 1
        
        # Orthodox Easter is calculated in Julian calendar, then converted
        # For simplicity, we return the approximate Gregorian date
        easter_julian = date(year, int(month), int(day))
        
        # The difference between Julian and Gregorian calendars
        # 1900-2099: 13 days, 1800-1899: 12 days, etc.
        century = year // 100
        correction = 10 - (century - 16) if century >= 16 else 0
        
        return easter_julian + timedelta(days=correction)
    
    @staticmethod
    def get_orthodox_holidays(year: int) -> List[Tuple[date, str, str, bool]]:
        """
        Get all Orthodox holidays for a given year.
        Returns list of (date, name, local_name, is_fixed)
        """
        holidays = []
        easter = OrthodoxHolidayService.easter_date(year)
        
        # Fixed Orthodox holidays (Julian calendar converted to Gregorian)
        # The Julian calendar is 13 days behind Gregorian in 1900-2099
        fixed_holidays = [
            (1, 1, "New Year", "Нова година", True),
            (1, 2, "St. Basil's Day", "Ден на Св. Васил", True),
            (1, 6, "Epiphany", "Богоявление", True),
            (1, 7, "St. John the Baptist", "Св. Йоан Кръстител", True),
            (1, 18, "St. Anthony the Great", "Св. Антон Велики", True),
            (1, 19, "St. Athanasius", "Св. Атанасий", True),
            (1, 20, "St. Euthymius", "Св. Евтимий", True),
            (1, 21, "St. Maximus", "Св. Максим", True),
            (2, 2, "Candlemas", "Сретение Господне", True),
            (2, 14, "St. Valentine", "Трифоновден", True),
            (3, 1, "Grandmother's Day", "Баба Марта", True),
            (3, 3, "St. Dimitri", "Св. Димитър", True),
            (3, 9, "St. 40 Martyrs", "Св. 40 мъченици", True),
            (3, 25, "Annunciation", "Благовещение", True),
            (4, 23, "St. George", "Гергьовден", True),
            (5, 6, "St. Dimitar", "Духовден", True),
            (5, 21, "St. Helena", "Св. Елена", True),
            (5, 25, "St. Sophia", "Св. София", True),
            (6, 24, "St. John the Baptist", "Еньовден", True),
            (7, 20, "St. Elias", "Илинден", True),
            (7, 27, "St. Pantaleon", "Св. Пантелеймон", True),
            (8, 15, "Assumption", "Успение на Св. Богородица", True),
            (8, 19, "St. Andrey", "Преображение Господне", True),
            (8, 28, "Dormition", "Успение на Св. Богородица", True),
            (9, 6, "St. Mother of God", "Св. Богородица", True),
            (9, 8, "Nativity of Mary", "Рождество на Св. Богородица", True),
            (9, 14, "Exaltation", "Въздвижение на Св. Кръст", True),
            (9, 21, "St. Matthew", "Св. Матей", True),
            (10, 6, "St. Thomas", "Св. Тома", True),
            (10, 22, "St. James", "Св. Яков", True),
            (11, 1, "All Saints' Day", "Покров на Св. Богородица", True),
            (11, 8, "St. Michael", "Св. Архангел", True),
            (11, 21, "Presentation", "Въведение Богородично", True),
            (12, 6, "St. Nicholas", "Никулден", True),
            (12, 20, "St. Ignatius", "Игнажден", True),
            (12, 24, "Christmas Eve", "Бъдни вечер", True),
            (12, 25, "Christmas", "Коледа", True),
            (12, 26, "St. Stephen", "Св. Стефан", True),
            (12, 27, "St. Georgi", "Св. Йордан", True),
            (12, 31, "St. Silvester", "Силвестровден", True),
        ]
        
        # Add fixed holidays
        for month, day, name, local_name, is_fixed in fixed_holidays:
            try:
                # Apply Julian to Gregorian correction (13 days for 1900-2099)
                julian_date = date(year, month, day)
                # Julian date is 13 days behind
                gregorian_date = julian_date + timedelta(days=13)
                # Handle year boundary - December dates + 13 days can spill into next year's January
                if gregorian_date.year != year:
                    continue  # Skip holidays that fall in different year
                holidays.append((gregorian_date, name, local_name, is_fixed))
            except ValueError:
                pass
        
        # Add Easter and movable feasts
        holidays.append((easter, "Easter", "Великден", False))
        
        # Palm Sunday (8 days before Easter)
        palm_sunday = easter + timedelta(days=-8)
        holidays.append((palm_sunday, "Palm Sunday", "Цветница", False))
        
        # Great Monday
        great_monday = easter + timedelta(days=-7)
        holidays.append((great_monday, "Great Monday", "Велики понеделник", False))
        
        # Great Tuesday
        great_tuesday = easter + timedelta(days=-6)
        holidays.append((great_tuesday, "Great Tuesday", "Велики вторник", False))
        
        # Ascension (39 days after Easter)
        ascension = easter + timedelta(days=39)
        holidays.append((ascension, "Ascension", "Възнесение", False))
        
        # Pentecost (49 days after Easter)
        pentecost = easter + timedelta(days=49)
        holidays.append((pentecost, "Pentecost", "Св. Дух", False))
        
        # St. Peter and Paul (57 days after Easter - usually June 29)
        st_peter_paul = easter + timedelta(days=57)
        holidays.append((st_peter_paul, "St. Peter and Paul", "Петровден", False))
        
        # St. George's Day (if not already on April 23)
        st_george = easter + timedelta(days=56)
        holidays.append((st_george, "St. George", "Гергьовден", False))
        
        # Dormition Fast (August 1-14)
        for day in range(1, 15):
            try:
                fast_date = date(year, 8, day)
                holidays.append((fast_date, "Dormition Fast", "Голямa Богородица", False))
            except:
                pass
        
        # Nativity Fast (November 25 - December 24)
        for day in range(25, 32):
            try:
                fast_date = date(year, 11, day)
                nativity_date = fast_date + timedelta(days=13)
                if nativity_date.month == 12:  # Only add if still in December
                    holidays.append((nativity_date, "Nativity Fast", "Коледни пости", False))
            except:
                pass

        try:
            fast_date = date(year, 12, 24)
            christmas_eve_date = fast_date + timedelta(days=13)
            if christmas_eve_date.month == 12 and christmas_eve_date.year == year:
                holidays.append((christmas_eve_date, "Christmas Eve Fast", "Бъднивечерски пост", False))
        except:
            pass
        
        # Sort by date
        holidays.sort(key=lambda x: x[0])
        
        return holidays


async def fetch_and_store_orthodox_holidays(db, year: int) -> int:
    """Fetch and store Orthodox holidays for a given year"""
    from datetime import date
    from sqlalchemy import select
    from backend.database.models import OrthodoxHoliday
    
    holidays = OrthodoxHolidayService.get_orthodox_holidays(year)
    
    count_new = 0
    existing_dates = set()
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    result = await db.execute(
        select(OrthodoxHoliday.date).where(OrthodoxHoliday.date >= start_date).where(OrthodoxHoliday.date <= end_date)
    )
    existing_dates = {row[0] for row in result.fetchall()}
    
    new_holidays = []
    for holiday_date, name, local_name, is_fixed in holidays:
        if holiday_date not in existing_dates:
            new_holidays.append({
                "date": holiday_date,
                "name": name,
                "local_name": local_name,
                "is_fixed": is_fixed
            })
    
    if new_holidays:
        for h in new_holidays:
            try:
                new_holiday = OrthodoxHoliday(**h)
                db.add(new_holiday)
                count_new += 1
            except Exception:
                pass
    
    await db.commit()
    return count_new
