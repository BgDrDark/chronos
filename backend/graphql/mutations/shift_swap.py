import strawberry

from backend.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
)
from backend.database.transaction_manager import atomic_with_savepoint
from backend.services.shift_swap_service import shift_swap_service
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class ShiftSwapMutation:
    @strawberry.mutation
    async def create_swap_request(self, requestor_schedule_id: int, target_user_id: int, target_schedule_id: int,
                                  info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_created"):
            res = await service.create_request(current_user.id, requestor_schedule_id, target_user_id, target_schedule_id)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def approve_swap(self, swap_id: int, approve: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        new_status = "approved" if approve else "rejected"
        service = shift_swap_service(db)
        async with atomic_with_savepoint(db, "swap_approved"):
            res = await service.update_status(swap_id, new_status, admin_user_id=current_user.id)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_instance(res)

    @strawberry.mutation
    async def respond_to_swap(self, swap_id: int, accept: bool, info: strawberry.Info) -> types.ShiftSwapRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        new_status = "accepted" if accept else "rejected"
        service = shift_swap_service(db)
        res = await service.update_status(swap_id, new_status)
        await db.commit()
        await db.refresh(res)
        return types.ShiftSwapRequest.from_instance(res)
