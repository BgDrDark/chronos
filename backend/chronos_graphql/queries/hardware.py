
import strawberry
from sqlalchemy import func, select

from backend.exceptions import AuthenticationException
from backend.chronos_graphql import types

authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class HardwareQuery:

    @strawberry.field
    async def gateways(self, info: strawberry.Info, is_active: bool | None = None) -> list[types.Gateway]:
        """Get all gateways"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Gateway
        stmt = select(Gateway)

        if current_user.role.name != "super_admin":
            stmt = stmt.where(Gateway.company_id == current_user.company_id)

        if is_active is not None:
            stmt = stmt.where(Gateway.is_active == is_active)

        stmt = stmt.order_by(Gateway.registered_at.desc())

        res = await db.execute(stmt)
        return [types.Gateway.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def gateway(self, info: strawberry.Info, id: int) -> types.Gateway | None:
        """Get a single gateway by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Gateway
        gateway = await db.get(Gateway, id)
        if not gateway:
            return None

        return types.Gateway.from_pydantic(gateway)

    @strawberry.field
    async def terminals(
        self,
        info: strawberry.Info,
        gateway_id: int | None = None,
        is_active: bool | None = None,
    ) -> list[types.Terminal]:
        """Get all terminals"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Gateway, Terminal
        stmt = select(Terminal)

        # Filter by company via Gateway, but ALWAYS allow terminals without gateway
        if current_user.role.name != "super_admin":
            from sqlalchemy import or_
            stmt = stmt.outerjoin(Gateway).where(
                or_(Gateway.company_id == current_user.company_id, Terminal.gateway_id is None),
            )

        if gateway_id is not None:
            stmt = stmt.where(Terminal.gateway_id == gateway_id)
        if is_active is not None:
            stmt = stmt.where(Terminal.is_active == is_active)

        stmt = stmt.order_by(Terminal.last_seen.desc())

        res = await db.execute(stmt)
        return [types.Terminal.from_pydantic(i) for i in res.scalars().all()]

    @strawberry.field
    async def terminal(self, info: strawberry.Info, id: int) -> types.Terminal | None:
        """Get a single terminal by ID"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if not terminal:
            return None

        return types.Terminal.from_pydantic(terminal)

    @strawberry.field
    async def gateway_stats(self, info: strawberry.Info) -> types.GatewayStats:
        """Get gateway statistics"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)
        if current_user.role.name != "super_admin":
            raise AuthenticationException

        from backend.database.models import Gateway, Printer, Terminal

        total_gateways = await db.scalar(select(func.count(Gateway.id)))
        active_gateways = await db.scalar(select(func.count(Gateway.id)).where(Gateway.is_active))
        inactive_gateways = await db.scalar(select(func.count(Gateway.id)).where(not Gateway.is_active))

        total_terminals = await db.scalar(select(func.count(Terminal.id)))
        active_terminals = await db.scalar(select(func.count(Terminal.id)).where(Terminal.is_active))

        total_printers = await db.scalar(select(func.count(Printer.id)))
        active_printers = await db.scalar(select(func.count(Printer.id)).where(Printer.is_active))

        return types.GatewayStats(
            total_gateways=total_gateways or 0,
            active_gateways=active_gateways or 0,
            inactive_gateways=inactive_gateways or 0,
            total_terminals=total_terminals or 0,
            active_terminals=active_terminals or 0,
            total_printers=total_printers or 0,
            active_printers=active_printers or 0,
        )

    @strawberry.field
    async def printers(self, info: strawberry.Info, gateway_id: int) -> list[types.Printer]:
        """Get all printers for a gateway"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user: raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Printer
        stmt = select(Printer).where(Printer.gateway_id == gateway_id)
        stmt = stmt.order_by(Printer.is_default.desc(), Printer.name)

        res = await db.execute(stmt)
        return [types.Printer.from_pydantic(i) for i in res.scalars().all()]
