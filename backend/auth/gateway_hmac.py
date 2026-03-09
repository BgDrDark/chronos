"""
HMAC Validation for Gateway - Backend Communication
Provides functions to sign and verify HMAC-SHA256 signatures
"""
import hmac
import hashlib
import json
import time
from typing import Optional
from fastapi import HTTPException, Header, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.database import get_db
from backend.database.models import Gateway


# Timestamp validity window in seconds (5 minutes)
TIMESTAMP_WINDOW = 300


def generate_hmac_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for a payload"""
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_hmac_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature"""
    expected_signature = generate_hmac_signature(payload, secret)
    return hmac.compare_digest(expected_signature, signature)


def verify_timestamp(timestamp: str) -> bool:
    """Verify that timestamp is not older than TIMESTAMP_WINDOW seconds"""
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        return abs(current_time - request_time) <= TIMESTAMP_WINDOW
    except (ValueError, TypeError):
        return False


async def get_gateway_from_request(
    x_gateway_key: str = Header(..., alias="X-Gateway-Key"),
    db: AsyncSession = Depends(get_db)
) -> Gateway:
    """Get and verify gateway from X-Gateway-Key header"""
    from sqlalchemy import select
    
    # Find gateway by API key
    stmt = select(Gateway).where(Gateway.api_key == x_gateway_key)
    result = await db.execute(stmt)
    gateway = result.scalar_one_or_none()
    
    if not gateway:
        raise HTTPException(status_code=401, detail="Invalid gateway API key")
    
    if not gateway.is_active:
        raise HTTPException(status_code=403, detail="Gateway is inactive")
    
    return gateway


class HMACVerifier:
    """Helper class for HMAC verification in endpoints"""
    
    def __init__(self, gateway_secret: str):
        self.gateway_secret = gateway_secret
    
    def verify(self, payload: str, signature: str, timestamp: str) -> bool:
        """Verify HMAC signature and timestamp"""
        # Check timestamp first
        if not verify_timestamp(timestamp):
            return False
        
        # Verify signature
        return verify_hmac_signature(payload, signature, self.gateway_secret)


async def require_gateway_auth(
    x_signature: str = Header(..., alias="X-Signature"),
    x_timestamp: str = Header(..., alias="X-Timestamp"),
    request: Request = None,
    gateway: Gateway = Depends(get_gateway_from_request)
):
    """Dependency that requires valid HMAC signature"""
    # Get the raw body
    body = await request.body()
    body_str = body.decode() if body else ""
    
    # For GET requests, use query params as payload
    if not body_str and request:
        body_str = str(request.url.query)
    
    # Verify timestamp
    if not verify_timestamp(x_timestamp):
        raise HTTPException(
            status_code=401, 
            detail="Request timestamp expired. Please sync your clock or retry."
        )
    
    # Verify HMAC signature
    # Use API key as secret for signature verification
    if not verify_hmac_signature(body_str, x_signature, gateway.api_key):
        raise HTTPException(
            status_code=401, 
            detail="Invalid HMAC signature"
        )
    
    return gateway


def create_gateway_signature(payload: dict, secret: str) -> tuple[str, str]:
    """
    Create signature and timestamp for gateway requests
    Returns (signature, timestamp)
    """
    timestamp = str(int(time.time()))
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = generate_hmac_signature(f"{payload_str}{timestamp}", secret)
    return signature, timestamp
