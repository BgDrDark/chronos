
import strawberry


@strawberry.input
class CostCenterInput:
    name: str
    department_id: int | None = None
    is_active: bool | None = True
    company_id: int


@strawberry.input
class UpdateCostCenterInput:
    id: int
    name: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
