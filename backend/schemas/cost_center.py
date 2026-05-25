from datetime import datetime

from backend.schemas.base import CustomBaseModel


class VehicleCostCenterBase(CustomBaseModel):
    name: str
    department_id: int | None = None
    is_active: bool | None = None
    company_id: int
    created_at: datetime | None = None


class VehicleCostCenter(VehicleCostCenterBase):
    id: int
