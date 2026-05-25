import strawberry
from sqlalchemy import select

from backend.exceptions import AuthenticationException
from backend.graphql import types


@strawberry.type
class ProductionQuery:

    @strawberry.field
    async def recipes(self, info: strawberry.Info) -> list[types.Recipe]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Recipe
        stmt = select(Recipe)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Recipe.company_id == current_user.company_id)

        res = await db.execute(stmt)
        return [types.Recipe.from_pydantic(r) for r in res.scalars().all()]

    @strawberry.field
    async def recipes_with_prices(
        self,
        info: strawberry.Info,
        category_id: int | None = None,
    ) -> list[types.Recipe]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Recipe
        stmt = select(Recipe)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Recipe.company_id == current_user.company_id)

        if category_id:
            stmt = stmt.where(Recipe.category_id == category_id)

        res = await db.execute(stmt)
        return [types.Recipe.from_pydantic(r) for r in res.scalars().all()]

    @strawberry.field
    async def price_history(
        self,
        info: strawberry.Info,
        recipe_id: int,
        limit: int = 20,
    ) -> list[types.PriceHistory]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Трябва да се автентикирате")

        from sqlalchemy import desc

        from backend.database.models import PriceHistory, Recipe

        recipe = await db.get(Recipe, recipe_id)
        if not recipe or recipe.company_id != current_user.company_id:
            from backend.exceptions import NotFoundException
            raise NotFoundException.record("Recipe")

        stmt = select(PriceHistory).where(
            PriceHistory.recipe_id == recipe_id,
        ).order_by(desc(PriceHistory.changed_at)).limit(limit)

        res = await db.execute(stmt)
        return [types.PriceHistory.from_pydantic(h) for h in res.scalars().all()]

    @strawberry.field
    async def workstations(self, info: strawberry.Info) -> list[types.Workstation]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Workstation
        stmt = select(Workstation)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Workstation.company_id == current_user.company_id)

        res = await db.execute(stmt)
        return [types.Workstation.from_pydantic(w) for w in res.scalars().all()]

    @strawberry.field
    async def production_orders(self, info: strawberry.Info, status: str | None = None) -> list[types.ProductionOrder]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import ProductionOrder
        stmt = select(ProductionOrder)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)

        if status:
            stmt = stmt.where(ProductionOrder.status == status)

        stmt = stmt.order_by(ProductionOrder.due_date.asc())

        res = await db.execute(stmt)
        return [types.ProductionOrder.from_pydantic(o) for o in res.scalars().all()]

    @strawberry.field
    async def terminal_orders(self, info: strawberry.Info, workstation_id: int) -> list[types.TerminalOrder]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import ProductionOrder, ProductionTask, Recipe
        stmt = select(ProductionOrder).where(
            ProductionOrder.status.in_(["in_progress", "ready", "pending"]),
        )

        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)

        stmt = stmt.order_by(ProductionOrder.created_at.desc()).limit(50)

        res = await db.execute(stmt)
        orders = []

        for order in res.scalars().all():
            recipe = await db.get(Recipe, order.recipe_id) if order.recipe_id else None

            task_stmt = select(ProductionTask).where(
                ProductionTask.order_id == order.id,
                ProductionTask.workstation_id == workstation_id,
                ProductionTask.status.in_(["pending", "in_progress"]),
            )
            task_res = await db.execute(task_stmt)
            order_qty = int(order.quantity) if order.quantity else 0
            tasks = [types.TerminalTask.from_instance(t, order_qty) for t in task_res.scalars().all()]

            if tasks:
                orders.append(types.TerminalOrder.from_instance(
                    order,
                    recipe_name=recipe.name if recipe else "Unknown",
                    instructions=recipe.instructions if recipe else None,
                    tasks=tasks,
                ))

        return orders

    @strawberry.field
    async def production_records(self, info: strawberry.Info, order_id: int | None = None) -> list[types.ProductionRecord]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import ProductionRecord
        stmt = select(ProductionRecord)
        if current_user.role.name != "super_admin":
            from backend.database.models import ProductionOrder
            stmt = stmt.join(ProductionOrder).where(ProductionOrder.company_id == current_user.company_id)

        if order_id:
            stmt = stmt.where(ProductionRecord.order_id == order_id)

        stmt = stmt.order_by(ProductionRecord.confirmed_at.desc())

        res = await db.execute(stmt)
        return [types.ProductionRecord.from_pydantic(r) for r in res.scalars().all()]

    @strawberry.field
    async def production_record_by_order(self, order_id: int, info: strawberry.Info) -> types.ProductionRecord | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import ProductionOrder, ProductionRecord
        stmt = select(ProductionRecord).where(ProductionRecord.order_id == order_id)

        if current_user.role.name != "super_admin":
            stmt = stmt.join(ProductionOrder).where(ProductionOrder.company_id == current_user.company_id)

        res = await db.execute(stmt)
        record = res.scalars().first()
        if not record:
            return None
        return types.ProductionRecord.from_pydantic(record)

    @strawberry.field
    async def production_orders_for_day(
        self,
        info: strawberry.Info,
        date: str | None = None,
    ) -> list[types.ProductionOrder]:
        """Get production orders for a specific day (by production_deadline)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()

        from datetime import datetime

        from backend.database.models import ProductionOrder

        target_date = datetime.now().date()
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())

        stmt = select(ProductionOrder).where(
            ProductionOrder.production_deadline >= start_of_day,
            ProductionOrder.production_deadline <= end_of_day,
            ProductionOrder.status.in_(["ready", "in_progress", "pending"]),
        )

        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)

        stmt = stmt.order_by(ProductionOrder.production_deadline.asc())

        res = await db.execute(stmt)
        return [types.ProductionOrder.from_pydantic(o) for o in res.scalars().all()]

    @strawberry.field
    async def overdue_production_orders(
        self,
        info: strawberry.Info,
    ) -> list[types.ProductionOrder]:
        """Get overdue production orders (production_deadline < now)"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException()

        from datetime import datetime

        from backend.database.models import ProductionOrder

        now = datetime.now()

        stmt = select(ProductionOrder).where(
            ProductionOrder.production_deadline < now,
            ProductionOrder.status.in_(["ready", "in_progress", "pending"]),
        )

        if current_user.role.name != "super_admin":
            stmt = stmt.where(ProductionOrder.company_id == current_user.company_id)

        stmt = stmt.order_by(ProductionOrder.production_deadline.asc())

        res = await db.execute(stmt)
        return [types.ProductionOrder.from_pydantic(o) for o in res.scalars().all()]
