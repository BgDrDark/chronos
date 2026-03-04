from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import asyncio

from backend.database.database import get_db
from backend.database.models import (
    TerminalSession, ProductionTaskLog, User, Workstation,
    ProductionOrder, ProductionTask
)
from backend.auth.qr_utils import verify_dynamic_qr_token
from backend.auth.module_guard import require_module

router = APIRouter(prefix="/terminal", tags=["terminal"])


class TerminalIdentifyRequest(BaseModel):
    qr_token: str


class TerminalIdentifyResponse(BaseModel):
    employee_id: int
    first_name: str
    last_name: str
    profile_picture: Optional[str]


class TerminalSessionStart(BaseModel):
    terminal_id: str
    workstation_id: int


class TerminalSessionEnd(BaseModel):
    terminal_id: str


class TerminalTaskStart(BaseModel):
    terminal_id: str
    order_id: int
    task_id: int


class TerminalTaskComplete(BaseModel):
    terminal_id: str
    task_id: int
    quantity_produced: int = 0
    scrap_quantity: int = 0


class TerminalTaskScrap(BaseModel):
    terminal_id: str
    task_id: int
    scrap_quantity: int


class WorkstationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_number: str
    product_name: str
    quantity: int
    status: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    recipe_name: str
    quantity: int
    status: str

    class Config:
        from_attributes = True


@router.post("/identify", response_model=TerminalIdentifyResponse)
@require_module("confectionery")
async def identify_terminal(
    request: TerminalIdentifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Идентификация на служител чрез QR код.
    QR формат: {user_id}:{dynamic_token}
    """
    
    user = None
    
    if ":" in request.qr_token:
        try:
            user_id_str, token = request.qr_token.split(":")
            user_id = int(user_id_str)
            user = await db.get(User, user_id)
            if user and user.qr_secret:
                if not verify_dynamic_qr_token(user.qr_secret, token):
                    user = None
        except:
            user = None
    
    if not user:
        user = await db.execute(
            select(User).where(User.username == request.qr_token)
        )
        user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Невалиден или изтекъл QR код")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Акаунтът е деактивиран")
    
    profile_pic = user.profile_picture
    if profile_pic and not profile_pic.startswith('http') and not profile_pic.startswith('/'):
        profile_pic = f"/uploads/{profile_pic}"
    
    return TerminalIdentifyResponse(
        employee_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        profile_picture=profile_pic
    )


@router.get("/workstations", response_model=List[WorkstationResponse])
@require_module("confectionery")
async def get_workstations(
    db: AsyncSession = Depends(get_db)
):
    """Списък с всички работни станции"""
    
    result = await db.execute(
        select(Workstation).where(Workstation.is_active == True)
    )
    return result.scalars().all()


@router.get("/workstations/{workstation_id}/orders", response_model=List[OrderResponse])
@require_module("confectionery")
async def get_orders_for_workstation(
    workstation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Поръчки за конкретна станция"""
    
    result = await db.execute(
        select(ProductionOrder)
        .where(ProductionOrder.workstation_id == workstation_id)
        .where(ProductionOrder.status.in_(["in_progress", "ready", "pending"]))
        .order_by(ProductionOrder.created_at.desc())
    )
    return result.scalars().all()


@router.get("/orders/{order_id}/tasks", response_model=List[TaskResponse])
@require_module("confectionery")
async def get_tasks_for_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Задачи за конкретна поръчка"""
    
    result = await db.execute(
        select(ProductionTask)
        .where(ProductionTask.production_order_id == order_id)
        .where(ProductionTask.status.in_(["pending", "in_progress"]))
    )
    return result.scalars().all()


@router.post("/session/start")
async def start_session(
    session: TerminalSessionStart,
    db: AsyncSession = Depends(get_db)
):
    """Старт на сесия - служителят избира станция"""
    
    new_session = TerminalSession(
        terminal_id=session.terminal_id,
        employee_id=session.employee_id,
        workstation_id=session.workstation_id,
        started_at=datetime.utcnow()
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return {
        "status": "started",
        "session_id": new_session.id,
        "workstation_id": session.workstation_id
    }


@router.post("/session/end")
async def end_session(
    session: TerminalSessionEnd,
    db: AsyncSession = Depends(get_db)
):
    """Край на сесията"""
    
    result = await db.execute(
        select(TerminalSession)
        .where(TerminalSession.terminal_id == session.terminal_id)
        .where(TerminalSession.ended_at == None)
    )
    current_session = result.scalar_one_or_none()
    
    if not current_session:
        raise HTTPException(status_code=404, detail="Няма активна сесия")
    
    current_session.ended_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "ended"}


@router.get("/session/status")
async def get_session_status(
    terminal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Текуща сесия на терминала"""
    
    result = await db.execute(
        select(TerminalSession)
        .where(TerminalSession.terminal_id == terminal_id)
        .where(TerminalSession.ended_at == None)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return {"active": False}
    
    return {
        "active": True,
        "session_id": session.id,
        "employee_id": session.employee_id,
        "workstation_id": session.workstation_id,
        "started_at": session.started_at
    }


@router.post("/task/start")
async def start_task(
    task_start: TerminalTaskStart,
    db: AsyncSession = Depends(get_db)
):
    """Старт на задача"""
    
    result = await db.execute(
        select(TerminalSession)
        .where(TerminalSession.terminal_id == task_start.terminal_id)
        .where(TerminalSession.ended_at == None)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=400, detail="Няма активна сесия")
    
    task_log = ProductionTaskLog(
        session_id=session.id,
        production_order_id=task_start.order_id,
        production_task_id=task_start.task_id,
        started_at=datetime.utcnow(),
        status="in_progress"
    )
    
    db.add(task_log)
    await db.commit()
    await db.refresh(task_log)
    
    return {
        "status": "started",
        "task_log_id": task_log.id
    }


@router.post("/task/complete")
async def complete_task(
    task_complete: TerminalTaskComplete,
    db: AsyncSession = Depends(get_db)
):
    """Завършване на задача"""
    
    result = await db.execute(
        select(ProductionTaskLog).where(ProductionTaskLog.id == task_complete.task_id)
    )
    task_log = result.scalar_one_or_none()
    
    if not task_log:
        raise HTTPException(status_code=404, detail="Задача не е намерен")
    
    task_log.completed_at = datetime.utcnow()
    task_log.quantity_produced = task_complete.quantity_produced
    task_log.scrap_quantity = task_complete.scrap_quantity
    task_log.status = "completed"
    
    await db.commit()
    
    return {
        "status": "completed",
        "quantity_produced": task_complete.quantity_produced,
        "scrap_quantity": task_complete.scrap_quantity
    }


@router.post("/task/scrap")
async def add_scrap(
    scrap: TerminalTaskScrap,
    db: AsyncSession = Depends(get_db)
):
    """Добавяне на брак"""
    
    result = await db.execute(
        select(ProductionTaskLog).where(ProductionTaskLog.id == scrap.task_id)
    )
    task_log = result.scalar_one_or_none()
    
    if not task_log:
        raise HTTPException(status_code=404, detail="Задача не е намерен")
    
    task_log.scrap_quantity = (task_log.scrap_quantity or 0) + scrap.scrap_quantity
    
    await db.commit()
    
    return {
        "status": "scrap_added",
        "scrap_quantity": task_log.scrap_quantity
    }


@router.get("/sessions")
@require_module("confectionery")
async def get_sessions(
    terminal_id: Optional[str] = None,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """История на сесиите (за админ)"""
    
    query = select(TerminalSession)
    
    if terminal_id:
        query = query.where(TerminalSession.terminal_id == terminal_id)
    
    query = query.order_by(TerminalSession.started_at.desc()).limit(100)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "terminal_id": s.terminal_id,
            "employee_id": s.employee_id,
            "workstation_id": s.workstation_id,
            "started_at": s.started_at,
            "ended_at": s.ended_at,
        }
        for s in sessions
    ]
