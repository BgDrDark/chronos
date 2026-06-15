from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud.repositories.salary_payment_repo import salary_payment_repo
from backend.database.models import SalaryPaymentBatch, User
from backend.exceptions import ValidationException
from backend.services.notification_service import NotificationService
from backend.services.payroll_service import PayrollService


class SalaryPaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = salary_payment_repo
        self.notification_service = NotificationService(db)
        self.payroll_service = PayrollService(db)

    async def create_batch(
        self,
        company_id: int,
        period_start: date,
        period_end: date,
        payment_date: datetime,
        payment_method: str,
        paid_by: int,
        payment_reference: str | None = None,
        notes: str | None = None,
    ) -> SalaryPaymentBatch:
        if period_start > period_end:
            raise ValidationException("Началната дата трябва да е преди крайната")
        if not payment_method:
            raise ValidationException("Методът на плащане е задължителен")

        return await self.repo.create_batch(
            self.db,
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            payment_date=payment_date,
            payment_method=payment_method,
            paid_by=paid_by,
            payment_reference=payment_reference,
            notes=notes,
        )

    async def add_items(
        self,
        batch_id: int,
        user_ids: list[int],
    ) -> SalaryPaymentBatch:
        batch = await self.repo.get_batch(self.db, batch_id)
        if not batch:
            raise ValidationException(f"Партида {batch_id} не е намерена")
        if batch.status != "draft":
            raise ValidationException("Само чернови партиди могат да се редактират")

        errors = []
        for uid in user_ids:
            # Check for overlapping completed payments
            existing = await self.repo.get_completed_items_in_period(
                self.db, uid, batch.period_start, batch.period_end,
            )
            if existing:
                e = existing[0]
                user = await self.db.get(User, uid)
                name = f"{user.first_name} {user.last_name}" if user else str(uid)
                errors.append(
                    f"{name} вече е платен за период {e.batch.period_start} - {e.batch.period_end}. "
                    f"Новият период трябва да започва след {e.batch.period_end}.",
                )
                continue

            # Generate payslip if needed
            start_dt = datetime.combine(batch.period_start, datetime.min.time())
            end_dt = datetime.combine(batch.period_end, datetime.max.time())
            payslip = await self.payroll_service.generate_payslip(uid, start_dt, end_dt)

            amount = Decimal(str(payslip.total_amount))
            await self.repo.create_item(
                self.db,
                batch_id=batch_id,
                user_id=uid,
                amount=amount,
                payslip_id=payslip.id,
            )

        if errors:
            raise ValidationException("\n".join(errors))

        # Recalculate total_amount
        items = await self.repo.list_items_by_batch(self.db, batch_id)
        batch.total_amount = sum(item.amount for item in items)
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def complete_batch(self, batch_id: int) -> SalaryPaymentBatch:
        batch = await self.repo.get_batch(self.db, batch_id)
        if not batch:
            raise ValidationException(f"Партида {batch_id} не е намерена")
        if batch.status != "draft":
            raise ValidationException("Само чернови партиди могат да се финализират")
        if not batch.items:
            raise ValidationException("Партидата няма елементи")

        for item in batch.items:
            if item.payslip_id:
                await self.repo.update_payslip_batch(
                    self.db,
                    payslip_id=item.payslip_id,
                    batch_id=batch.id,
                    payment_status="paid",
                    payment_method=batch.payment_method,
                )
            item.paid_at = datetime.now()

        batch.status = "completed"

        for item in batch.items:
            user = await self.db.get(User, item.user_id)
            if user:
                await self.notification_service.create_notification(
                    user_id=item.user_id,
                    message=f"Заплатата ви за период {batch.period_start} - {batch.period_end} "
                            f"е платена. Нетна сума: {item.amount} лв.",
                )

        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def cancel_batch(self, batch_id: int) -> SalaryPaymentBatch:
        batch = await self.repo.get_batch(self.db, batch_id)
        if not batch:
            raise ValidationException(f"Партида {batch_id} не е намерена")
        if batch.status != "draft":
            raise ValidationException("Само чернови партиди могат да се отменят")

        batch.status = "cancelled"
        await self.db.flush()
        await self.db.refresh(batch)
        return batch

    async def get_statistics(
        self,
        company_id: int,
        year: int,
        month: int | None = None,
    ) -> dict:
        return await self.repo.get_statistics(self.db, company_id, year, month)

    async def export_batch(
        self,
        batch_id: int,
        format: str = "csv",
    ) -> str:
        batch = await self.repo.get_batch(self.db, batch_id)
        if not batch:
            raise ValidationException(f"Партида {batch_id} не е намерена")

        items = await self.repo.list_items_by_batch(self.db, batch_id)
        if format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Служител", "Брутна сума", "Нетна сума", "Статус", "Дата на плащане"])
            for item in items:
                user = await self.db.get(User, item.user_id)
                name = f"{user.first_name} {user.last_name}" if user else str(item.user_id)
                gross = 0
                if item.payslip:
                    gross = float(item.payslip.gross_salary) if item.payslip.gross_salary else 0
                writer.writerow([name, gross, float(item.amount), "paid", batch.payment_date])
            return output.getvalue()

        raise ValidationException(f"Unsupported format: {format}")
