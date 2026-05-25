from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.crud.repositories import payroll_repo, time_repo
from backend.database.models import (
    LeaveBalance,
    LeaveRequest,
    Notification,
    Shift,
    WorkSchedule,
    sofia_now,
)


class LeaveService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.time_repo = time_repo
        self.payroll_repo = payroll_repo

    async def get_balance(self, user_id: int, year: int) -> LeaveBalance:
        payrolls = await self.payroll_repo.get_user_payrolls(self.db, user_id)
        payroll = payrolls[0] if payrolls else None
        configured_days = payroll.annual_leave_days if payroll and payroll.annual_leave_days is not None else 20

        balances = await self.time_repo.get_leave_balance(self.db, user_id, year=year)
        balance = balances[0] if balances else None

        if not balance:
            balance = LeaveBalance(user_id=user_id, year=year, total_days=configured_days, used_days=0)
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)
        elif balance.total_days != configured_days:
            balance.total_days = configured_days
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)

        return balance

    async def calculate_working_days(self, start_date: date, end_date: date) -> int:
        days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:
                days += 1
            current += timedelta(days=1)
        return days

    async def approve_request(
        self,
        request_id: int,
        admin_comment: str | None = None,
        admin_user_id: int | None = None,
        employer_top_up: bool | None = False,
    ) -> LeaveRequest:
        request = await self._get_request(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.status != "pending":
            raise ValueError("Can only update pending requests")

        request.status = "approved"
        request.admin_comment = admin_comment
        request.employer_top_up = employer_top_up

        working_days = await self.calculate_working_days(request.start_date, request.end_date)

        if request.leave_type == "paid_leave":
            balance = await self.get_balance(request.user_id, request.start_date.year)
            if balance.used_days + working_days > balance.total_days:
                raise ValueError(
                    f"Недостатъчен баланс за отпуск. Заявени: {working_days}, Оставащи: {balance.total_days - balance.used_days}",
                )
            balance.used_days += working_days
            self.db.add(balance)

        await self._update_schedule_for_leave(request)

        await self.db.commit()
        await self.db.refresh(request)

        await self._notify_status(request, "ОДОБРЕНА")
        return request

    async def reject_request(
        self,
        request_id: int,
        admin_comment: str | None = None,
        admin_user_id: int | None = None,
    ) -> LeaveRequest:
        request = await self._get_request(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.status != "pending":
            raise ValueError("Can only update pending requests")

        request.status = "rejected"
        request.admin_comment = admin_comment

        await self.db.commit()
        await self.db.refresh(request)

        await self._notify_status(request, "ОТХВЪРЛЕНА")
        return request

    async def cancel_request(
        self,
        request_id: int,
        current_user_id: int,
        is_admin: bool = False,
    ) -> LeaveRequest:
        request = await self._get_request(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.user_id != current_user_id and not is_admin:
            raise ValueError("Not authorized to cancel this request")

        today = sofia_now().date()

        if request.status == "approved":
            if not is_admin:
                raise ValueError("Само администратор може да прекратява вече одобрен отпуск.")

            if today > request.end_date:
                raise ValueError("Не може да прекратите отминал отпуск.")

            if today >= request.start_date:
                await self._terminate_early(request, today)
            else:
                await self._cancel_future(request)

        elif request.status == "pending":
            request.status = "cancelled"
            self.db.add(request)
            await self.db.commit()
            await self.db.refresh(request)

        elif request.status in ["rejected", "cancelled"]:
            raise ValueError("Request is already cancelled/rejected")

        return request

    async def get_my_requests(self, user_id: int) -> list[LeaveRequest]:
        return await self.time_repo.get_user_leave_requests(self.db, user_id)

    async def get_pending_requests(self, company_id: int | None = None) -> list[LeaveRequest]:
        stmt = select(LeaveRequest).where(LeaveRequest.status == "pending")
        if company_id:
            stmt = stmt.where(LeaveRequest.company_id == company_id)
        stmt = stmt.order_by(LeaveRequest.created_at.desc()).options(
            selectinload(LeaveRequest.user),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_request(self, request_id: int) -> LeaveRequest | None:
        return await self.time_repo.get_leave_request_by_id(self.db, request_id)

    async def _update_schedule_for_leave(self, request: LeaveRequest) -> None:
        target_shift = await self._get_shift_by_type(request.leave_type)

        if target_shift:
            current = request.start_date
            while current <= request.end_date:
                if current.weekday() < 5:
                    sched_stmt = select(WorkSchedule).where(
                        WorkSchedule.user_id == request.user_id,
                        WorkSchedule.date == current,
                    )
                    sched_res = await self.db.execute(sched_stmt)
                    schedule = sched_res.scalars().first()

                    if schedule:
                        schedule.shift_id = target_shift.id
                        self.db.add(schedule)
                    else:
                        schedule = WorkSchedule(
                            user_id=request.user_id,
                            shift_id=target_shift.id,
                            date=current,
                        )
                        self.db.add(schedule)
                current += timedelta(days=1)

    async def _get_shift_by_type(self, leave_type: str) -> Shift | None:
        if leave_type == "paid_leave":
            shift_type = "leave"
        elif leave_type == "unpaid_leave":
            shift_type = "unpaid_leave"
        elif leave_type == "sick_leave":
            shift_type = "sick"
        else:
            return None

        stmt = select(Shift).where(Shift.shift_type == shift_type).limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _terminate_early(self, request: LeaveRequest, today: date) -> None:
        new_end_date = today

        refund_start = new_end_date + timedelta(days=1)
        days_to_refund = 0
        if refund_start <= request.end_date:
            days_to_refund = await self.calculate_working_days(refund_start, request.end_date)

        if request.leave_type == "paid_leave" and days_to_refund > 0:
            balance = await self.get_balance(request.user_id, request.start_date.year)
            balance.used_days = max(0, balance.used_days - days_to_refund)
            self.db.add(balance)

        curr = refund_start
        while curr <= request.end_date:
            sched_stmt = select(WorkSchedule).where(
                WorkSchedule.user_id == request.user_id,
                WorkSchedule.date == curr,
            )
            sched_res = await self.db.execute(sched_stmt)
            schedule = sched_res.scalars().first()
            if schedule:
                await self.db.delete(schedule)
            curr += timedelta(days=1)

        request.end_date = new_end_date
        request.admin_comment = (request.admin_comment or "") + f" [Прекратен на {today}]"
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

    async def _cancel_future(self, request: LeaveRequest) -> None:
        if request.leave_type == "paid_leave":
            days_to_refund = await self.calculate_working_days(request.start_date, request.end_date)
            balance = await self.get_balance(request.user_id, request.start_date.year)
            balance.used_days = max(0, balance.used_days - days_to_refund)
            self.db.add(balance)

        curr = request.start_date
        while curr <= request.end_date:
            sched_stmt = select(WorkSchedule).where(
                WorkSchedule.user_id == request.user_id,
                WorkSchedule.date == curr,
            )
            sched_res = await self.db.execute(sched_stmt)
            schedule = sched_res.scalars().first()
            if schedule:
                await self.db.delete(schedule)
            curr += timedelta(days=1)

        request.status = "cancelled"
        request.admin_comment = (request.admin_comment or "") + " [Отменен от администратор]"
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

    async def _notify_status(self, request: LeaveRequest, status_bg: str) -> None:
        notification = Notification(
            user_id=request.user_id,
            message=f"Вашата заявка за отпуск за периода {request.start_date} - {request.end_date} беше {status_bg}.",
        )
        self.db.add(notification)
        await self.db.flush()

        try:
            from backend.crud_legacy import send_push_to_user
            await send_push_to_user(
                self.db,
                request.user_id,
                "Статус на отпуска",
                f"Заявката Ви за {request.start_date} беше {status_bg}.",
            )
        except Exception:
            pass


leave_service = LeaveService
