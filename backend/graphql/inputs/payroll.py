import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class BonusCreateInput:
    user_id: int
    amount: Decimal
    date: datetime.date
    description: str | None = None
