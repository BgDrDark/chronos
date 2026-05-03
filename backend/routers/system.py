from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import date
from typing import List
import json
import logging

from backend.config import settings
from backend.auth.jwt_utils import get_current_user
from backend.database import models
from backend.services.backup_service import BackupService, json_serial
from backend.services.module_service import ModuleService
from backend import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

# --- Dependencies ---

def ensure_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )
    return current_user

# --- Synchronous DB Setup for Backup/Restore ---
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg")
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Module Management ---

@router.get("/modules", response_model=List[schemas.Module])
async def get_modules(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Списък с всички системни модули"""
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Само Admin/Super Admin може да управлява модули")
    
    return await ModuleService.get_all_modules(db)

@router.patch("/modules/{code}", response_model=schemas.Module)
async def update_module(
    code: str,
    module_in: schemas.ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Включване/изключване на модул"""
    if current_user.role.name not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Само Admin/Super Admin може да управлява модули")
    
    success = await ModuleService.toggle_module(db, code, module_in.is_enabled)
    if not success:
        raise HTTPException(status_code=404, detail="Модулът не е намерен")
    
    # Force clear cache and fetch fresh
    ModuleService.clear_cache()
    # Expire all cached objects to ensure fresh fetch
    db.expire_all()
    from sqlalchemy import select
    res = await db.execute(select(models.Module).where(models.Module.code == code))
    db_module = res.scalar_one()
    await db.refresh(db_module)
    return db_module

@router.get("/password-settings", response_model=schemas.PasswordSettings)
async def get_password_settings(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Вземане на текущите настройки за сложност на паролите"""
    if current_user.role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Само Super Admin може да управлява настройки за пароли")
    
    from backend import crud
    return schemas.PasswordSettings(
        min_length=int(await crud.get_global_setting(db, "pwd_min_length") or "8"),
        max_length=int(await crud.get_global_setting(db, "pwd_max_length") or "32"),
        require_upper=(await crud.get_global_setting(db, "pwd_require_upper")) == "true",
        require_lower=(await crud.get_global_setting(db, "pwd_require_lower")) == "true",
        require_digit=(await crud.get_global_setting(db, "pwd_require_digit")) == "true",
        require_special=(await crud.get_global_setting(db, "pwd_require_special")) == "true"
    )

@router.patch("/password-settings", response_model=schemas.PasswordSettings)
async def update_password_settings(
    settings_in: schemas.PasswordSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Обновяване на настройките за сложност на паролите"""
    if current_user.role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Само Super Admin може да управлява настройки за пароли")
    
    from backend import crud
    await crud.set_global_setting(db, "pwd_min_length", str(settings_in.min_length))
    await crud.set_global_setting(db, "pwd_max_length", str(settings_in.max_length))
    await crud.set_global_setting(db, "pwd_require_upper", "true" if settings_in.require_upper else "false")
    await crud.set_global_setting(db, "pwd_require_lower", "true" if settings_in.require_lower else "false")
    await crud.set_global_setting(db, "pwd_require_digit", "true" if settings_in.require_digit else "false")
    await crud.set_global_setting(db, "pwd_require_special", "true" if settings_in.require_special else "false")
    
    # Increment password settings version
    current_version = int(await crud.get_global_setting(db, "password_settings_version") or "0")
    await crud.set_global_setting(db, "password_settings_version", str(current_version + 1))

    # Set password_force_change to True for all users
    await crud.force_password_change_for_all_users(db)
    
    await db.commit()
    return settings_in

@router.post("/kiosk-background")
async def upload_kiosk_background(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Качване на фоново изображение за Kiosk терминала"""
    if current_user.role.name != "super_admin":
        raise HTTPException(status_code=403, detail="Само Super Admin може да променя фона на терминала")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файлът трябва да бъде изображение.")

    import os
    import uuid
    from PIL import Image
    import io
    from backend.routers.documents import UPLOAD_DIR
    from backend import crud

    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # Optional: Resize if too large (e.g., max 1920 width)
    if image.width > 1920:
        ratio = 1920 / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((1920, new_height), Image.LANCZOS)

    filename = f"kiosk_bg_{uuid.uuid4().hex[:8]}.webp"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    image.save(file_path, "WEBP", quality=80)

    # Save to global settings
    old_bg = await crud.get_global_setting(db, "kiosk_background_image")
    if old_bg:
        old_path = os.path.join(UPLOAD_DIR, old_bg)
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass

    await crud.set_global_setting(db, "kiosk_background_image", filename)
    return {"status": "success", "filename": filename}

# --- Backup / Restore / Archive ---

@router.get("/backup")
def download_backup(
    sync_db: Session = Depends(get_sync_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Downloads a full backup of the database as a JSON file."""
    try:
        data = BackupService.create_backup(sync_db)
        json_str = json.dumps(data, default=json_serial, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=chronos_backup_{data['metadata']['timestamp']}.json"}
        )
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    sync_db: Session = Depends(get_sync_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Restores the database from a JSON backup file. WARNING: Wipes current data."""
    try:
        content = await file.read()
        data = json.loads(content)
        BackupService.restore_backup(sync_db, data)
        return {"message": "Database restored successfully"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        logging.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.post("/archive")
def archive_data(
    cutoff_date: date,
    sync_db: Session = Depends(get_sync_db),
    current_user: models.User = Depends(ensure_admin)
):
    """Archives and deletes transactional data older than cutoff_date."""
    try:
        data = BackupService.archive_old_data(sync_db, cutoff_date)
        json_str = json.dumps(data, default=json_serial, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=chronos_archive_{cutoff_date}.json"}
        )
    except Exception as e:
        logging.error(f"Archive failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
