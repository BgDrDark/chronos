from datetime import date

from backend.schemas.base import CustomBaseModel


class PublicHolidayBase(CustomBaseModel):
    date: date
    name: str
    local_name: str | None = None


class PublicHoliday(PublicHolidayBase):
    id: int


class OrthodoxHolidayBase(CustomBaseModel):
    date: date
    name: str
    local_name: str | None = None
    is_fixed: bool


class OrthodoxHoliday(OrthodoxHolidayBase):
    id: int
