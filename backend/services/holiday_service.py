import httpx
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import PublicHoliday, sofia_now

API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/BG"

async def fetch_and_store_holidays(db: AsyncSession, year: int):
    url = API_URL.format(year=year)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            holidays_data = response.json()
    except Exception as e:
        print(f"Error fetching holidays: {e}")
        return False

    count_new = 0
    for h in holidays_data:
        date_str = h.get("date")
        local_name = h.get("localName")
        name = h.get("name")
        
        holiday_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Check if exists
        result = await db.execute(select(PublicHoliday).where(PublicHoliday.date == holiday_date))
        existing = result.scalars().first()
        
        if not existing:
            new_holiday = PublicHoliday(
                date=holiday_date,
                name=name,
                local_name=local_name
            )
            db.add(new_holiday)
            count_new += 1
            
    await db.commit()
    return count_new
