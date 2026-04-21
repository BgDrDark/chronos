from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Gateway, Terminal, TerminalSession, GatewayHeartbeat
from .base import BaseRepository


class AccessRepository(BaseRepository):
    """Repository за контрол на достъп"""
    
    model = Gateway
    
    async def get_online_gateways(
        self,
        db: AsyncSession,
        company_id: int = None
    ) -> List[Gateway]:
        """Връща онлайн gateway-ове"""
        query = select(Gateway).where(Gateway.is_online == True)
        
        if company_id:
            query = query.where(Gateway.company_id == company_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_active_sessions(
        self,
        db: AsyncSession,
        terminal_id: int = None
    ) -> List[TerminalSession]:
        """Връща активни терминални сесии"""
        query = select(TerminalSession).where(TerminalSession.end_time == None)
        
        if terminal_id:
            query = query.where(TerminalSession.terminal_id == terminal_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_terminal_by_id(self, db: AsyncSession, terminal_id: int) -> Optional[Terminal]:
        """Връща терминал по ID"""
        result = await db.execute(
            select(Terminal).where(Terminal.id == terminal_id)
        )
        return result.scalar_one_or_none()
    
    async def get_terminals_by_company(
        self,
        db: AsyncSession,
        company_id: int
    ) -> List[Terminal]:
        """Връща терминалите на компанията"""
        result = await db.execute(
            select(Terminal).where(Terminal.company_id == company_id)
        )
        return list(result.scalars().all())
    
    async def get_gateways_by_company(
        self,
        db: AsyncSession,
        company_id: int
    ) -> List[Gateway]:
        """Връща gateway-овете на компанията"""
        result = await db.execute(
            select(Gateway).where(Gateway.company_id == company_id)
        )
        return list(result.scalars().all())
    
    async def get_gateway_heartbeats(
        self,
        db: AsyncSession,
        gateway_id: int,
        limit: int = 10
    ) -> List[GatewayHeartbeat]:
        """Връща последните heartbeats за gateway"""
        result = await db.execute(
            select(GatewayHeartbeat)
            .where(GatewayHeartbeat.gateway_id == gateway_id)
            .order_by(GatewayHeartbeat.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


access_repo = AccessRepository()