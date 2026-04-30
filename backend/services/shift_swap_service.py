from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

from backend.database.models import ShiftSwapRequest, WorkSchedule, Notification


class ShiftSwapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self,
        requestor_id: int,
        requestor_schedule_id: int,
        target_user_id: int,
        target_schedule_id: int
    ) -> ShiftSwapRequest:
        req_sched = await self.db.get(WorkSchedule, requestor_schedule_id)
        tar_sched = await self.db.get(WorkSchedule, target_schedule_id)

        if not req_sched or req_sched.user_id != requestor_id:
            raise ValueError("Вашата избрана смяна е невалидна.")
        if not tar_sched or tar_sched.user_id != target_user_id:
            raise ValueError("Избраната смяна на колегата е невалидна.")

        stmt = select(ShiftSwapRequest).where(
            ShiftSwapRequest.requestor_schedule_id == requestor_schedule_id,
            ShiftSwapRequest.status == "pending"
        )
        res = await self.db.execute(stmt)
        if res.scalars().first():
            raise ValueError("Вече има активна заявка за тази смяна.")

        swap = ShiftSwapRequest(
            requestor_id=requestor_id,
            requestor_schedule_id=requestor_schedule_id,
            target_user_id=target_user_id,
            target_schedule_id=target_schedule_id,
            status="pending"
        )
        self.db.add(swap)
        await self.db.commit()
        await self.db.refresh(swap)

        await self._notify_target_user(swap, req_sched)
        await self._push_notification(
            target_user_id,
            "Размяна на смени",
            f"Колега иска да размени смяна с Вас за {req_sched.date}."
        )

        return swap

    async def get_request(self, swap_id: int) -> Optional[ShiftSwapRequest]:
        stmt = select(ShiftSwapRequest).where(ShiftSwapRequest.id == swap_id).options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_user_requests(self, user_id: int) -> List[ShiftSwapRequest]:
        stmt = select(ShiftSwapRequest).where(
            or_(
                ShiftSwapRequest.requestor_id == user_id,
                ShiftSwapRequest.target_user_id == user_id
            )
        ).order_by(ShiftSwapRequest.created_at.desc()).options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_pending_requests(self) -> List[ShiftSwapRequest]:
        stmt = select(ShiftSwapRequest).where(ShiftSwapRequest.status == "accepted").options(
            selectinload(ShiftSwapRequest.requestor),
            selectinload(ShiftSwapRequest.target_user),
            selectinload(ShiftSwapRequest.requestor_schedule).selectinload(WorkSchedule.shift),
            selectinload(ShiftSwapRequest.target_schedule).selectinload(WorkSchedule.shift)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_status(
        self,
        swap_id: int,
        new_status: str,
        admin_user_id: Optional[int] = None
    ) -> ShiftSwapRequest:
        swap = await self.get_request(swap_id)
        if not swap:
            raise ValueError("Заявката не е намерена.")

        swap.status = new_status

        if new_status == "approved":
            await self._execute_swap(swap, admin_user_id)
        elif new_status == "accepted":
            await self._handle_accepted(swap)
        elif new_status == "rejected":
            await self._handle_rejected(swap)
        elif new_status == "cancelled":
            pass

        await self.db.commit()
        await self.db.refresh(swap)
        return swap

    async def delete_request(self, swap_id: int, user_id: int) -> bool:
        swap = await self.get_request(swap_id)
        if not swap:
            return False

        if swap.requestor_id != user_id and swap.target_user_id != user_id:
            raise ValueError("Нямате права да изтриете тази заявка.")

        if swap.status != "pending":
            raise ValueError("Може да изтриете само чакащи заявки.")

        await self.db.delete(swap)
        await self.db.commit()
        return True

    async def _execute_swap(self, swap: ShiftSwapRequest, admin_user_id: Optional[int]) -> None:
        req_sched = swap.requestor_schedule
        tar_sched = swap.target_schedule

        old_req_shift_id = req_sched.shift_id
        req_sched.shift_id = tar_sched.shift_id
        tar_sched.shift_id = old_req_shift_id

        self.db.add(req_sched)
        self.db.add(tar_sched)

        await self._create_audit_log(admin_user_id, swap)
        await self._notify_approval(swap)

    async def _handle_accepted(self, swap: ShiftSwapRequest) -> None:
        requestor = swap.requestor
        target = swap.target_user
        req_sched = swap.requestor_schedule
        tar_sched = swap.target_schedule

        for admin_id in await self._get_admin_ids():
            await self._create_notification(
                admin_id,
                f"Нова размяна на смени чака одобрение: {requestor.email} <-> {target.email}"
            )

        await self._create_notification(
            swap.requestor_id,
            f"Колегата ПРИЕ вашата покана за размяна. Чака се одобрение от администратор."
        )
        await self._push_notification(
            swap.requestor_id,
            "Поканата е приета",
            "Колегата прие вашата размяна. Чака се одобрение."
        )

    async def _handle_rejected(self, swap: ShiftSwapRequest) -> None:
        await self._create_notification(
            swap.requestor_id,
            f"Колегата ОТКАЗА вашата покана за размяна."
        )
        await self._push_notification(
            swap.requestor_id,
            "Поканата е отказана",
            "Колегата отказа вашата покана за размяна."
        )

    async def _notify_target_user(self, swap: ShiftSwapRequest, req_sched: WorkSchedule) -> None:
        await self._create_notification(
            swap.target_user_id,
            f"Колега иска да размени смяна с Вас за дата {req_sched.date}."
        )

    async def _notify_approval(self, swap: ShiftSwapRequest) -> None:
        req_sched = swap.requestor_schedule
        tar_sched = swap.target_schedule

        await self._create_notification(
            swap.requestor_id,
            f"Размяната на смени за {req_sched.date} беше ОДОБРЕНА от администратор."
        )
        await self._create_notification(
            swap.target_user_id,
            f"Размяната на смени за {tar_sched.date} беше ОДОБРЕНА от администратор."
        )
        await self._push_notification(
            swap.requestor_id,
            "Размяната е одобрена",
            f"Размяната за {req_sched.date} беше одобрена."
        )
        await self._push_notification(
            swap.target_user_id,
            "Размяната е одобрена",
            f"Размяната за {tar_sched.date} беше одобрена."
        )

    async def _create_notification(self, user_id: int, message: str) -> Notification:
        notification = Notification(user_id=user_id, message=message)
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def _push_notification(self, user_id: int, title: str, body: str) -> None:
        from backend.crud_legacy import send_push_to_user
        try:
            await send_push_to_user(self.db, user_id, title, body)
        except Exception:
            pass

    async def _get_admin_ids(self) -> List[int]:
        from backend.database.models import User, Role
        stmt = select(User.id).join(Role).where(Role.name.in_(["admin", "super_admin"]))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def _create_audit_log(self, admin_user_id: Optional[int], swap: ShiftSwapRequest) -> None:
        pass


shift_swap_service = ShiftSwapService