import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
import os
import base64
from typing import List, Optional

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
    RegistrationCredential,
    AuthenticationCredential,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers import options_to_json
from webauthn.helpers import base64url_to_bytes

from backend.database.database import get_db
from backend.database.models import User, WebAuthnCredential, WebAuthnChallenge, sofia_now
from backend.auth import jwt_utils, security
from backend.config import settings

from backend.auth.module_guard import require_module_dep

router = APIRouter(
    prefix="/webauthn", 
    tags=["Biometrics"],
    dependencies=[Depends(require_module_dep("integrations"))]
)

def get_rp_id_from_request(request: Request = None) -> str:
    """Get the RP ID from the request host or settings"""
    if request:
        host = request.headers.get("host", "")
        if host:
            return host.split(":")[0]  # Remove port if present
    
    if settings.BACKEND_CORS_ORIGINS and len(settings.BACKEND_CORS_ORIGINS) > 0:
        return settings.BACKEND_CORS_ORIGINS[0].split("//")[-1].split(":")[0]
    return "localhost"

def get_expected_origin(request: Request = None) -> str:
    """Get the expected origin - use request origin if available"""
    if request:
        origin = request.headers.get("origin") or request.headers.get("host", "")
        if origin:
            if origin.startswith("https//"):
                origin = origin.replace("https//", "https://")
            elif origin.startswith("http//"):
                origin = origin.replace("http//", "http://")
            elif not origin.startswith("http"):
                origin = f"https://{origin}"
            return origin
    
    if settings.BACKEND_CORS_ORIGINS and len(settings.BACKEND_CORS_ORIGINS) > 0:
        if request:
            host = request.headers.get("host", "")
            for allowed in settings.BACKEND_CORS_ORIGINS:
                if host.split(":")[0] in allowed:
                    return allowed
        return settings.BACKEND_CORS_ORIGINS[0]
    
    return "http://localhost:3000"

RP_NAME = "Chronos WorkTime"

@router.post("/register/options")
async def get_registration_options(
    request: Request,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерира опции за регистрация на нов биометричен ключ"""
    
    rp_id = get_rp_id_from_request(request)
    
    # Изчистване на стари предизвикателства
    await db.execute(delete(WebAuthnChallenge).where(WebAuthnChallenge.expires_at < sofia_now()))
    
    # Вземане на съществуващите ключове на потребителя
    stmt = select(WebAuthnCredential).where(WebAuthnCredential.user_id == current_user.id)
    result = await db.execute(stmt)
    existing_credentials = result.scalars().all()
    
    exclude_credentials = [
        PublicKeyCredentialDescriptor(
            id=cred.credential_id,
            type=PublicKeyCredentialType.PUBLIC_KEY
        ) for cred in existing_credentials
    ]

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=RP_NAME,
        user_id=str(current_user.id).encode(),
        user_name=current_user.email,
        user_display_name=f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
        attestation=AttestationConveyancePreference.NONE,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
        exclude_credentials=exclude_credentials,
    )

    # Записване на предизвикателството в базата
    challenge_str = bytes_to_base64url(options.challenge)
    new_challenge = WebAuthnChallenge(
        user_id=current_user.id,
        challenge=challenge_str,
        expires_at=sofia_now() + timedelta(minutes=5)
    )
    db.add(new_challenge)
    await db.commit()

    return json.loads(options_to_json(options))

@router.post("/register/verify")
async def verify_registration(
    request: Request,
    response_data: dict,
    current_user: User = Depends(jwt_utils.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Верифицира резултата от регистрацията и записва ключа"""
    
    expected_origin = get_expected_origin(request)
    rp_id = get_rp_id_from_request(request)
    
    # Намиране на валидно предизвикателство
    stmt = select(WebAuthnChallenge).where(
        WebAuthnChallenge.user_id == current_user.id,
        WebAuthnChallenge.expires_at > sofia_now()
    ).order_by(WebAuthnChallenge.created_at.desc())
    
    result = await db.execute(stmt)
    challenge_record = result.scalars().first()
    
    if not challenge_record:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        expected_challenge_bytes = base64url_to_bytes(challenge_record.challenge)
        
        verification = verify_registration_response(
            credential=response_data,
            expected_challenge=expected_challenge_bytes,
            expected_origin=expected_origin,
            expected_rp_id=rp_id,
            require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_cred = WebAuthnCredential(
        user_id=current_user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        friendly_name=response_data.get("friendly_name", "Устройство")
    )
    db.add(new_cred)
    
    await db.delete(challenge_record)
    await db.commit()

    return {"status": "success", "message": "Biometrics registered successfully"}

@router.post("/login/options")
async def get_login_options(
    request: Request,
    body: dict = None,
    db: AsyncSession = Depends(get_db)
):
    """Генерира опции за биометричен вход"""
    
    if body is None:
        try:
            body = await request.json()
        except:
            body = {}
    
    email = body.get("email")
    rp_id = get_rp_id_from_request(request)
    
    allow_credentials: list[PublicKeyCredentialDescriptor] = []
    if email:
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user:
            stmt = select(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id)
            res = await db.execute(stmt)
            creds = res.scalars().all()
            for c in creds:
                allow_credentials.append(PublicKeyCredentialDescriptor(
                    id=c.credential_id,
                    type=PublicKeyCredentialType.PUBLIC_KEY
                ))
    
    options = generate_authentication_options(
        rp_id=rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=allow_credentials,
    )

    challenge_str = bytes_to_base64url(options.challenge)
    new_challenge = WebAuthnChallenge(
        challenge=challenge_str,
        expires_at=sofia_now() + timedelta(minutes=5)
    )
    db.add(new_challenge)
    await db.commit()

    return json.loads(options_to_json(options))

@router.post("/login/verify")
async def verify_login(
    request: Request,
    response_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Верифицира биометричния вход и издава JWT"""
    
    expected_origin = get_expected_origin(request)
    rp_id = get_rp_id_from_request(request)
    
    # 1. Намиране на предизвикателството
    stmt = select(WebAuthnChallenge).where(WebAuthnChallenge.expires_at > sofia_now()).order_by(WebAuthnChallenge.created_at.desc())
    result = await db.execute(stmt)
    challenge_record = result.scalars().first()

    if not challenge_record:
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    # 2. Намиране на ключа
    cred_id_bytes = base64url_to_bytes(response_data["id"])
    stmt = select(WebAuthnCredential).where(WebAuthnCredential.credential_id == cred_id_bytes)
    result = await db.execute(stmt)
    db_credential = result.scalars().first()

    if not db_credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    try:
        expected_challenge_bytes = base64url_to_bytes(challenge_record.challenge)
        
        verification = verify_authentication_response(
            credential=response_data,
            expected_challenge=expected_challenge_bytes,
            expected_origin=expected_origin,
            expected_rp_id=rp_id,
            credential_public_key=db_credential.public_key,
            credential_current_sign_count=db_credential.sign_count,
            require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Verification failed: {str(e)}")

    # 3. Обновяване на брояча и дата на ползване
    db_credential.sign_count = verification.new_sign_count
    db_credential.last_used_at = sofia_now()
    
    # 4. Генериране на JWT за потребителя
    stmt = select(User).options(selectinload(User.role)).where(User.id == db_credential.user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    access_token, _ = await jwt_utils.create_tokens(db, user.id, user.email)
    
    await db.delete(challenge_record)
    await db.commit()

    user_role = user.role.name if user.role else None
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user_role
        }
    }
