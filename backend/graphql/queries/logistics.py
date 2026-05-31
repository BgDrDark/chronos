import datetime
from decimal import Decimal

import strawberry
from sqlalchemy import func, select

from backend.exceptions import AuthenticationException
from backend.graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class LogisticsQuery:

    @strawberry.field
    async def storage_zones(self, info: strawberry.Info) -> list[types.StorageZone]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import StorageZone
        stmt = select(StorageZone)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(StorageZone.company_id == current_user.company_id)

        res = await db.execute(stmt)
        return [types.StorageZone.from_pydantic(z) for z in res.scalars().all()]

    @strawberry.field
    async def suppliers(self, info: strawberry.Info) -> list[types.Supplier]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Supplier
        stmt = select(Supplier)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Supplier.company_id == current_user.company_id)

        res = await db.execute(stmt)
        return [types.Supplier.from_pydantic(s) for s in res.scalars().all()]

    @strawberry.field
    async def ingredients(self, info: strawberry.Info, search: str | None = None) -> list[types.Ingredient]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Ingredient
        stmt = select(Ingredient)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)

        if search:
            stmt = stmt.where(Ingredient.name.ilike(f"%{search}%"))

        res = await db.execute(stmt)
        return [types.Ingredient.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def batches(
        self,
        info: strawberry.Info,
        ingredient_id: int | None = None,
        status: str | None = "active",
    ) -> list[types.Batch]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Batch, Ingredient
        stmt = select(Batch).join(Ingredient)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)

        if ingredient_id:
            stmt = stmt.where(Batch.ingredient_id == ingredient_id)
        if status:
            stmt = stmt.where(Batch.status == status)
        stmt = stmt.order_by(Batch.expiry_date.asc())
        res = await db.execute(stmt)
        return [types.Batch.from_pydantic(b) for b in res.scalars().all()]

    @strawberry.field
    async def get_fefo_suggestion(
        self,
        ingredient_id: int,
        quantity: Decimal,
        info: strawberry.Info,
    ) -> list[types.FefoSuggestion]:
        db = info.context["db"]
        from backend.database.models import Batch

        stmt = select(Batch).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0,
        ).order_by(Batch.expiry_date.asc())

        result = await db.execute(stmt)
        batches = result.scalars().all()

        suggestions = []
        remaining = quantity
        today = datetime.date.today()

        for batch in batches:
            if remaining <= 0:
                break
            to_take = min(batch.quantity, remaining)
            suggestions.append(types.FefoSuggestion(
                batch_id=batch.id,
                batch_number=batch.batch_number or f"ID-{batch.id}",
                available_quantity=batch.quantity,
                quantity_to_take=to_take,
                expiry_date=batch.expiry_date,
                days_until_expiry=(batch.expiry_date - today).days,
            ))
            remaining -= to_take

        return suggestions

    @strawberry.field
    async def stock_consumption_logs(
        self,
        info: strawberry.Info,
        ingredient_id: int | None = None,
        batch_id: int | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> list[types.StockConsumptionLog]:
        db = info.context["db"]
        from backend.database.models import StockConsumptionLog
        stmt = select(StockConsumptionLog)

        if ingredient_id:
            stmt = stmt.where(StockConsumptionLog.ingredient_id == ingredient_id)
        if batch_id:
            stmt = stmt.where(StockConsumptionLog.batch_id == batch_id)
        if start_date:
            stmt = stmt.where(StockConsumptionLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(StockConsumptionLog.created_at <= end_date)
        stmt = stmt.order_by(StockConsumptionLog.created_at.desc())
        result = await db.execute(stmt)
        logs = result.scalars().all()
        return [types.StockConsumptionLog.from_instance(item) for item in logs]

    @strawberry.field
    async def ingredient_batches_with_stock(
        self,
        info: strawberry.Info,
        ingredient_id: int,
    ) -> list[types.Batch]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Batch, Ingredient
        stmt = select(Batch).join(Ingredient).where(
            Batch.ingredient_id == ingredient_id,
            Batch.status == "active",
            Batch.quantity > 0,
        )

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Ingredient.company_id == current_user.company_id)

        stmt = stmt.order_by(Batch.expiry_date.asc())

        res = await db.execute(stmt)
        return [types.Batch.from_pydantic(b) for b in res.scalars().all()]

    @strawberry.field
    async def inventory_sessions(self, info: strawberry.Info, status: str | None = None) -> list[types.InventorySession]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import InventorySession
        stmt = select(InventorySession)
        if current_user.role.name != "super_admin":
            stmt = stmt.where(InventorySession.company_id == current_user.company_id)

        if status:
            stmt = stmt.where(InventorySession.status == status)

        stmt = stmt.order_by(InventorySession.started_at.desc())

        res = await db.execute(stmt)
        return [types.InventorySession.from_instance(s) for s in res.scalars().all()]

    @strawberry.field
    async def inventory_session_items(self, session_id: int, info: strawberry.Info) -> list[types.InventoryItem]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import InventoryItem, InventorySession

        session = await db.get(InventorySession, session_id)
        if not session:
            return []
        if current_user.role.name != "super_admin" and session.company_id != current_user.company_id:
            return []

        stmt = select(InventoryItem).where(InventoryItem.session_id == session_id)
        res = await db.execute(stmt)
        return [types.InventoryItem.from_instance(i) for i in res.scalars().all()]

    @strawberry.field
    async def inventory_by_barcode(self, barcode: str, info: strawberry.Info) -> types.InventoryItem | None:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail="Трябва да се автентикирате")

        from backend.database.models import Batch, Ingredient

        stmt = select(Ingredient).where(Ingredient.barcode == barcode)
        res = await db.execute(stmt)
        ingredient = res.scalars().first()
        if not ingredient:
            return None

        stmt = select(func.coalesce(func.sum(Batch.quantity), 0)).where(
            Batch.ingredient_id == ingredient.id,
            Batch.status == "active",
        )
        res = await db.execute(stmt)
        system_qty = Decimal(res.scalar() or 0)

        return types.InventoryItem(
            id=0,
            session_id=0,
            ingredient_id=ingredient.id,
            ingredient_name=ingredient.name,
            ingredient_unit=ingredient.unit,
            found_quantity=None,
            system_quantity=system_qty,
            difference=None,
            adjusted=False,
        )
