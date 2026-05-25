import datetime

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@sp.type(schemas.VehicleCostCenter)
class VehicleCostCenter:
    id: strawberry.auto
    name: strawberry.auto
    department_id: strawberry.auto
    is_active: strawberry.auto
    company_id: strawberry.auto
    created_at: strawberry.auto
