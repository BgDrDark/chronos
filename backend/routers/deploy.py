import os
import subprocess
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["deploy"])


class DeployResponse(BaseModel):
    status: str
    commit: str
    branch: str = "main"
    message: str
    timestamp: str


class HealthCheckResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthCheckResponse)
async def deploy_health():
    """Health check for deploy endpoint"""
    return HealthCheckResponse(
        status="ok",
        version=settings.VERSION
    )


@router.post("/deploy", response_model=DeployResponse)
async def deploy_update(
    info: Request,
):
    """Trigger deployment via webhook - requires super_admin role"""
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
        db = info.state.db
        payload = await verify_and_decode_token(db, token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database to check role
        from backend.database.models import User
        from sqlalchemy import select
        
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or user.role.name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admins can deploy"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy auth error: {e}")
        raise HTTPException(401, "Invalid token")
    
    # Proceed with deployment
    deploy_key = settings.DEPLOY_API_KEY
    
    if not deploy_key:
        logger.warning("Deploy attempt without API key configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deploy API not configured on server"
        )
    
    try:
        logger.info("Starting deployment...")
        
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            cwd="/app"
        )
        
        commit_hash = "unknown"
        if result.returncode == 0:
            output = result.stdout or ""
            commit_hash = output.strip()[-8:] if output else "unknown"
            logger.info(f"Git pull result: {output}")
        
        subprocess.run(
            ["docker", "compose", "build", "backend"],
            capture_output=True,
            cwd="/app"
        )
        
        subprocess.run(
            ["docker", "compose", "up", "-d", "backend"],
            capture_output=True,
            cwd="/app"
        )
        
        logger.info(f"Deployment complete: {commit_hash}")
        
        return DeployResponse(
            status="success",
            commit=commit_hash,
            branch="main",
            message="Deployed successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment error: {str(e)}"
        )


@router.post("/rollback", response_model=DeployResponse)
async def deploy_rollback(
    x_api_key: str = Header(..., description="API key for deployment"),
    steps: int = 1,
):
    """Rollback deployment by N steps"""
    deploy_key = settings.DEPLOY_API_KEY
    
    if x_api_key != deploy_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        logger.info(f"Rolling back {steps} step(s)...")
        
        subprocess.run(
            ["git", "reset", "--hard", f"HEAD~{steps}"],
            capture_output=True,
            cwd="/app"
        )
        
        subprocess.run(
            ["docker", "compose", "build", "backend"],
            capture_output=True,
            cwd="/app"
        )
        
        subprocess.run(
            ["docker", "compose", "up", "-d", "backend"],
            capture_output=True,
            cwd="/app"
        )
        
        return DeployResponse(
            status="success",
            commit=f"rolled-back-{steps}",
            branch="main",
            message=f"Rolled back {steps} step(s)",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )