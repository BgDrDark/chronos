import contextlib
import io
import json
import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_utils import get_current_user
from backend.database import models
from backend.database.database import get_db
from backend.routers.documents import UPLOAD_DIR

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager for collaborative floor plan editing."""

    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, floor_plan_id: int):
        await websocket.accept()
        if floor_plan_id not in self.rooms:
            self.rooms[floor_plan_id] = []
        self.rooms[floor_plan_id].append(websocket)
        await self.broadcast(
            floor_plan_id,
            {"type": "user_connected", "count": len(self.rooms[floor_plan_id])},
        )

    def disconnect(self, websocket: WebSocket, floor_plan_id: int):
        if floor_plan_id in self.rooms:
            self.rooms[floor_plan_id] = [
                ws for ws in self.rooms[floor_plan_id] if ws != websocket
            ]
            if not self.rooms[floor_plan_id]:
                del self.rooms[floor_plan_id]

    async def broadcast(self, floor_plan_id: int, message: dict[str, Any]):
        if floor_plan_id not in self.rooms:
            return
        disconnected = []
        for ws in self.rooms[floor_plan_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws, floor_plan_id)


manager = ConnectionManager()


@router.websocket("/ws/floor-plan/{floor_plan_id}")
async def floor_plan_websocket(websocket: WebSocket, floor_plan_id: int):
    await manager.connect(websocket, floor_plan_id)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("type")

            if msg_type == "door_move":
                await manager.broadcast(
                    floor_plan_id,
                    {
                        "type": "door_moved",
                        "doorId": msg["doorId"],
                        "x": msg["x"],
                        "y": msg["y"],
                    },
                )
            elif msg_type == "door_rotate":
                await manager.broadcast(
                    floor_plan_id,
                    {
                        "type": "door_rotated",
                        "doorId": msg["doorId"],
                        "rotation": msg["rotation"],
                    },
                )
            elif msg_type == "door_added":
                await manager.broadcast(
                    floor_plan_id,
                    {
                        "type": "door_added",
                        "door": msg["door"],
                    },
                )
            elif msg_type == "door_removed":
                await manager.broadcast(
                    floor_plan_id,
                    {
                        "type": "door_removed",
                        "doorId": msg["doorId"],
                    },
                )
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for floor_plan {floor_plan_id}: {e}")
    finally:
        manager.disconnect(websocket, floor_plan_id)
        await manager.broadcast(
            floor_plan_id,
            {
                "type": "user_disconnected",
                "count": len(manager.rooms.get(floor_plan_id, [])),
            },
        )


@router.post("/floor-plan/{floor_plan_id}/upload-background")
async def upload_floor_plan_background(
    floor_plan_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Качване на фоново изображение за план на етаж."""
    if current_user.role.name not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Само администратор може да променя фона")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Файлът трябва да бъде изображение.")

    from backend.database.models import FloorPlan as DbFloorPlan

    fp = await db.get(DbFloorPlan, floor_plan_id)
    if not fp:
        raise HTTPException(status_code=404, detail="Етажът не е намерен")

    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    if image.width > 1920:
        ratio = 1920 / float(image.width)
        new_height = int(float(image.height) * ratio)
        image = image.resize((1920, new_height), Image.Resampling.LANCZOS)

    filename = f"floor_plan_{floor_plan_id}_{uuid.uuid4().hex[:8]}.webp"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    file_path = os.path.join(UPLOAD_DIR, filename)
    image.save(file_path, "WEBP", quality=85)

    if fp.background_image:
        old_path = os.path.join(UPLOAD_DIR, fp.background_image)
        if os.path.exists(old_path):
            with contextlib.suppress(BaseException):
                os.remove(old_path)

    fp.background_image = filename
    await db.commit()

    return {"status": "success", "filename": f"/uploads/{filename}"}
