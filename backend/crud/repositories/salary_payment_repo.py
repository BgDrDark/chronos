from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    Payslip,
    SalaryPaymentBatch,
    SalaryPaymentItem,
    User,
)

from .base import BaseRepository


class SalaryPaymentRepository(BaseRepository):
    model = SalaryPaymentBatch

    # --- Batch ---

    async def create_batch(
        self,
        db: AsyncSession,
        company_id: int,
        period_start: date,
        period_end: date,
        payment_date: datetime,
        payment_method: str,
        paid_by: int,
        payment_reference: str | None = None,
        notes: str | None = None,
    ) -> SalaryPaymentBatch:
        batch = SalaryPaymentBatch(
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            payment_date=payment_date,
            payment_method=payment_method,
            paid_by=paid_by,
            payment_reference=payment_reference,
            notes=notes,
            status="draft",
        )
        db.add(batch)
        await db.flush()
        return batch

    async def get_batch(self, db: AsyncSession, batch_id: int) -> SalaryPaymentBatch | None:
        result = await db.execute(
            select(SalaryPaymentBatch)
            .where(SalaryPaymentBatch.id == batch_id)
            .options(selectinload(SalaryPaymentBatch.items).selectinload(SalaryPaymentItem.user)),
        )
        return result.scalar_one_or_none()

    async def list_batches(
        self,
        db: AsyncSession,
        company_id: int | None = None,
        status: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[SalaryPaymentBatch]:
        query = select(SalaryPaymentBatch).order_by(SalaryPaymentBatch.created_at.desc())
        if company_id is not None:
            query = query.where(SalaryPaymentBatch.company_id == company_id)
        if status is not None:
            query = query.where(SalaryPaymentBatch.status == status)
        if period_start is not None:
            query = query.where(SalaryPaymentBatch.period_start >= period_start)
        if period_end is not None:
            query = query.where(SalaryPaymentBatch.period_end <= period_end)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_batch_status(
        self,
        db: AsyncSession,
        batch_id: int,
        status: str,
    ) -> SalaryPaymentBatch | None:
        batch = await db.get(SalaryPaymentBatch, batch_id)
        if not batch:
            return None
        batch.status = status
        await db.flush()
        return batch

    # --- Items ---

    async def create_item(
        self,
        db: AsyncSession,
        batch_id: int,
        user_id: int,
        amount: Decimal,
        payslip_id: int | None = None,
    ) -> SalaryPaymentItem:
        item = SalaryPaymentItem(
            batch_id=batch_id,
            user_id=user_id,
            amount=amount,
            payslip_id=payslip_id,
        )
        db.add(item)
        await db.flush()
        return item

    async def list_items_by_batch(self, db: AsyncSession, batch_id: int) -> list[SalaryPaymentItem]:
        result = await db.execute(
            select(SalaryPaymentItem)
            .where(SalaryPaymentItem.batch_id == batch_id)
            .options(selectinload(SalaryPaymentItem.user)),
        )
        return list(result.scalars().all())

    async def list_items_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        year: int | None = None,
    ) -> list[SalaryPaymentItem]:
        query = (
            select(SalaryPaymentItem)
            .where(SalaryPaymentItem.user_id == user_id)
            .join(SalaryPaymentBatch)
            .where(SalaryPaymentBatch.status == "completed")
            .options(selectinload(SalaryPaymentItem.payslip))
            .order_by(SalaryPaymentBatch.period_start.desc())
        )
        if year is not None:
            query = query.where(
                and_(
                    SalaryPaymentBatch.period_start >= date(year, 1, 1),
                    SalaryPaymentBatch.period_start <= date(year, 12, 31),
                ),
            )
        result = await db.execute(query)
        return list(result.scalars().all())

    # --- Payslip ---

    async def update_payslip_batch(
        self,
        db: AsyncSession,
        payslip_id: int,
        batch_id: int,
        payment_status: str = "paid",
        payment_method: str = "bank",
    ) -> Payslip | None:
        payslip = await db.get(Payslip, payslip_id)
        if not payslip:
            return None
        payslip.batch_id = batch_id
        payslip.payment_status = payment_status
        payslip.actual_payment_date = datetime.now()
        payslip.payment_method = payment_method
        await db.flush()
        return payslip

    # --- Overlap check ---

    async def get_completed_items_in_period(
        self,
        db: AsyncSession,
        user_id: int,
        period_start: date,
        period_end: date,
    ) -> list[SalaryPaymentItem]:
        result = await db.execute(
            select(SalaryPaymentItem)
            .where(SalaryPaymentItem.user_id == user_id)
            .join(SalaryPaymentBatch)
            .where(SalaryPaymentBatch.status == "completed")
            .where(
                and_(
                    SalaryPaymentBatch.period_start <= period_end,
                    SalaryPaymentBatch.period_end >= period_start,
                ),
            ),
        )
        return list(result.scalars().all())

    # --- Statistics ---

    async def get_statistics(
        self,
        db: AsyncSession,
        company_id: int,
        year: int,
        month: int | None = None,
    ) -> dict:
        query = select(SalaryPaymentBatch).where(
            SalaryPaymentBatch.company_id == company_id,
            SalaryPaymentBatch.status == "completed",
            SalaryPaymentBatch.period_start >= date(year, 1, 1),
            SalaryPaymentBatch.period_start <= date(year, 12, 31),
        )
        if month is not None:
            query = query.where(
                SalaryPaymentBatch.period_start >= date(year, month, 1),
                SalaryPaymentBatch.period_start <= date(year, month, 31),
            )

        count_result = await db.execute(query)
        batches = list(count_result.scalars().all())

        total_amount = sum(b.total_amount for b in batches)
        total_items = sum(len(b.items) for b in batches)

        by_method: dict[str, float] = {}
        for b in batches:
            by_method[b.payment_method] = by_method.get(b.payment_method, 0) + float(b.total_amount)

        status_query = select(
            SalaryPaymentBatch.status,
            func.count(SalaryPaymentBatch.id),
        ).where(
            SalaryPaymentBatch.company_id == company_id,
        )
        if month is not None:
            status_query = status_query.where(
                SalaryPaymentBatch.period_start >= date(year, month, 1),
            )
        status_query = status_query.group_by(SalaryPaymentBatch.status)
        status_result = await db.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.all()}

        return {
            "total_batches": len(batches),
            "total_amount": float(total_amount),
            "total_employees_paid": total_items,
            "average_payment_per_employee": float(total_amount / total_items) if total_items else 0.0,
            "by_method": by_method,
            "by_status": by_status,
        }


salary_payment_repo = SalaryPaymentRepository()
