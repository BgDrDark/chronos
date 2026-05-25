import datetime

import strawberry
from sqlalchemy import select
from strawberry.file_uploads import Upload

from backend.auth.module_guard import verify_module_enabled
from backend.database.models import LeaveRequest
from backend.exceptions import AuthenticationException, NotFoundException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"

@strawberry.type
class LeaveMutation:
    @strawberry.mutation
    async def attach_leave_document(
        self,
        request_id: int,
        file: Upload,
        info: strawberry.Info,
    ) -> types.LeaveRequest:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        await verify_module_enabled("integrations", db)

        # Read file content
        content = await file.read()
        filename = file.filename

        # Perform OCR
        from backend.services.ocr_service import extract_text_from_file
        ocr_text = extract_text_from_file(content, filename)

        stmt = select(LeaveRequest).where(LeaveRequest.id == request_id)
        res = await db.execute(stmt)
        req = res.scalars().first()

        if not req:
            raise NotFoundException.request()

        if req.user_id != current_user.id and current_user.role.name not in ["admin", "super_admin"]:
            raise AuthenticationException(detail="Нямате права за това действие")

        # Append text
        original_reason = req.reason or ""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_reason = f"{original_reason}\n\n[OCR DATA - {filename} - {timestamp}]:\n{ocr_text}"
        req.reason = new_reason

        db.add(req)
        await db.commit()
        await db.refresh(req)

        return types.LeaveRequest.from_pydantic(req)
