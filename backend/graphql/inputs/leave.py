import datetime

import strawberry


@strawberry.input
class LeaveRequestInput:
    start_date: datetime.date
    end_date: datetime.date
    leave_type: str
    reason: str | None = None


@strawberry.input
class UpdateLeaveRequestStatusInput:
    request_id: int
    status: str
    admin_comment: str | None = None
    employer_top_up: bool | None = False
