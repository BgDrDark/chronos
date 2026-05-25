from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    BusinessTrip,
    ContractAnnex,
    ContractTemplate,
    EmploymentContract,
    NightWorkBonus,
    OvertimeWork,
    User,
    WorkExperience,
    WorkOnHoliday,
)

from .base import BaseRepository


class TRZRepository(BaseRepository):
    """Repository за TRZ (Трудови договори)"""

    model = EmploymentContract

    async def get_user_contracts(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> list[EmploymentContract]:
        """Връща договорите на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .order_by(EmploymentContract.start_date.desc()),
        )
        return list(result.scalars().all())

    async def get_active_contract(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> EmploymentContract | None:
        """Връща активния договор на потребител"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.user_id == user_id)
            .where(EmploymentContract.status == "active")
            .order_by(EmploymentContract.start_date.desc()),
        )
        return result.scalar_one_or_none()

    async def get_contract_annexes(
        self,
        db: AsyncSession,
        contract_id: int,
    ) -> list[ContractAnnex]:
        """Връща анексите на договор"""
        result = await db.execute(
            select(ContractAnnex)
            .where(ContractAnnex.contract_id == contract_id)
            .order_by(ContractAnnex.created_at.desc()),
        )
        return list(result.scalars().all())

    async def get_contract_with_relations(
        self,
        db: AsyncSession,
        contract_id: int,
    ) -> EmploymentContract | None:
        """Връща договор с потребител и компания"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.id == contract_id)
            .options(
                selectinload(EmploymentContract.user),
                selectinload(EmploymentContract.company),
                selectinload(EmploymentContract.position),
                selectinload(EmploymentContract.department),
            ),
        )
        return result.scalar_one_or_none()

    async def get_contracts_by_company(
        self,
        db: AsyncSession,
        company_id: int,
        status: str = None,
        limit: int = 100,
    ) -> list[EmploymentContract]:
        """Връща договорите на компания"""
        query = select(EmploymentContract).where(EmploymentContract.company_id == company_id)
        if status:
            query = query.where(EmploymentContract.status == status)
        query = query.order_by(EmploymentContract.start_date.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ── EmploymentContract ──────────────────────────────────────────

    async def create_contract(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> EmploymentContract:
        """Създава нов трудов договор"""
        instance = EmploymentContract(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_contract(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> EmploymentContract | None:
        """Обновява трудов договор"""
        instance = await self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def terminate_contract(
        self,
        db: AsyncSession,
        id: int,
        end_date: date,
        termination_reason: str | None = None,
    ) -> EmploymentContract | None:
        """Прекратява договор - статус terminated"""
        contract = await self.get_by_id(db, id)
        if contract:
            contract.status = "terminated"
            contract.is_active = False
            contract.end_date = end_date
            await db.flush()
            await db.refresh(contract)
        return contract

    async def get_contract_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> EmploymentContract | None:
        """Връща договор с всички релации"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.id == id)
            .options(
                selectinload(EmploymentContract.user),
                selectinload(EmploymentContract.company),
                selectinload(EmploymentContract.position),
                selectinload(EmploymentContract.department),
                selectinload(EmploymentContract.annexes),
            ),
        )
        return result.scalar_one_or_none()

    async def get_active_contracts_by_company(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[EmploymentContract]:
        """Всички активни договори за компания"""
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.company_id == company_id)
            .where(EmploymentContract.status == "active")
            .order_by(EmploymentContract.start_date.desc()),
        )
        return list(result.scalars().all())

    async def deactivate_expired_contracts(
        self,
        db: AsyncSession,
    ) -> int:
        """Деактивира изтеклите договори (end_date < днес)"""
        today = date.today()
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.end_date < today)
            .where(EmploymentContract.status == "active"),
        )
        contracts = list(result.scalars().all())
        for contract in contracts:
            contract.status = "terminated"
            contract.is_active = False
        await db.flush()
        return len(contracts)

    async def get_contracts_expiring_soon(
        self,
        db: AsyncSession,
        company_id: int,
        days: int,
    ) -> list[EmploymentContract]:
        """Договори, изтичащи в рамките на N дни"""
        today = date.today()
        end = today + timedelta(days=days)
        result = await db.execute(
            select(EmploymentContract)
            .where(EmploymentContract.company_id == company_id)
            .where(EmploymentContract.end_date >= today)
            .where(EmploymentContract.end_date <= end)
            .where(EmploymentContract.status == "active")
            .order_by(EmploymentContract.end_date.asc()),
        )
        return list(result.scalars().all())

    # ── ContractAnnex ───────────────────────────────────────────────

    async def create_annex(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> ContractAnnex:
        """Създава анекс към договор"""
        instance = ContractAnnex(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_annex_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> ContractAnnex | None:
        """Връща анекс по ID"""
        result = await db.execute(
            select(ContractAnnex).where(ContractAnnex.id == id),
        )
        return result.scalar_one_or_none()

    async def get_annexes_by_contract(
        self,
        db: AsyncSession,
        contract_id: int,
    ) -> list[ContractAnnex]:
        """Връща анексите на договор (alias за get_contract_annexes)"""
        return await self.get_contract_annexes(db, contract_id)

    async def delete_annex(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        """Изтрива анекс"""
        instance = await self.get_annex_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    # ── ContractTemplate ────────────────────────────────────────────

    async def create_template(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> ContractTemplate:
        """Създава шаблон за договор"""
        instance = ContractTemplate(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_template_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> ContractTemplate | None:
        """Връща шаблон по ID"""
        result = await db.execute(
            select(ContractTemplate).where(ContractTemplate.id == id),
        )
        return result.scalar_one_or_none()

    async def get_templates_by_company(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[ContractTemplate]:
        """Шаблони на компания"""
        result = await db.execute(
            select(ContractTemplate)
            .where(ContractTemplate.company_id == company_id)
            .order_by(ContractTemplate.name.asc()),
        )
        return list(result.scalars().all())

    async def update_template(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> ContractTemplate | None:
        """Обновява шаблон"""
        instance = await self.get_template_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_template(
        self,
        db: AsyncSession,
        id: int,
    ) -> bool:
        """Изтрива шаблон"""
        instance = await self.get_template_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    # ── NightWorkBonus ──────────────────────────────────────────────

    async def create_night_work_bonus(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> NightWorkBonus:
        """Създава запис за нощен труд"""
        instance = NightWorkBonus(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_night_work_bonuses_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[NightWorkBonus]:
        """Нощен труд за потребител в период"""
        result = await db.execute(
            select(NightWorkBonus)
            .where(NightWorkBonus.user_id == user_id)
            .where(NightWorkBonus.date >= start_date)
            .where(NightWorkBonus.date <= end_date)
            .order_by(NightWorkBonus.date.desc()),
        )
        return list(result.scalars().all())

    async def get_night_work_bonuses_by_period(
        self,
        db: AsyncSession,
        company_id: int,
        start_date: date,
        end_date: date,
    ) -> list[NightWorkBonus]:
        """Нощен труд за компания в период"""
        result = await db.execute(
            select(NightWorkBonus)
            .join(User, NightWorkBonus.user_id == User.id)
            .where(User.company_id == company_id)
            .where(NightWorkBonus.date >= start_date)
            .where(NightWorkBonus.date <= end_date)
            .order_by(NightWorkBonus.date.desc()),
        )
        return list(result.scalars().all())

    # ── OvertimeWork ────────────────────────────────────────────────

    async def create_overtime_work(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> OvertimeWork:
        """Създава запис за извънреден труд"""
        instance = OvertimeWork(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_overtime_works_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[OvertimeWork]:
        """Извънреден труд за потребител в период"""
        result = await db.execute(
            select(OvertimeWork)
            .where(OvertimeWork.user_id == user_id)
            .where(OvertimeWork.date >= start_date)
            .where(OvertimeWork.date <= end_date)
            .order_by(OvertimeWork.date.desc()),
        )
        return list(result.scalars().all())

    async def get_overtime_works_by_period(
        self,
        db: AsyncSession,
        company_id: int,
        start_date: date,
        end_date: date,
    ) -> list[OvertimeWork]:
        """Извънреден труд за компания в период"""
        result = await db.execute(
            select(OvertimeWork)
            .join(User, OvertimeWork.user_id == User.id)
            .where(User.company_id == company_id)
            .where(OvertimeWork.date >= start_date)
            .where(OvertimeWork.date <= end_date)
            .order_by(OvertimeWork.date.desc()),
        )
        return list(result.scalars().all())

    # ── WorkOnHoliday ───────────────────────────────────────────────

    async def create_work_on_holiday(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> WorkOnHoliday:
        """Създава запис за труд на празник"""
        instance = WorkOnHoliday(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_work_on_holidays_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[WorkOnHoliday]:
        """Труд на празник за потребител в период"""
        result = await db.execute(
            select(WorkOnHoliday)
            .where(WorkOnHoliday.user_id == user_id)
            .where(WorkOnHoliday.date >= start_date)
            .where(WorkOnHoliday.date <= end_date)
            .order_by(WorkOnHoliday.date.desc()),
        )
        return list(result.scalars().all())

    async def get_work_on_holidays_by_period(
        self,
        db: AsyncSession,
        company_id: int,
        start_date: date,
        end_date: date,
    ) -> list[WorkOnHoliday]:
        """Труд на празник за компания в период"""
        result = await db.execute(
            select(WorkOnHoliday)
            .join(User, WorkOnHoliday.user_id == User.id)
            .where(User.company_id == company_id)
            .where(WorkOnHoliday.date >= start_date)
            .where(WorkOnHoliday.date <= end_date)
            .order_by(WorkOnHoliday.date.desc()),
        )
        return list(result.scalars().all())

    # ── BusinessTrip ────────────────────────────────────────────────

    async def create_business_trip(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> BusinessTrip:
        """Създава командировка"""
        instance = BusinessTrip(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_business_trip(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> BusinessTrip | None:
        """Обновява командировка"""
        instance = await db.execute(
            select(BusinessTrip).where(BusinessTrip.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_business_trip_by_id(
        self,
        db: AsyncSession,
        id: int,
    ) -> BusinessTrip | None:
        """Връща командировка по ID"""
        result = await db.execute(
            select(BusinessTrip).where(BusinessTrip.id == id),
        )
        return result.scalar_one_or_none()

    async def get_business_trips_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[BusinessTrip]:
        """Командировки за потребител в период"""
        result = await db.execute(
            select(BusinessTrip)
            .where(BusinessTrip.user_id == user_id)
            .where(BusinessTrip.start_date >= start_date)
            .where(BusinessTrip.end_date <= end_date)
            .order_by(BusinessTrip.start_date.desc()),
        )
        return list(result.scalars().all())

    async def get_active_business_trips(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[BusinessTrip]:
        """Активни командировки (end_date >= днес) за компания"""
        today = date.today()
        result = await db.execute(
            select(BusinessTrip)
            .join(User, BusinessTrip.user_id == User.id)
            .where(User.company_id == company_id)
            .where(BusinessTrip.end_date >= today)
            .where(BusinessTrip.status == "approved")
            .order_by(BusinessTrip.start_date.asc()),
        )
        return list(result.scalars().all())

    # ── WorkExperience ──────────────────────────────────────────────

    async def create_work_experience(
        self,
        db: AsyncSession,
        **kwargs,
    ) -> WorkExperience:
        """Създава запис за трудов стаж"""
        instance = WorkExperience(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_work_experience(
        self,
        db: AsyncSession,
        id: int,
        **kwargs,
    ) -> WorkExperience | None:
        """Обновява трудов стаж"""
        instance = await db.execute(
            select(WorkExperience).where(WorkExperience.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_work_experience_by_user(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> list[WorkExperience]:
        """Трудов стаж за потребител"""
        result = await db.execute(
            select(WorkExperience)
            .where(WorkExperience.user_id == user_id)
            .order_by(WorkExperience.start_date.desc()),
        )
        return list(result.scalars().all())


trz_repo = TRZRepository()
