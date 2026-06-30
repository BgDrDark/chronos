import strawberry


@strawberry.input
class MonthlyWorkDaysInput:
    year: int
    month: int
    days_count: int
