import os
import subprocess
import logging
import threading
import httpx
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from backend.config import settings
from backend.database.database import get_db
from backend.auth.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["deploy"])


class DeployRequest(BaseModel):
    version: Optional[str] = None


class DeployResponse(BaseModel):
    status: str
    commit: str
    branch: str = "main"
    message: str
    timestamp: str
    output: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    db_status: str = "unknown"
    maintenance_mode: bool = False


class DeployStatusResponse(BaseModel):
    is_deploying: bool
    status: str
    progress: str
    version: Optional[str] = None
    output: Optional[str] = None
    timestamp: Optional[str] = None


class MaintenanceModeResponse(BaseModel):
    enabled: bool
    reason: str = ""


_deploy_status = {
    "is_deploying": False,
    "status": "idle",
    "progress": "",
    "version": None,
    "output": "",
    "timestamp": None,
}

_deploy_lock = threading.Lock()

PROJECT_DIR = os.environ.get("PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


async def _set_maintenance_mode(db: AsyncSession, enabled: bool, reason: str = ""):
    """Set maintenance mode using pg_advisory_lock"""
    lock_id = 1234567890
    if enabled:
        await db.execute(text(f"SELECT pg_advisory_lock({lock_id})"))
        await db.execute(text(f"SELECT set_config('app.maintenance_reason', '{reason}', false)"))
    else:
        await db.execute(text(f"SELECT pg_advisory_unlock({lock_id})"))
    await db.commit()


async def _is_maintenance_mode(db: AsyncSession) -> bool:
    """Check if maintenance mode is active"""
    lock_id = 1234567890
    result = await db.execute(text(f"SELECT pg_try_advisory_lock({lock_id})"))
    locked = result.scalar()
    if locked:
        await db.execute(text(f"SELECT pg_advisory_unlock({lock_id})"))
        await db.commit()
        return False
    return True


async def _get_db_health(db: AsyncSession) -> dict:
    """Check database health including connection pool and active queries"""
    try:
        pool_result = await db.execute(text("""
            SELECT count(*) as total,
                   count(*) FILTER (WHERE state = 'active') as active,
                   count(*) FILTER (WHERE state = 'idle') as idle,
                   count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_txn
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))
        pool_stats = pool_result.fetchone()

        return {
            "status": "healthy",
            "total_connections": pool_stats[0],
            "active_queries": pool_stats[1],
            "idle_connections": pool_stats[2],
            "idle_in_transaction": pool_stats[3],
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def _wait_for_active_queries(db: AsyncSession, timeout: int = 30):
    """Wait for active queries to finish before shutdown"""
    import asyncio
    start = datetime.now()
    while (datetime.now() - start).seconds < timeout:
        health = await _get_db_health(db)
        if health.get("active_queries", 0) == 0:
            return True
        await asyncio.sleep(1)
    return False


def _update_deploy_status(status: str, progress: str, output: str = "", version: str = None):
    with _deploy_lock:
        _deploy_status["status"] = status
        _deploy_status["progress"] = progress
        _deploy_status["version"] = version
        if output:
            _deploy_status["output"] = output
        _deploy_status["timestamp"] = datetime.now().isoformat()


def _poll_listener_status(listener_url: str, version: Optional[str]):
    """Poll deploy listener for status updates and sync to local status"""
    import time
    max_polls = 300  # 5 minutes at 1s intervals
    for _ in range(max_polls):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{listener_url}/deploy-status")
                if response.status_code == 200:
                    data = response.json()
                    _update_deploy_status(
                        status=data.get("status", "running"),
                        progress=data.get("progress", ""),
                        output=data.get("output", ""),
                        version=version
                    )
                    with _deploy_lock:
                        _deploy_status["is_deploying"] = data.get("is_deploying", False)
                    if not data.get("is_deploying", False):
                        break
        except Exception as e:
            logger.debug(f"Poll error: {e}")
        time.sleep(1)


def _start_listener_polling(listener_url: str, version: Optional[str]):
    """Start background thread to poll listener for status"""
    thread = threading.Thread(
        target=_poll_listener_status,
        args=(listener_url, version),
        daemon=True
    )
    thread.start()


async def _verify_super_admin(db: AsyncSession, token: str):
    """Verify token and check super_admin role"""
    from backend.auth.jwt_utils import verify_and_decode_token
    from backend.database.models import User, Role

    payload = await verify_and_decode_token(db, token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    if not role or role.name != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admins can deploy"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def deploy_health(db: AsyncSession = Depends(get_db)):
    db_health = await _get_db_health(db)
    maintenance = await _is_maintenance_mode(db)
    return HealthCheckResponse(
        status="ok",
        version=settings.VERSION,
        db_status=db_health.get("status", "unknown"),
        maintenance_mode=maintenance,
    )


@router.get("/deploy-status", response_model=DeployStatusResponse)
async def get_deploy_status():
    with _deploy_lock:
        return DeployStatusResponse(**_deploy_status)


@router.post("/deploy", response_model=DeployResponse)
@limiter.limit("1/5minute")
async def deploy_update(
    request: Request,
    deploy_req: DeployRequest,
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("Authorization", "")
    deploy_key = settings.get_deploy_key()

    # 1. Check UpdateKey first (CI/CD)
    if auth_header.startswith("UpdateKey "):
        if not deploy_key:
            raise HTTPException(status_code=503, detail="Deploy API not configured")
        if auth_header[9:] != deploy_key:
            raise HTTPException(status_code=401, detail="Invalid deploy API key")
    else:
        # 2. Try Bearer JWT, fallback to HttpOnly cookie
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            token = request.cookies.get("access_token")

        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            await _verify_super_admin(db, token)
        except Exception as e:
            logger.error(f"Deploy auth error: {e}")
            raise HTTPException(401, "Invalid or expired token. Please refresh the page.")

    if not deploy_key:
        logger.warning("Deploy attempt without API key configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deploy API not configured on server"
        )

    with _deploy_lock:
        if _deploy_status["is_deploying"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment already in progress"
            )

    # Deploy via host manager (required - no fallback to local execution)
    deploy_manager_url = os.environ.get("DEPLOY_MANAGER_URL") or os.environ.get("DEPLOY_LISTENER_URL")
    if not deploy_manager_url:
        # Default: try host gateway (Linux Docker) or host.docker.internal
        deploy_manager_url = "http://host.docker.internal:14241"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{deploy_manager_url}/deploy",
                json={"version": deploy_req.version},
                headers={"Authorization": f"UpdateKey {deploy_key}"}
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Deploy triggered via manager: {result}")
                # Start polling manager for status
                _start_listener_polling(deploy_manager_url, deploy_req.version)
                return DeployResponse(
                    status="started",
                    commit="pending",
                    branch=deploy_req.version or "main",
                    message=f"Deployment started via host manager. Poll /webhook/deploy-status for progress.",
                    timestamp=datetime.now().isoformat(),
                    output=""
                )
            else:
                logger.error(f"Deploy manager returned {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Deploy manager error: {response.text}"
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy manager unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Deploy manager unavailable at {deploy_manager_url}. "
                   f"Error: {e}. "
                   f"Please ensure chronos-update-manager is running on the host machine."
        )


@router.post("/rollback", response_model=DeployResponse)
@limiter.limit("1/hour")
async def deploy_rollback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    timestamp: Optional[str] = None,
):
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        await _verify_super_admin(db, token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, "Invalid token")

    deploy_key = settings.DEPLOY_API_KEY
    if not deploy_key:
        raise HTTPException(status_code=503, detail="Deploy API not configured")

    try:
        logger.info(f"Starting SAFE rollback to {timestamp or 'latest'}...")

        app_dir = PROJECT_DIR
        script_path = os.path.join(app_dir, "scripts", "rollback.sh")

        if not os.path.exists(script_path):
            raise HTTPException(status_code=500, detail="Rollback script not found")

        cmd = ["bash", "-c", f"echo 'yes' | {script_path}{' ' + timestamp if timestamp else ''}"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=app_dir,
            timeout=600
        )

        output = result.stdout + result.stderr

        if result.returncode == 0:
            return DeployResponse(
                status="success",
                commit=f"rollback-{timestamp or 'latest'}",
                branch="main",
                message=f"Rolled back to {timestamp or 'latest'}",
                timestamp=datetime.now().isoformat(),
                output=output[-2000:] if len(output) > 2000 else output
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Rollback failed: {output[-500:]}"
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Rollback timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback error: {str(e)}")


@router.get("/deploy-log")
async def get_deploy_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    lines: int = 50,
):
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        from backend.auth.jwt_utils import verify_and_decode_token
        from backend.database.models import User, Role

        payload = await verify_and_decode_token(db, token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()

        if not role or role.name not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin role required")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, "Invalid token")

    app_dir = PROJECT_DIR
    log_path = os.path.join(app_dir, "backups", "chronos", "deploy.log")

    if not os.path.exists(log_path):
        return {"status": "ok", "log": [], "message": "No deploy log found"}

    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {
                "status": "ok",
                "log": [line.strip() for line in last_lines],
                "total_lines": len(all_lines)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log: {str(e)}")


@router.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed database health check"""
    health = await _get_db_health(db)
    maintenance = await _is_maintenance_mode(db)
    return {
        **health,
        "maintenance_mode": maintenance,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/maintenance-mode")
@limiter.limit("5/hour")
async def set_maintenance(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Toggle maintenance mode using pg_advisory_lock"""
    from backend.auth.jwt_utils import verify_and_decode_token
    from backend.database.models import User, Role
    from pydantic import BaseModel

    class MaintenanceRequest(BaseModel):
        enabled: bool
        reason: str = ""

    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = await verify_and_decode_token(db, token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()

        if not role or role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admins can toggle maintenance mode")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, "Invalid token")

    body = await request.json()
    req = MaintenanceRequest(**body)

    await _set_maintenance_mode(db, req.enabled, req.reason)

    return MaintenanceModeResponse(enabled=req.enabled, reason=req.reason)
