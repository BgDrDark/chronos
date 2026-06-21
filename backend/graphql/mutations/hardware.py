import logging

import httpx
import strawberry

from backend.exceptions import (
    InvalidOperationException,
    NotFoundException,
)
from backend.graphql import types
from backend.graphql.utils.permission_checker import get_current_user

logger = logging.getLogger(__name__)


@strawberry.type
class HardwareMutation:

    @strawberry.mutation
    async def update_terminal(
        self,
        id: int,
        alias: str | None = None,
        mode: str | None = None,
        is_active: bool | None = None,
        info: strawberry.Info = None,
    ) -> types.Terminal:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if not terminal:
            raise NotFoundException.resource("Terminal")
        if alias is not None:
            terminal.alias = alias
        if mode is not None:
            terminal.mode = mode
        if is_active is not None:
            terminal.is_active = is_active

        await db.commit()
        await db.refresh(terminal)
        return types.Terminal.from_pydantic(terminal)

    @strawberry.mutation
    async def delete_terminal(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import Terminal
        terminal = await db.get(Terminal, id)
        if terminal:
            await db.delete(terminal)
            await db.commit()
            return True
        return False

    @strawberry.mutation
    async def update_gateway(
        self,
        id: int,
        alias: str | None = None,
        company_id: int | None = None,
        info: strawberry.Info = None,
    ) -> types.Gateway:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import Gateway
        gateway = await db.get(Gateway, id)
        if not gateway:
            raise NotFoundException.resource("Gateway")

        if alias is not None:
            gateway.alias = alias
        if company_id is not None:
            gateway.company_id = company_id

        await db.commit()
        await db.refresh(gateway)
        return types.Gateway.from_pydantic(gateway)

    @strawberry.mutation
    async def sync_gateway_config(
        self,
        id: int,
        direction: str,
        info: strawberry.Info = None,
    ) -> str:
        if not info:
            raise InvalidOperationException.info_required()
        db = info.context["db"]
        get_current_user(info)

        from backend.database.models import Gateway as GwModel
        gateway = await db.get(GwModel, id)
        if not gateway:
            raise NotFoundException.resource("Gateway")

        host = gateway.ip_address or "localhost"
        port = gateway.web_port or 8889

        if direction == "push":
            url = f"http://{host}:{port}/sync/push"
        elif direction == "pull":
            url = f"http://{host}:{port}/sync/pull"
        else:
            raise InvalidOperationException("direction must be 'push' or 'pull'")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", "Sync completed")
        except httpx.RequestError as e:
            logger.error(f"Failed to reach gateway {id} at {url}: {e}")
            return f"Грешка: Неуспешна връзка с gateway-а ({e})"
        except Exception as e:
            logger.error(f"Unexpected error syncing gateway {id}: {e}")
            return f"Грешка при синхронизация: {e}"
