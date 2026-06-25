"""
SCIM 2.0 Server for HR provisioning

Поддържа:
- GET /scim/v2/Users — списък с потребители
- GET /scim/v2/Users/{id} — детайли
- POST /scim/v2/Users — създаване
- PUT /scim/v2/Users/{id} — ъпдейт
- PATCH /scim/v2/Users/{id} — частичен ъпдейт
- DELETE /scim/v2/Users/{id} — деактивиране

Съхранява потребителите в SQLite и ги синхронизира с zone.authorized_users
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from gateway.database.sqlite_manager import config_db
from gateway.access import zone_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scim/v2")


def _load_users() -> List[Dict[str, Any]]:
    """Зарежда потребители от JSON файл"""
    import os
    from pathlib import Path
    from gateway.config import config as gateway_config
    base = Path(gateway_config.get("logging.file", "logs/gateway.log")).parent.parent
    path = base / "config" / "scim_users.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def _save_users(users: List[Dict[str, Any]]):
    """Запазва потребители в JSON файл"""
    import os
    from pathlib import Path
    from gateway.config import config as gateway_config
    base = Path(gateway_config.get("logging.file", "logs/gateway.log")).parent.parent
    path = base / "config" / "scim_users.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(users, f, indent=2, default=str)


def _scim_user(external_id: str, user_name: str, display_name: str, emails: list,
               active: bool = True, roles: list = None) -> dict:
    """Създава SCIM 2.0 User resource"""
    uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scim:{external_id}"))
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": uid,
        "externalId": external_id,
        "userName": user_name,
        "name": {"formatted": display_name, "givenName": display_name.split()[0] if display_name else user_name,
                 "familyName": " ".join(display_name.split()[1:]) if display_name and len(display_name.split()) > 1 else ""},
        "displayName": display_name or user_name,
        "emails": emails or [{"value": f"{user_name}@local", "type": "work", "primary": True}],
        "active": active,
        "roles": roles or [],
        "meta": {"resourceType": "User", "created": now, "lastModified": now, "location": f"/scim/v2/Users/{uid}"},
    }


def _sync_to_zones(user_id: str, active: bool):
    """Синхронизира потребителя с authorized_users на зоните"""
    try:
        uid_int = int(user_id)
        for zone in zone_manager.zones.values():
            if active:
                if uid_int not in zone.authorized_users:
                    zone.authorized_users.append(uid_int)
                    zone_manager._save_zone_to_sqlite(zone)
            else:
                if uid_int in zone.authorized_users:
                    zone.authorized_users.remove(uid_int)
                    zone_manager._save_zone_to_sqlite(zone)
    except (ValueError, TypeError):
        pass


@router.get("/Users")
async def list_users():
    users = _load_users()
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(users),
        "itemsPerPage": len(users),
        "startIndex": 1,
        "Resources": users
    }


@router.get("/Users/{user_id}")
async def get_user(user_id: str):
    users = _load_users()
    for u in users:
        if u["id"] == user_id or u.get("externalId") == user_id:
            return u
    return JSONResponse(status_code=404, content={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": "User not found", "status": "404"
    })


@router.post("/Users")
async def create_user(data: dict):
    external_id = data.get("externalId", data.get("userName", str(uuid.uuid4())))
    user_name = data.get("userName", external_id)
    display_name = data.get("displayName") or data.get("name", {}).get("formatted", user_name)
    active = data.get("active", True)
    emails = data.get("emails", [])
    roles = data.get("roles", [])

    user = _scim_user(external_id, user_name, display_name, emails, active, roles)
    users = _load_users()
    users.append(user)
    _save_users(users)

    if active:
        _sync_to_zones(external_id, True)

    logger.info(f"SCIM: Created user {user_name} (ext: {external_id})")
    return user


@router.put("/Users/{user_id}")
async def update_user(user_id: str, data: dict):
    users = _load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id or u.get("externalId") == user_id:
            if "userName" in data:
                u["userName"] = data["userName"]
            if "displayName" in data:
                u["displayName"] = data["displayName"]
            if "active" in data:
                u["active"] = data["active"]
                _sync_to_zones(u.get("externalId", u["userName"]), data["active"])
            if "name" in data:
                u["name"] = data["name"]
            if "emails" in data:
                u["emails"] = data["emails"]
            if "roles" in data:
                u["roles"] = data["roles"]
            u["meta"]["lastModified"] = datetime.now(timezone.utc).isoformat()
            users[i] = u
            _save_users(users)
            logger.info(f"SCIM: Updated user {u['userName']}")
            return u
    return JSONResponse(status_code=404, content={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": "User not found", "status": "404"
    })


@router.patch("/Users/{user_id}")
async def patch_user(user_id: str, data: dict):
    users = _load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id or u.get("externalId") == user_id:
            if "Operations" in data:
                for op in data["Operations"]:
                    path = op.get("path", "")
                    value = op.get("value")
                    if path == "active" or (not path and isinstance(value, dict) and "active" in value):
                        new_active = value if isinstance(value, bool) else value.get("active", True)
                        u["active"] = new_active
                        _sync_to_zones(u.get("externalId", u["userName"]), new_active)
                    elif path.startswith("name."):
                        if "name" not in u:
                            u["name"] = {}
                        field = path.split(".")[1]
                        u["name"][field] = value
                        u["displayName"] = u["name"].get("formatted", u.get("displayName"))
                    elif path == "emails" and isinstance(value, list):
                        u["emails"] = value
                    elif path == "roles" and isinstance(value, list):
                        u["roles"] = value
            u["meta"]["lastModified"] = datetime.now(timezone.utc).isoformat()
            users[i] = u
            _save_users(users)
            logger.info(f"SCIM: Patched user {u['userName']}")
            return u
    return JSONResponse(status_code=404, content={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": "User not found", "status": "404"
    })


@router.delete("/Users/{user_id}")
async def delete_user(user_id: str):
    users = _load_users()
    for i, u in enumerate(users):
        if u["id"] == user_id or u.get("externalId") == user_id:
            u["active"] = False
            _sync_to_zones(u.get("externalId", u["userName"]), False)
            users[i] = u
            _save_users(users)
            logger.info(f"SCIM: Deactivated user {u['userName']}")
            return Response(status_code=204)
    return JSONResponse(status_code=404, content={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": "User not found", "status": "404"
    })
