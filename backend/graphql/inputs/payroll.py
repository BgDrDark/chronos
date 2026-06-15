import datetime
from decimal import Decimal

import strawberry


@strawberry.input
class BonusCreateInput:
    user_id: int
    amount: Decimal
    date: datetime.date
    description: str | None = None


@strawberry.input
class CreatePaymentBatchInput:
    company_id: int
    period_start: datetime.date
    period_end: datetime.date
    payment_date: datetime.datetime
    payment_method: str = "bank"
    payment_reference: str | None = None
    notes: str | None = None


@strawberry.input
class AddItemsToBatchInput:
    batch_id: int
    user_ids: list[int]
