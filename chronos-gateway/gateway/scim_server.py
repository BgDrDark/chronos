"""
SCIM 2.0 Server for HR provisioning

Поддържа:
- Users: GET (list + pagination), POST, GET/{id}, PUT/{id}, PATCH/{id}, DELETE/{id}
- Groups: GET (list), POST, GET/{id}, PUT/{id}, PATCH/{id}, DELETE/{id}
- ServiceProviderConfig, Schemas, ResourceTypes (discovery)
- /Me endpoint
- Bearer token auth
- SQLite persistence via config.db
- Zone sync on active/deactivate
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Response, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from gateway.database.sqlite_manager import config_db
from gateway.access import zone_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scim/v2")


def migrate_json_to_sqlite():
    """Мигрира съществуващи потребители от JSON файл в SQLite (ако има)"""
    import os
    from pathlib import Path
    from gateway.config import config as gw_config
    base = Path(gw_config.get("logging.file", "logs/gateway.log")).parent.parent
    json_path = base / "config" / "scim_users.json"
    if not json_path.exists():
        return

    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM scim_users").fetchone()[0]
        if existing > 0:
            return

        try:
            with open(json_path) as f:
                users = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        now = _now()
        for u in users:
            ext_id = u.get("externalId", u.get("userName", ""))
            uid = u.get("id", str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scim:{ext_id}")))
            name = u.get("name", {})
            conn.execute(
                """INSERT OR IGNORE INTO scim_users
                   (id, external_id, user_name, display_name, given_name, family_name, emails, active, roles, created_at, modified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid, ext_id, u.get("userName", ext_id), u.get("displayName", ext_id),
                    name.get("givenName", ""), name.get("familyName", ""),
                    json.dumps(u.get("emails", [])), 1 if u.get("active", True) else 0,
                    json.dumps(u.get("roles", [])), now, now,
                ),
            )

        logger.info(f"SCIM: Migrated {len(users)} users from JSON to SQLite")

SCHEMAS_CORE_USER = "urn:ietf:params:scim:schemas:core:2.0:User"
SCHEMAS_CORE_GROUP = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCHEMAS_LIST = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCHEMAS_ERROR = "urn:ietf:params:scim:api:messages:2.0:Error"

# ─── DB helpers ──────────────────────────────────────────────

SCIM_USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS scim_users (
        id TEXT PRIMARY KEY,
        external_id TEXT UNIQUE,
        user_name TEXT UNIQUE,
        display_name TEXT,
        given_name TEXT DEFAULT '',
        family_name TEXT DEFAULT '',
        emails TEXT DEFAULT '[]',
        active INTEGER DEFAULT 1,
        roles TEXT DEFAULT '[]',
        created_at TEXT,
        modified_at TEXT
    )
"""

SCIM_GROUPS_TABLE = """
    CREATE TABLE IF NOT EXISTS scim_groups (
        id TEXT PRIMARY KEY,
        display_name TEXT UNIQUE,
        members TEXT DEFAULT '[]',
        created_at TEXT,
        modified_at TEXT
    )
"""


def _ensure_scim_tables():
    with config_db.get_connection() as conn:
        conn.execute(SCIM_USERS_TABLE)
        conn.execute(SCIM_GROUPS_TABLE)


def _row_to_scim_user(row) -> dict:
    now = row["modified_at"] or row["created_at"]
    uid = row["id"]
    return {
        "schemas": [SCHEMAS_CORE_USER],
        "id": uid,
        "externalId": row["external_id"],
        "userName": row["user_name"],
        "name": {
            "formatted": row["display_name"],
            "givenName": row["given_name"],
            "familyName": row["family_name"],
        },
        "displayName": row["display_name"],
        "emails": json.loads(row["emails"] or "[]"),
        "active": bool(row["active"]),
        "roles": json.loads(row["roles"] or "[]"),
        "meta": {
            "resourceType": "User",
            "created": row["created_at"],
            "lastModified": now,
            "location": f"/scim/v2/Users/{uid}",
        },
    }


def _row_to_scim_group(row) -> dict:
    uid = row["id"]
    members = json.loads(row["members"] or "[]")
    return {
        "schemas": [SCHEMAS_CORE_GROUP],
        "id": uid,
        "displayName": row["display_name"],
        "members": members,
        "meta": {
            "resourceType": "Group",
            "created": row["created_at"],
            "lastModified": row["modified_at"] or row["created_at"],
            "location": f"/scim/v2/Groups/{uid}",
        },
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sync_to_zones(user_id: str, active: bool):
    """Синхронизира потребителя с authorized_users на зоните"""
    try:
        uid_int = int(user_id)
    except (ValueError, TypeError):
        try:
            uid_int = int(uuid.UUID(user_id).int) & 0x7FFFFFFF
        except (ValueError, AttributeError):
            return

    for zone in zone_manager.zones.values():
        changed = False
        if active:
            if uid_int not in zone.authorized_users:
                zone.authorized_users.append(uid_int)
                changed = True
        else:
            if uid_int in zone.authorized_users:
                zone.authorized_users.remove(uid_int)
                changed = True
        if changed:
            zone_manager._save_zone_to_sqlite(zone)


# ─── Auth ─────────────────────────────────────────────────────

def _get_bearer_token(authorization: Optional[str] = Header(None, alias="Authorization")) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


async def verify_scim_auth(authorization: Optional[str] = Header(None, alias="Authorization")):
    from gateway.config import config as gw_config
    token = _get_bearer_token(authorization)
    expected = gw_config.get("scim.api_token", "")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail={
            "schemas": [SCHEMAS_ERROR],
            "detail": "Unauthorized",
            "status": "401",
        })
    return token


# ─── Users ────────────────────────────────────────────────────

@router.get("/Users")
async def list_users(
    start_index: int = 1,
    count: int = 100,
    filter: Optional[str] = None,
    _auth=Depends(verify_scim_auth),
):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        if filter:
            where_clauses = []
            params = []
            for part in filter.split(" "):
                if "eq" in part.lower():
                    op = "="
                    parts = part.split("eq", 1)
                elif "sw" in part.lower():
                    op = "LIKE"
                    parts = part.split("sw", 1)
                elif "co" in part.lower():
                    op = "LIKE"
                    parts = part.split("co", 1)
                else:
                    continue
                field = parts[0].strip()
                val = parts[1].strip().strip('"')
                if op == "LIKE":
                    val = f"%{val}%"
                if field == "userName":
                    where_clauses.append(f"user_name {op} ?")
                elif field == "active":
                    where_clauses.append(f"active {op} ?")
                    val = 1 if val.lower() in ("true", "1") else 0
                else:
                    continue
                params.append(val)
            if where_clauses:
                where_sql = " AND ".join(where_clauses)
                total = conn.execute(f"SELECT COUNT(*) FROM scim_users WHERE {where_sql}", params).fetchone()[0]
                rows = conn.execute(
                    f"SELECT * FROM scim_users WHERE {where_sql} ORDER BY user_name LIMIT ? OFFSET ?",
                    params + [count, start_index - 1],
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) FROM scim_users").fetchone()[0]
                rows = conn.execute(
                    "SELECT * FROM scim_users ORDER BY user_name LIMIT ? OFFSET ?",
                    (count, start_index - 1),
                ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) FROM scim_users").fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM scim_users ORDER BY user_name LIMIT ? OFFSET ?",
                (count, start_index - 1),
            ).fetchall()

    return {
        "schemas": [SCHEMAS_LIST],
        "totalResults": total,
        "itemsPerPage": count,
        "startIndex": start_index,
        "Resources": [_row_to_scim_user(r) for r in rows],
    }


@router.get("/Users/{user_id}")
async def get_user(user_id: str, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_users WHERE id = ? OR external_id = ?",
            (user_id, user_id),
        ).fetchone()
    if not row:
        return JSONResponse(status_code=404, content={
            "schemas": [SCHEMAS_ERROR], "detail": "User not found", "status": "404",
        })
    return _row_to_scim_user(row)


@router.post("/Users", status_code=201)
async def create_user(data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    external_id = data.get("externalId", data.get("userName", str(uuid.uuid4())))
    user_name = data.get("userName", external_id)
    display_name = data.get("displayName") or data.get("name", {}).get("formatted", user_name)
    given_name = data.get("name", {}).get("givenName", display_name.split()[0] if display_name else "")
    family_name = data.get("name", {}).get("familyName", " ".join(display_name.split()[1:]) if display_name and len(display_name.split()) > 1 else "")
    active = data.get("active", True)
    emails = json.dumps(data.get("emails", [{"value": f"{user_name}@local", "type": "work", "primary": True}]))
    roles = json.dumps(data.get("roles", []))
    now = _now()
    uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scim:{external_id}"))

    with config_db.get_connection() as conn:
        try:
            conn.execute(
                """INSERT INTO scim_users (id, external_id, user_name, display_name, given_name, family_name, emails, active, roles, created_at, modified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid, external_id, user_name, display_name, given_name, family_name, emails, 1 if active else 0, roles, now, now),
            )
        except Exception as e:
            return JSONResponse(status_code=409, content={
                "schemas": [SCHEMAS_ERROR], "detail": f"User already exists: {e}", "status": "409",
            })

    logger.info(f"SCIM: Created user {user_name} (ext: {external_id})")

    if active:
        _sync_to_zones(uid, True)

    row = conn.execute("SELECT * FROM scim_users WHERE id = ?", (uid,)).fetchone()
    return _row_to_scim_user(row)


@router.put("/Users/{user_id}")
async def update_user(user_id: str, data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_users WHERE id = ? OR external_id = ?",
            (user_id, user_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "User not found", "status": "404",
            })

        user_name = data.get("userName", row["user_name"])
        display_name = data.get("displayName") or data.get("name", {}).get("formatted", row["display_name"])
        given_name = data.get("name", {}).get("givenName", row["given_name"])
        family_name = data.get("name", {}).get("familyName", row["family_name"])
        active = data.get("active", bool(row["active"]))
        emails = json.dumps(data.get("emails", json.loads(row["emails"] or "[]")))
        roles = json.dumps(data.get("roles", json.loads(row["roles"] or "[]")))
        now = _now()

        conn.execute(
            """UPDATE scim_users SET user_name=?, display_name=?, given_name=?, family_name=?, emails=?, active=?, roles=?, modified_at=?
               WHERE id=?""",
            (user_name, display_name, given_name, family_name, emails, 1 if active else 0, roles, now, row["id"]),
        )

        logger.info(f"SCIM: Updated user {user_name}")
        _sync_to_zones(row["id"], active)

        row = conn.execute("SELECT * FROM scim_users WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_scim_user(row)


@router.patch("/Users/{user_id}")
async def patch_user(user_id: str, data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_users WHERE id = ? OR external_id = ?",
            (user_id, user_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "User not found", "status": "404",
            })

        operations = data.get("Operations", [])
        updates = {}
        active_changed = False

        for op in operations:
            path = op.get("path", "")
            value = op.get("value")

            if path == "active" or (not path and isinstance(value, dict) and "active" in value):
                new_active = value if isinstance(value, bool) else value.get("active", True)
                updates["active"] = 1 if new_active else 0
                active_changed = True
            elif path == "userName" and value:
                updates["user_name"] = value
            elif path.startswith("name."):
                field = path.split(".")[1]
                name_map = {"givenName": "given_name", "familyName": "family_name", "formatted": "display_name"}
                col = name_map.get(field)
                if col:
                    updates[col] = value
            elif path == "displayName" and value:
                updates["display_name"] = value
            elif path == "emails" and isinstance(value, list):
                updates["emails"] = json.dumps(value)
            elif path == "roles" and isinstance(value, list):
                updates["roles"] = json.dumps(value)

        if updates:
            updates["modified_at"] = _now()
            set_clause = ", ".join(f"{k}=?" for k in updates)
            params = list(updates.values()) + [row["id"]]
            conn.execute(f"UPDATE scim_users SET {set_clause} WHERE id=?", params)

        if active_changed:
            _sync_to_zones(row["id"], bool(updates.get("active", row["active"])))

        row = conn.execute("SELECT * FROM scim_users WHERE id = ?", (row["id"],)).fetchone()
        logger.info(f"SCIM: Patched user {row['user_name']}")
        return _row_to_scim_user(row)


@router.delete("/Users/{user_id}", status_code=204)
async def delete_user(user_id: str, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_users WHERE id = ? OR external_id = ?",
            (user_id, user_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "User not found", "status": "404",
            })

        conn.execute("UPDATE scim_users SET active=0, modified_at=? WHERE id=?", (_now(), row["id"]))
        _sync_to_zones(row["id"], False)

    logger.info(f"SCIM: Deactivated user {row['user_name']}")
    return Response(status_code=204)


# ─── Groups ───────────────────────────────────────────────────

@router.get("/Groups")
async def list_groups(
    start_index: int = 1,
    count: int = 100,
    _auth=Depends(verify_scim_auth),
):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM scim_groups").fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM scim_groups ORDER BY display_name LIMIT ? OFFSET ?",
            (count, start_index - 1),
        ).fetchall()

    return {
        "schemas": [SCHEMAS_LIST],
        "totalResults": total,
        "itemsPerPage": count,
        "startIndex": start_index,
        "Resources": [_row_to_scim_group(r) for r in rows],
    }


@router.get("/Groups/{group_id}")
async def get_group(group_id: str, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_groups WHERE id = ? OR display_name = ?",
            (group_id, group_id),
        ).fetchone()
    if not row:
        return JSONResponse(status_code=404, content={
            "schemas": [SCHEMAS_ERROR], "detail": "Group not found", "status": "404",
        })
    return _row_to_scim_group(row)


@router.post("/Groups", status_code=201)
async def create_group(data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    display_name = data.get("displayName", str(uuid.uuid4()))
    members = json.dumps(data.get("members", []))
    now = _now()
    uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"scim:group:{display_name}"))

    with config_db.get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO scim_groups (id, display_name, members, created_at, modified_at) VALUES (?, ?, ?, ?, ?)",
                (uid, display_name, members, now, now),
            )
        except Exception as e:
            return JSONResponse(status_code=409, content={
                "schemas": [SCHEMAS_ERROR], "detail": f"Group already exists: {e}", "status": "409",
            })

    logger.info(f"SCIM: Created group {display_name}")
    row = conn.execute("SELECT * FROM scim_groups WHERE id = ?", (uid,)).fetchone()
    return _row_to_scim_group(row)


@router.put("/Groups/{group_id}")
async def update_group(group_id: str, data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_groups WHERE id = ? OR display_name = ?",
            (group_id, group_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "Group not found", "status": "404",
            })

        display_name = data.get("displayName", row["display_name"])
        members = json.dumps(data.get("members", json.loads(row["members"] or "[]")))
        now = _now()

        conn.execute(
            "UPDATE scim_groups SET display_name=?, members=?, modified_at=? WHERE id=?",
            (display_name, members, now, row["id"]),
        )

        logger.info(f"SCIM: Updated group {display_name}")
        row = conn.execute("SELECT * FROM scim_groups WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_scim_group(row)


@router.patch("/Groups/{group_id}")
async def patch_group(group_id: str, data: dict, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_groups WHERE id = ? OR display_name = ?",
            (group_id, group_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "Group not found", "status": "404",
            })

        operations = data.get("Operations", [])
        updates = {}

        for op in operations:
            path = op.get("path", "")
            value = op.get("value")

            if path == "displayName" and value:
                updates["display_name"] = value
            elif path == "members" and isinstance(value, list):
                existing = json.loads(row["members"] or "[]")
                op_type = op.get("op", "replace").lower()
                if op_type == "add":
                    existing_member_ids = {m.get("value") for m in existing}
                    for m in value:
                        if m.get("value") not in existing_member_ids:
                            existing.append(m)
                elif op_type == "remove":
                    remove_ids = {m.get("value") for m in value}
                    existing = [m for m in existing if m.get("value") not in remove_ids]
                elif op_type in ("replace", "replaceAll"):
                    existing = value
                updates["members"] = json.dumps(existing)
            elif not path and isinstance(value, dict):
                for k, v in value.items():
                    if k == "members" and isinstance(v, list):
                        updates["members"] = json.dumps(v)
                    elif k == "displayName":
                        updates["display_name"] = v

        if updates:
            updates["modified_at"] = _now()
            set_clause = ", ".join(f"{k}=?" for k in updates)
            params = list(updates.values()) + [row["id"]]
            conn.execute(f"UPDATE scim_groups SET {set_clause} WHERE id=?", params)

        row = conn.execute("SELECT * FROM scim_groups WHERE id = ?", (row["id"],)).fetchone()
        logger.info(f"SCIM: Patched group {row['display_name']}")
        return _row_to_scim_group(row)


@router.delete("/Groups/{group_id}", status_code=204)
async def delete_group(group_id: str, _auth=Depends(verify_scim_auth)):
    _ensure_scim_tables()
    with config_db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scim_groups WHERE id = ? OR display_name = ?",
            (group_id, group_id),
        ).fetchone()
        if not row:
            return JSONResponse(status_code=404, content={
                "schemas": [SCHEMAS_ERROR], "detail": "Group not found", "status": "404",
            })

        conn.execute("DELETE FROM scim_groups WHERE id=?", (row["id"],))

    logger.info(f"SCIM: Deleted group {row['display_name']}")
    return Response(status_code=204)


# ─── Discovery ────────────────────────────────────────────────

SERVICEPROVIDER_CONFIG = {
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
    "patch": {"supported": True},
    "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
    "filter": {"supported": True, "maxResults": 200},
    "changePassword": {"supported": False},
    "sort": {"supported": False},
    "etag": {"supported": False},
    "authenticationSchemes": [
        {
            "name": "Bearer Token",
            "description": "Authentication scheme using Bearer token",
            "specUri": "https://tools.ietf.org/html/rfc6750",
            "type": "oauthbearertoken",
            "primary": True,
        }
    ],
    "meta": {
        "resourceType": "ServiceProviderConfig",
        "location": "/scim/v2/ServiceProviderConfig",
        "created": "2024-01-01T00:00:00Z",
        "lastModified": "2024-01-01T00:00:00Z",
    },
}

SCHEMAS_LIST_RESPONSE = {
    "schemas": [SCHEMAS_LIST],
    "totalResults": 3,
    "itemsPerPage": 3,
    "startIndex": 1,
    "Resources": [
        {
            "id": SCHEMAS_CORE_USER,
            "name": "User",
            "description": "User Account",
            "attributes": [
                {"name": "userName", "type": "string", "multiValued": False, "required": True, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "server"},
                {"name": "displayName", "type": "string", "multiValued": False, "required": False, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "none"},
                {"name": "name", "type": "complex", "multiValued": False, "required": False, "subAttributes": [
                    {"name": "formatted", "type": "string"},
                    {"name": "givenName", "type": "string"},
                    {"name": "familyName", "type": "string"},
                ]},
                {"name": "emails", "type": "complex", "multiValued": True, "required": False},
                {"name": "active", "type": "boolean", "multiValued": False, "required": False, "mutability": "readWrite", "returned": "default"},
                {"name": "roles", "type": "string", "multiValued": True, "required": False},
                {"name": "externalId", "type": "string", "multiValued": False, "required": False},
            ],
            "meta": {"resourceType": "Schema", "location": f"/scim/v2/Schemas/{SCHEMAS_CORE_USER}"},
        },
        {
            "id": SCHEMAS_CORE_GROUP,
            "name": "Group",
            "description": "Group",
            "attributes": [
                {"name": "displayName", "type": "string", "multiValued": False, "required": True},
                {"name": "members", "type": "complex", "multiValued": True, "required": False, "subAttributes": [
                    {"name": "value", "type": "string"},
                    {"name": "display", "type": "string"},
                    {"name": "type", "type": "string"},
                ]},
            ],
            "meta": {"resourceType": "Schema", "location": f"/scim/v2/Schemas/{SCHEMAS_CORE_GROUP}"},
        },
    ],
}


@router.get("/ServiceProviderConfig")
async def get_service_provider_config(_auth=Depends(verify_scim_auth)):
    return SERVICEPROVIDER_CONFIG


@router.get("/Schemas")
async def list_schemas(_auth=Depends(verify_scim_auth)):
    return SCHEMAS_LIST_RESPONSE


@router.get("/Schemas/{schema_id}")
async def get_schema(schema_id: str, _auth=Depends(verify_scim_auth)):
    for resource in SCHEMAS_LIST_RESPONSE["Resources"]:
        if resource["id"] == schema_id:
            return resource
    return JSONResponse(status_code=404, content={
        "schemas": [SCHEMAS_ERROR], "detail": "Schema not found", "status": "404",
    })


RESOURCE_TYPES = {
    "schemas": [SCHEMAS_LIST],
    "totalResults": 2,
    "itemsPerPage": 2,
    "startIndex": 1,
    "Resources": [
        {
            "id": "User",
            "name": "User",
            "description": "User Account",
            "endpoint": "/Users",
            "schema": SCHEMAS_CORE_USER,
            "meta": {"resourceType": "ResourceType", "location": "/scim/v2/ResourceTypes/User"},
        },
        {
            "id": "Group",
            "name": "Group",
            "description": "Group",
            "endpoint": "/Groups",
            "schema": SCHEMAS_CORE_GROUP,
            "meta": {"resourceType": "ResourceType", "location": "/scim/v2/ResourceTypes/Group"},
        },
    ],
}


@router.get("/ResourceTypes")
async def list_resource_types(_auth=Depends(verify_scim_auth)):
    return RESOURCE_TYPES


@router.get("/ResourceTypes/{type_id}")
async def get_resource_type(type_id: str, _auth=Depends(verify_scim_auth)):
    for resource in RESOURCE_TYPES["Resources"]:
        if resource["id"] == type_id:
            return resource
    return JSONResponse(status_code=404, content={
        "schemas": [SCHEMAS_ERROR], "detail": "Resource type not found", "status": "404",
    })


# ─── /Me ──────────────────────────────────────────────────────

@router.get("/Me")
async def get_me(_auth=Depends(verify_scim_auth)):
    return {
        "schemas": [SCHEMAS_CORE_USER],
        "id": "me",
        "userName": "scim-client",
        "displayName": "SCIM Client",
        "active": True,
        "meta": {"resourceType": "User", "location": "/scim/v2/Me"},
    }


@router.patch("/Me")
async def patch_me(data: dict, _auth=Depends(verify_scim_auth)):
    return {
        "schemas": [SCHEMAS_CORE_USER],
        "id": "me",
        "userName": "scim-client",
        "displayName": "SCIM Client",
        "active": True,
    }
