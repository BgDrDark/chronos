import logging

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
