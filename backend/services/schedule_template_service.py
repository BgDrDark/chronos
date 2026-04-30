from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from backend.database.models import ScheduleTemplate, ScheduleTemplateItem, WorkSchedule, User


class ScheduleTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self,
        name: str,
        company_id: int,
        description: Optional[str] = None,
        items: List[dict] = None
    ) -> ScheduleTemplate:
        """Create a new schedule template"""
        template = ScheduleTemplate(
            name=name,
            company_id=company_id,
            description=description
        )
        self.db.add(template)
        await self.db.flush()

        if items:
            for item in items:
                tmpl_item = ScheduleTemplateItem(
                    template_id=template.id,
                    day_index=item["day_index"],
                    shift_id=item.get("shift_id")
                )
                self.db.add(tmpl_item)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_templates(self, company_id: Optional[int] = None) -> List[ScheduleTemplate]:
        """Get all templates"""
        stmt = select(ScheduleTemplate).options(
            selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
        )
        if company_id:
            stmt = stmt.where(ScheduleTemplate.company_id == company_id)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_template(self, template_id: int, company_id: Optional[int] = None) -> Optional[ScheduleTemplate]:
        """Get a specific template"""
        stmt = select(ScheduleTemplate).where(
            ScheduleTemplate.id == template_id
        ).options(
            selectinload(ScheduleTemplate.items).selectinload(ScheduleTemplateItem.shift)
        )
        
        if company_id:
            stmt = stmt.where(ScheduleTemplate.company_id == company_id)
        
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def delete_template(self, template_id: int, company_id: Optional[int] = None) -> bool:
        """Delete a template"""
        stmt = select(ScheduleTemplate).where(ScheduleTemplate.id == template_id)
        
        if company_id:
            stmt = stmt.where(ScheduleTemplate.company_id == company_id)
        
        result = await self.db.execute(stmt)
        tmpl = result.scalars().first()
        
        if tmpl:
            await self.db.delete(tmpl)
            await self.db.commit()
            return True
        
        return False

    async def apply_template(
        self,
        template_id: int,
        user_id: int,
        start_date: date,
        end_date: date,
        admin_id: int
    ) -> List[WorkSchedule]:
        """Apply a template to a user for a date range"""
        template = await self.get_template(template_id)
        
        if not template or not template.items:
            raise ValueError("Шаблонът не съществува или е празен.")

        sorted_items = sorted(template.items, key=lambda x: x.day_index)
        rotation_length = len(sorted_items)

        created_schedules = []
        current_date = start_date
        days_processed = 0

        while current_date <= end_date:
            item_index = days_processed % rotation_length
            target_item = sorted_items[item_index]

            stmt = select(WorkSchedule).where(
                WorkSchedule.user_id == user_id,
                WorkSchedule.date == current_date
            )
            res = await self.db.execute(stmt)
            existing = res.scalars().first()

            if target_item.shift_id:
                if existing:
                    existing.shift_id = target_item.shift_id
                    self.db.add(existing)
                else:
                    new_schedule = WorkSchedule(
                        user_id=user_id,
                        shift_id=target_item.shift_id,
                        date=current_date
                    )
                    self.db.add(new_schedule)
                    created_schedules.append(new_schedule)
            
            current_date = current_date.replace(day=current_date.day + 1)
            days_processed += 1

        await self.db.commit()

        for schedule in created_schedules:
            await self.db.refresh(schedule)

        return created_schedules

    async def get_template_preview(
        self,
        template_id: int,
        start_date: date,
        end_date: date
    ) -> List[dict]:
        """Preview what a template would create"""
        template = await self.get_template(template_id)
        
        if not template or not template.items:
            return []

        sorted_items = sorted(template.items, key=lambda x: x.day_index)
        rotation_length = len(sorted_items)

        preview = []
        current_date = start_date
        days_processed = 0

        while current_date <= end_date:
            item_index = days_processed % rotation_length
            item = sorted_items[item_index]
            
            preview.append({
                "date": current_date.isoformat(),
                "day_index": item.day_index,
                "shift_id": item.shift_id,
                "shift_name": item.shift.name if item.shift else None
            })
            
            current_date = current_date.replace(day=current_date.day + 1)
            days_processed += 1

        return preview


schedule_template_service = ScheduleTemplateService