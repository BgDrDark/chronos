import datetime

import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@sp.type(schemas.PublicHoliday)
class PublicHoliday:
    id: strawberry.auto
    date: strawberry.auto
    name: strawberry.auto
    local_name: strawberry.auto


@sp.type(schemas.OrthodoxHoliday)
class OrthodoxHoliday:
    id: strawberry.auto
    date: strawberry.auto
    name: strawberry.auto
    local_name: strawberry.auto
    is_fixed: strawberry.auto
