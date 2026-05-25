import datetime
import logging

import strawberry
from strawberry.file_uploads import Upload
from sqlalchemy import select

from backend.crud.repositories import time_repo
from backend.database.transaction_manager import atomic_with_savepoint
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import types
from backend.graphql.inputs import LeaveRequestInput, UpdateLeaveRequestStatusInput
from backend.auth.module_guard import verify_module_enabled
from backend.services.leave_service import leave_service

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class LeaveMutation:
    @strawberry.mutation(name="requestLeave")
    async def create_leave_request(self, leave_input: LeaveRequestInput, info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import LeaveRequest
        leave_request = LeaveRequest(
            user_id=current_user.id,
            start_date=leave_input.start_date,
            end_date=leave_input.end_date,
            leave_type=leave_input.leave_type,
            reason=leave_input.reason,
            status="pending"
        )
        db.add(leave_request)
        await db.commit()
        await db.refresh(leave_request)
        return types.LeaveRequest.from_instance(leave_request)

    @strawberry.mutation
    async def delete_leave_request(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")
        is_admin = current_user.role.name in ["admin", "super_admin"]
        result = await time_repo.delete_leave_request(db, id, current_user.id, is_admin)
        await db.commit()
        return result

    @strawberry.mutation(name="cancelLeaveRequest")
    async def cancel_leave_request(self, request_id: int, info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None:
            raise AuthenticationException(detail=authenticate_msg)
        req = await time_repo.get_leave_request_by_id(db, request_id)
        if not req:
            raise NotFoundException.leave_request(request_id=request_id)
        if req.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("cancel")
        if req.status not in ["pending", "approved"]:
            raise ValidationException.field("status", "Може да отмените само чакащи или одобрени отпуски")
        req.status = "cancelled"
        await db.commit()
        await db.refresh(req)
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation(name="approveLeave")
    async def approve_leave(self, info: strawberry.Info, request_id: int, admin_comment: str = None, employer_top_up: bool = False) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        async with atomic_with_savepoint(db, "leave_approved"):
            req = await service.approve_request(
                request_id=request_id,
                admin_comment=admin_comment,
                admin_user_id=current_user.id,
                employer_top_up=employer_top_up
            )
        await db.commit()
        await db.refresh(req)
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation(name="rejectLeave")
    async def reject_leave(self, info: strawberry.Info, request_id: int, admin_comment: str = None) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        async with atomic_with_savepoint(db, "leave_rejected"):
            req = await service.reject_request(
                request_id=request_id,
                admin_comment=admin_comment,
                admin_user_id=current_user.id
            )
        await db.commit()
        await db.refresh(req)
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def update_leave_request_status(self, input: UpdateLeaveRequestStatusInput,
                                          info: strawberry.Info) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if current_user is None or current_user.role.name not in ["admin", "super_admin"]:
            raise PermissionDeniedException.for_action("manage")

        service = leave_service(db)
        if input.status == "approved":
            req = await service.approve_request(
                request_id=input.request_id,
                admin_comment=input.admin_comment,
                admin_user_id=current_user.id,
                employer_top_up=input.employer_top_up
            )
        else:
            req = await service.reject_request(
                request_id=input.request_id,
                admin_comment=input.admin_comment,
                admin_user_id=current_user.id
            )
        await db.commit()
        await db.refresh(req)
        return types.LeaveRequest.from_instance(req)

    @strawberry.mutation
    async def attach_leave_document(
            self,
            request_id: int,
            file: Upload,
            info: strawberry.Info
    ) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await verify_module_enabled("integrations", db)

        content = await file.read()  # type: ignore
        filename = file.filename  # type: ignore

        from backend.services.ocr_service import extract_text_from_file
        ocr_text = extract_text_from_file(content, filename)

        from backend.database.models import LeaveRequest
        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        res = await db.execute(stmt)
        req = res.scalars().first()

        if not req:
            raise NotFoundException.request()

        if req.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Нямате права за това действие")

        original_reason = req.reason or ""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_reason = f"{original_reason}\n\n[OCR DATA - {filename} - {timestamp}]:\n{ocr_text}"
        req.reason = new_reason

        db.add(req)
        await db.commit()
        await db.refresh(req)

        return types.LeaveRequest.from_instance(req)
