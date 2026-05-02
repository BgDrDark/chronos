import os
import subprocess
import logging
import threading
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from backend.config import settings
from backend.database.database import get_db

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


def _parse_progress_line(line: str) -> Optional[str]:
    """Extract progress indicator from deploy script output"""
    if "[0/7]" in line:
        return "Acquiring DB lock..."
    elif "[1/7]" in line:
        return "Health check (current)"
    elif "[2/7]" in line:
        return "Creating backup..."
    elif "[3/7]" in line:
        return "Pulling images from GHCR..."
    elif "[4/7]" in line:
        return "Running Alembic migrations..."
    elif "[5/7]" in line:
        return "Deploying backend..."
    elif "[6/7]" in line:
        return "Deploying frontend..."
    elif "[7/7]" in line:
        return "Final health check..."
    elif "Deploy Complete" in line:
        return "Deployment complete"
    elif "Rolling back" in line or "ROLLBACK" in line:
        return "Rolling back..."
    return None


def _run_deploy_script(app_dir: str, script_path: str, version: Optional[str]):
    """Run deploy script in background thread with real-time progress updates"""
    full_output = []

    try:
        cmd = ["bash", script_path]
        if version:
            cmd.extend(["--version", version])

        _update_deploy_status("running", "Starting deployment...", "", version)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=app_dir,
        )

        for line in iter(process.stdout.readline, ""):
            if line:
                line = line.rstrip()
                full_output.append(line)
                logger.info(f"deploy: {line}")

                progress = _parse_progress_line(line)
                if progress:
                    _update_deploy_status("running", progress, "\n".join(full_output[-50:]), version)

        process.wait()
        returncode = process.returncode
        output_text = "\n".join(full_output)

        if returncode == 0:
            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=app_dir
            )
            commit_hash = commit_result.stdout.strip() or "unknown"

            _update_deploy_status("success", "Deployment complete", output_text, version)
            logger.info(f"SAFE deployment complete: {commit_hash}")
        else:
            is_rollback = "Rollback" in output_text or "ROLLBACK" in output_text
            final_status = "rolled_back" if is_rollback else "failed"
            final_progress = "Deployment failed" + (" - rolled back" if is_rollback else "")

            _update_deploy_status(final_status, final_progress, output_text, version)
            logger.error(f"Deploy script failed with exit code {returncode}")

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        _update_deploy_status("failed", f"Error: {str(e)}", "\n".join(full_output), version)
    finally:
        with _deploy_lock:
            _deploy_status["is_deploying"] = False


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
async def deploy_update(
    request: DeployRequest,
    info: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header[7:]

    try:
        await _verify_super_admin(db, token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy auth error: {e}")
        raise HTTPException(401, "Invalid token")

    with _deploy_lock:
        if _deploy_status["is_deploying"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment already in progress"
            )

    deploy_key = settings.DEPLOY_API_KEY
    if not deploy_key:
        logger.warning("Deploy attempt without API key configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deploy API not configured on server"
        )

    app_dir = os.environ.get("PROJECT_DIR", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    script_path = os.path.join(app_dir, "scripts", "deploy-safe.sh")

    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deploy script not found"
        )

    with _deploy_lock:
        _deploy_status["is_deploying"] = True
        _deploy_status["status"] = "running"
        _deploy_status["progress"] = "Starting deployment..."
        _deploy_status["version"] = request.version
        _deploy_status["output"] = ""

    thread = threading.Thread(
        target=_run_deploy_script,
        args=(app_dir, script_path, request.version),
        daemon=True
    )
    thread.start()

    return DeployResponse(
        status="started",
        commit="pending",
        branch=request.version or "main",
        message=f"Deployment started{' to ' + request.version if request.version else ''}. Poll /webhook/deploy-status for progress.",
        timestamp=datetime.now().isoformat(),
        output=""
    )


@router.post("/rollback", response_model=DeployResponse)
async def deploy_rollback(
    info: Request,
    db: AsyncSession = Depends(get_db),
    timestamp: Optional[str] = None,
):
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header[7:]

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
    info: Request,
    db: AsyncSession = Depends(get_db),
    lines: int = 50,
):
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header[7:]

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
async def set_maintenance(
    info: Request,
    db: AsyncSession = Depends(get_db),
):
    """Toggle maintenance mode using pg_advisory_lock"""
    from backend.auth.jwt_utils import verify_and_decode_token
    from backend.database.models import User, Role
    from pydantic import BaseModel

    class MaintenanceRequest(BaseModel):
        enabled: bool
        reason: str = ""

    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header[7:]

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

    body = await info.json()
    req = MaintenanceRequest(**body)

    await _set_maintenance_mode(db, req.enabled, req.reason)

    return MaintenanceModeResponse(enabled=req.enabled, reason=req.reason)
