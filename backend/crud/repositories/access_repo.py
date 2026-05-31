from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    AccessCode,
    AccessDoor,
    AccessLog,
    AccessZone,
    Gateway,
    GatewayHeartbeat,
    Printer,
    Terminal,
    TerminalSession,
)

from .base import BaseRepository


class AccessRepository(BaseRepository):
    """Repository за контрол на достъп"""

    model = Gateway

    # ────────────────────────────── Gateway ──────────────────────────────

    async def create_gateway(self, db: AsyncSession, **kwargs) -> Gateway:
        instance = Gateway(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_gateway(self, db: AsyncSession, id: int, **kwargs) -> Gateway | None:
        instance = await self.get_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_gateway(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_online_gateways(
        self,
        db: AsyncSession,
        company_id: int = None,
    ) -> list[Gateway]:
        query = select(Gateway).where(Gateway.is_online)

        if company_id:
            query = query.where(Gateway.company_id == company_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_gateways_by_company(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[Gateway]:
        result = await db.execute(
            select(Gateway).where(Gateway.company_id == company_id),
        )
        return list(result.scalars().all())

    async def get_gateway_by_uuid(
        self,
        db: AsyncSession,
        hardware_uuid: str,
    ) -> Gateway | None:
        result = await db.execute(
            select(Gateway).where(Gateway.hardware_uuid == hardware_uuid),
        )
        return result.scalar_one_or_none()

    # ────────────────────────────── Terminal ──────────────────────────────

    async def create_terminal(self, db: AsyncSession, **kwargs) -> Terminal:
        instance = Terminal(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_terminal(self, db: AsyncSession, id: int, **kwargs) -> Terminal | None:
        instance = await self.get_terminal_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_terminal(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_terminal_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_terminal_by_id(self, db: AsyncSession, terminal_id: int) -> Terminal | None:
        result = await db.execute(
            select(Terminal).where(Terminal.id == terminal_id),
        )
        return result.scalar_one_or_none()

    async def get_terminals_by_gateway(
        self,
        db: AsyncSession,
        gateway_id: int,
    ) -> list[Terminal]:
        result = await db.execute(
            select(Terminal).where(Terminal.gateway_id == gateway_id),
        )
        return list(result.scalars().all())

    async def get_terminals_by_company(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[Terminal]:
        result = await db.execute(
            select(Terminal).where(Terminal.company_id == company_id),
        )
        return list(result.scalars().all())

    async def get_terminal_by_uuid(
        self,
        db: AsyncSession,
        hardware_uuid: str,
    ) -> Terminal | None:
        result = await db.execute(
            select(Terminal).where(Terminal.hardware_uuid == hardware_uuid),
        )
        return result.scalar_one_or_none()

    # ────────────────────────────── Printer ──────────────────────────────

    async def create_printer(self, db: AsyncSession, **kwargs) -> Printer:
        instance = Printer(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_printer(self, db: AsyncSession, id: int, **kwargs) -> Printer | None:
        instance = await self.get_printer_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_printer(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_printer_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_printer_by_id(self, db: AsyncSession, id: int) -> Printer | None:
        result = await db.execute(
            select(Printer).where(Printer.id == id),
        )
        return result.scalar_one_or_none()

    async def get_printers_by_gateway(
        self,
        db: AsyncSession,
        gateway_id: int,
    ) -> list[Printer]:
        result = await db.execute(
            select(Printer).where(Printer.gateway_id == gateway_id),
        )
        return list(result.scalars().all())

    # ────────────────────────────── AccessZone ──────────────────────────────

    async def create_access_zone(self, db: AsyncSession, **kwargs) -> AccessZone:
        instance = AccessZone(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_access_zone(self, db: AsyncSession, id: int, **kwargs) -> AccessZone | None:
        instance = await self.get_access_zone_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_access_zone(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_access_zone_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_access_zone_by_id(self, db: AsyncSession, id: int) -> AccessZone | None:
        result = await db.execute(
            select(AccessZone).where(AccessZone.id == id),
        )
        return result.scalar_one_or_none()

    async def get_access_zones_by_company(
        self,
        db: AsyncSession,
        company_id: int,
    ) -> list[AccessZone]:
        result = await db.execute(
            select(AccessZone).where(AccessZone.company_id == company_id),
        )
        return list(result.scalars().all())

    # ────────────────────────────── AccessDoor ──────────────────────────────

    async def create_access_door(self, db: AsyncSession, **kwargs) -> AccessDoor:
        instance = AccessDoor(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update_access_door(self, db: AsyncSession, id: int, **kwargs) -> AccessDoor | None:
        instance = await self.get_access_door_by_id(db, id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.flush()
            await db.refresh(instance)
        return instance

    async def delete_access_door(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_access_door_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_access_door_by_id(self, db: AsyncSession, id: int) -> AccessDoor | None:
        result = await db.execute(
            select(AccessDoor)
            .options(selectinload(AccessDoor.zone), selectinload(AccessDoor.gateway))
            .where(AccessDoor.id == id),
        )
        return result.scalar_one_or_none()

    async def get_access_doors_by_gateway(
        self,
        db: AsyncSession,
        gateway_id: int,
    ) -> list[AccessDoor]:
        result = await db.execute(
            select(AccessDoor).where(AccessDoor.gateway_id == gateway_id),
        )
        return list(result.scalars().all())

    async def get_access_doors_by_zone(
        self,
        db: AsyncSession,
        zone_db_id: int,
    ) -> list[AccessDoor]:
        result = await db.execute(
            select(AccessDoor).where(AccessDoor.zone_db_id == zone_db_id),
        )
        return list(result.scalars().all())

    async def get_door_by_device_id(
        self,
        db: AsyncSession,
        device_id: str,
    ) -> AccessDoor | None:
        result = await db.execute(
            select(AccessDoor).where(AccessDoor.device_id == device_id),
        )
        return result.scalar_one_or_none()

    # ────────────────────────────── AccessCode ──────────────────────────────

    async def create_access_code(self, db: AsyncSession, **kwargs) -> AccessCode:
        instance = AccessCode(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def delete_access_code(self, db: AsyncSession, id: int) -> bool:
        instance = await self.get_access_code_by_id(db, id)
        if instance:
            await db.delete(instance)
            await db.flush()
            return True
        return False

    async def get_access_code_by_id(self, db: AsyncSession, id: int) -> AccessCode | None:
        result = await db.execute(
            select(AccessCode).where(AccessCode.id == id),
        )
        return result.scalar_one_or_none()

    async def get_access_codes_by_gateway(
        self,
        db: AsyncSession,
        gateway_id: int,
    ) -> list[AccessCode]:
        result = await db.execute(
            select(AccessCode).where(AccessCode.gateway_id == gateway_id),
        )
        return list(result.scalars().all())

    async def get_access_code_by_value(
        self,
        db: AsyncSession,
        code: str,
    ) -> AccessCode | None:
        result = await db.execute(
            select(AccessCode).where(AccessCode.code == code),
        )
        return result.scalar_one_or_none()

    # ────────────────────────────── AccessLog ──────────────────────────────

    async def create_access_log(self, db: AsyncSession, **kwargs) -> AccessLog:
        instance = AccessLog(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_access_logs(
        self,
        db: AsyncSession,
        gateway_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AccessLog]:
        result = await db.execute(
            select(AccessLog)
            .where(AccessLog.gateway_id == gateway_id)
            .order_by(AccessLog.timestamp.desc())
            .limit(limit)
            .offset(offset),
        )
        return list(result.scalars().all())

    async def get_access_logs_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
    ) -> list[AccessLog]:
        result = await db.execute(
            select(AccessLog)
            .where(AccessLog.user_id == str(user_id))
            .order_by(AccessLog.timestamp.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    async def get_access_logs_by_date_range(
        self,
        db: AsyncSession,
        gateway_id: int,
        start: datetime,
        end: datetime,
        limit: int = 100,
    ) -> list[AccessLog]:
        result = await db.execute(
            select(AccessLog)
            .where(
                AccessLog.gateway_id == gateway_id,
                AccessLog.timestamp >= start,
                AccessLog.timestamp <= end,
            )
            .order_by(AccessLog.timestamp.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    # ────────────────────────────── GatewayHeartbeat ──────────────────────────────

    async def create_heartbeat(self, db: AsyncSession, **kwargs) -> GatewayHeartbeat:
        instance = GatewayHeartbeat(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def get_gateway_heartbeats(
        self,
        db: AsyncSession,
        gateway_id: int,
        limit: int = 10,
    ) -> list[GatewayHeartbeat]:
        result = await db.execute(
            select(GatewayHeartbeat)
            .where(GatewayHeartbeat.gateway_id == gateway_id)
            .order_by(GatewayHeartbeat.timestamp.desc())
            .limit(limit),
        )
        return list(result.scalars().all())

    # ────────────────────────────── TerminalSession ──────────────────────────────

    async def create_terminal_session(self, db: AsyncSession, **kwargs) -> TerminalSession:
        instance = TerminalSession(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def end_terminal_session(
        self,
        db: AsyncSession,
        id: int,
        end_time: datetime = None,
    ) -> TerminalSession | None:
        instance = await db.execute(
            select(TerminalSession).where(TerminalSession.id == id),
        )
        instance = instance.scalar_one_or_none()
        if instance:
            instance.ended_at = end_time or datetime.utcnow()
            await db.flush()
            await db.refresh(instance)
        return instance

    async def get_active_sessions(
        self,
        db: AsyncSession,
        terminal_id: int = None,
    ) -> list[TerminalSession]:
        query = select(TerminalSession).where(TerminalSession.end_time.is_(None))

        if terminal_id:
            query = query.where(TerminalSession.terminal_id == terminal_id)

        result = await db.execute(query)
        return list(result.scalars().all())


access_repo = AccessRepository()
