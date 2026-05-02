import os
import json
import subprocess
import logging
import threading
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import settings
from backend.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["deploy"])


class DeployRequest(BaseModel):
    version: Optional[str] = None  # e.g. "3.6.2.0" - if None, deploys latest main


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


class DeployStatusResponse(BaseModel):
    is_deploying: bool
    status: str  # "idle", "running", "success", "failed", "rolled_back"
    progress: str
    version: Optional[str] = None
    output: Optional[str] = None
    timestamp: Optional[str] = None


# Global deploy status (in-memory)
_deploy_status = {
    "is_deploying": False,
    "status": "idle",
    "progress": "",
    "version": None,
    "output": "",
    "timestamp": None,
}

# Lock for thread safety
_deploy_lock = threading.Lock()


def _update_deploy_status(status: str, progress: str, output: str = "", version: str = None):
    with _deploy_lock:
        _deploy_status["status"] = status
        _deploy_status["progress"] = progress
        _deploy_status["version"] = version
        if output:
            _deploy_status["output"] = output
        _deploy_status["timestamp"] = datetime.now().isoformat()


@router.get("/health", response_model=HealthCheckResponse)
async def deploy_health():
    """Health check for deploy endpoint"""
    return HealthCheckResponse(
        status="ok",
        version=settings.VERSION
    )


@router.get("/deploy-status", response_model=DeployStatusResponse)
async def get_deploy_status():
    """Get current deployment status for polling"""
    with _deploy_lock:
        return DeployStatusResponse(**_deploy_status)


@router.post("/deploy", response_model=DeployResponse)
async def deploy_update(
    request: DeployRequest,
    info: Request,
    db: AsyncSession = Depends(get_db),
):
    """Trigger SAFE deployment via webhook - requires super_admin role
    
    Uses deploy-safe.sh script which includes:
    - Pre-deployment checks (Docker, disk space, git, .env)
    - Backup (DB + images + config)
    - Backup verification
    - Git fetch + checkout (version-specific if provided)
    - Build images (with cache)
    - Alembic migrations
    - Deploy backend + health check
    - Deploy frontend
    - Gateway restart
    - Final health check
    - Auto-rollback on failure
    
    Request body:
    - version: Optional[str] - e.g. "3.6.2.0" for version-specific deploy
      If not provided, deploys latest main branch
    """
    from backend.auth.jwt_utils import verify_and_decode_token
    
    # Get token from Authorization header
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Decode token and check super_admin role
    try:
        payload = await verify_and_decode_token(db, token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database to check role
        from backend.database.models import User, Role
        
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Get role name
        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()
        
        if not role or role.name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admins can deploy"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy auth error: {e}")
        raise HTTPException(401, "Invalid token")
    
    # Check if already deploying
    with _deploy_lock:
        if _deploy_status["is_deploying"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment already in progress"
            )
    
    # Check deploy API key
    deploy_key = settings.DEPLOY_API_KEY
    if not deploy_key:
        logger.warning("Deploy attempt without API key configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deploy API not configured on server"
        )
    
    # Proceed with SAFE deployment using deploy-safe.sh
    try:
        logger.info(f"Starting SAFE deployment via deploy-safe.sh (version: {request.version or 'latest main'})...")
        
        # Update status
        with _deploy_lock:
            _deploy_status["is_deploying"] = True
            _deploy_status["status"] = "running"
            _deploy_status["progress"] = "Starting deployment..."
            _deploy_status["version"] = request.version
            _deploy_status["output"] = ""
        
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_path = os.path.join(app_dir, "scripts", "deploy-safe.sh")
        
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Deploy script not found"
            )
        
        # Build command
        cmd = ["bash", script_path]
        if request.version:
            cmd.extend(["--version", request.version])
        
        # Run deploy-safe.sh
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=app_dir,
            timeout=1800  # 30 minutes timeout
        )
        
        output = result.stdout + result.stderr
        
        # Update output in status
        with _deploy_lock:
            _deploy_status["output"] = output
        
        if result.returncode == 0:
            # Get current commit
            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=app_dir
            )
            commit_hash = commit_result.stdout.strip() or "unknown"
            
            logger.info(f"SAFE deployment complete: {commit_hash}")
            
            with _deploy_lock:
                _deploy_status["is_deploying"] = False
                _deploy_status["status"] = "success"
                _deploy_status["progress"] = "Deployment complete"
            
            return DeployResponse(
                status="success",
                commit=commit_hash,
                branch=request.version or "main",
                message=f"Deployed successfully{' to ' + request.version if request.version else ''}",
                timestamp=datetime.now().isoformat(),
                output=output[-2000:] if len(output) > 2000 else output
            )
        else:
            logger.error(f"Deploy script failed with exit code {result.returncode}")
            
            # Check if it was a rollback
            is_rollback = "Rollback" in output or "ROLLBACK" in output
            
            with _deploy_lock:
                _deploy_status["is_deploying"] = False
                _deploy_status["status"] = "rolled_back" if is_rollback else "failed"
                _deploy_status["progress"] = "Deployment failed" + (" - rolled back" if is_rollback else "")
            
            if is_rollback:
                return DeployResponse(
                    status="rolled_back",
                    commit="rollback",
                    branch="main",
                    message="Deployment failed and rolled back automatically",
                    timestamp=datetime.now().isoformat(),
                    output=output[-2000:] if len(output) > 2000 else output
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deployment failed: {output[-500:]}"
            )
        
    except subprocess.TimeoutExpired:
        logger.error("Deployment timed out (30 minutes)")
        with _deploy_lock:
            _deploy_status["is_deploying"] = False
            _deploy_status["status"] = "failed"
            _deploy_status["progress"] = "Deployment timed out"
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Deployment timed out after 30 minutes"
        )
    except HTTPException:
        with _deploy_lock:
            _deploy_status["is_deploying"] = False
            _deploy_status["status"] = "failed"
            _deploy_status["progress"] = "Deployment failed"
        raise
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        with _deploy_lock:
            _deploy_status["is_deploying"] = False
            _deploy_status["status"] = "failed"
            _deploy_status["progress"] = f"Error: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment error: {str(e)}"
        )


@router.post("/rollback", response_model=DeployResponse)
async def deploy_rollback(
    info: Request,
    db: AsyncSession = Depends(get_db),
    timestamp: Optional[str] = None,
):
    """Rollback deployment using rollback.sh script"""
    from backend.auth.jwt_utils import verify_and_decode_token
    
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header[7:]
    
    try:
        payload = await verify_and_decode_token(db, token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from backend.database.models import User, Role
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        role_result = await db.execute(select(Role).where(Role.id == user.role_id))
        role = role_result.scalar_one_or_none()
        
        if not role or role.name != "super_admin":
            raise HTTPException(status_code=403, detail="Only super_admins can rollback")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, "Invalid token")
    
    deploy_key = settings.DEPLOY_API_KEY
    if not deploy_key:
        raise HTTPException(status_code=503, detail="Deploy API not configured")
    
    try:
        logger.info(f"Starting SAFE rollback to {timestamp or 'latest'}...")
        
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        script_path = os.path.join(app_dir, "scripts", "rollback.sh")
        
        if not os.path.exists(script_path):
            raise HTTPException(status_code=500, detail="Rollback script not found")
        
        # For automated rollback, bypass confirmation prompt
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
    """Get the last N lines from deploy.log"""
    from backend.auth.jwt_utils import verify_and_decode_token
    
    auth_header = info.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header[7:]
    
    try:
        payload = await verify_and_decode_token(db, token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from backend.database.models import User, Role
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
    
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
