from datetime import date, datetime

from backend.schemas.base import CustomBaseModel


class LeaveRequestBase(CustomBaseModel):
    user_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None = None
    status: str = "pending"
    created_at: datetime
    admin_comment: str | None = None
    employer_top_up: bool = False


class LeaveRequest(LeaveRequestBase):
    id: int


class LeaveBalanceBase(CustomBaseModel):
    user_id: int
    year: int
    total_days: int
    used_days: int


class LeaveBalance(LeaveBalanceBase):
    id: int
