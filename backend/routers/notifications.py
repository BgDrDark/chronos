from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.database.database import get_db
from backend.auth.jwt_utils import get_current_user
from backend.database import models
from backend import schemas, crud
from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(require_module_dep("notifications"))]
)

def ensure_super_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role.name != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Само Super Admin може да конфигурира системни уведомления"
        )
    return current_user

@router.get("/smtp", response_model=schemas.SmtpSettings)
async def get_smtp_settings(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_super_admin)
):
    """Вземане на SMTP настройките (преместено от системни)"""
    server = await crud.get_global_setting(db, "smtp_server")
    port = await crud.get_global_setting(db, "smtp_port")
    username = await crud.get_global_setting(db, "smtp_username")
    password = await crud.get_global_setting(db, "smtp_password") 
    sender = await crud.get_global_setting(db, "sender_email")
    tls = await crud.get_global_setting(db, "use_tls")

    return schemas.SmtpSettings(
        smtp_server=server or "",
        smtp_port=int(port) if port else 587,
        smtp_username=username or "",
        smtp_password=password or "",
        sender_email=sender or "",
        use_tls=tls == "True"
    )

@router.patch("/smtp", response_model=schemas.SmtpSettings)
async def update_smtp_settings(
    settings_in: schemas.SmtpSettings,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_super_admin)
):
    """Обновяване на SMTP настройките"""
    await crud.set_global_setting(db, "smtp_server", settings_in.smtp_server)
    await crud.set_global_setting(db, "smtp_port", str(settings_in.smtp_port))
    await crud.set_global_setting(db, "smtp_username", settings_in.smtp_username)
    await crud.set_global_setting(db, "smtp_password", settings_in.smtp_password)
    await crud.set_global_setting(db, "sender_email", settings_in.sender_email)
    await crud.set_global_setting(db, "use_tls", "True" if settings_in.use_tls else "False")
    
    await db.commit()
    return settings_in
