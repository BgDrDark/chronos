from backend.schemas.base import CustomBaseModel


class MonthlyWorkDays(CustomBaseModel):
    id: int
    year: int
    month: int
    days_count: int
