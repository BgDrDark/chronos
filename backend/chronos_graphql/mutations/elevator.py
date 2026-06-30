from __future__ import annotations

import strawberry
from sqlalchemy import select

from backend.database import models
from backend.exceptions import NotFoundException, ValidationException
from backend.chronos_graphql.inputs.elevator import (
    ElevatorFloorInput,
    ElevatorFloorUpdateInput,
    ElevatorGroupInput,
    ElevatorGroupUpdateInput,
)
from backend.chronos_graphql.types.elevator import ElevatorFloor, ElevatorGroup
from backend.chronos_graphql.utils.permission_checker import get_current_user
from backend.database.transaction_manager import atomic_transaction


@strawberry.type
class ElevatorMutations:
    @strawberry.mutation
    async def create_elevator_group(self, info: strawberry.Info, input: ElevatorGroupInput) -> ElevatorGroup:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            group = models.ElevatorGroup(
                name=input.name,
                gateway_id=input.gateway_id,
                terminal_id=input.terminal_id,
                controller_type=input.controller_type,
            )
            db.add(group)
            await db.flush()
            return ElevatorGroup.from_pydantic(group)

    @strawberry.mutation
    async def update_elevator_group(self, info: strawberry.Info, id: int, input: ElevatorGroupUpdateInput) -> ElevatorGroup:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            group = await db.get(models.ElevatorGroup, id)
            if not group:
                raise NotFoundException("Асансьорна група")
            if input.name is not None:
                group.name = input.name
            if input.terminal_id is not None:
                group.terminal_id = input.terminal_id
            if input.controller_type is not None:
                group.controller_type = input.controller_type
            if input.is_active is not None:
                group.is_active = input.is_active
            await db.flush()
            return ElevatorGroup.from_pydantic(group)

    @strawberry.mutation
    async def delete_elevator_group(self, info: strawberry.Info, id: int) -> bool:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            group = await db.get(models.ElevatorGroup, id)
            if not group:
                raise NotFoundException("Асансьорна група")
            await db.delete(group)
            await db.flush()
            return True

    @strawberry.mutation
    async def create_elevator_floor(self, info: strawberry.Info, input: ElevatorFloorInput) -> ElevatorFloor:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            group = await db.get(models.ElevatorGroup, input.elevator_group_id)
            if not group:
                raise NotFoundException("Асансьорна група")
            floor = models.ElevatorFloor(
                elevator_group_id=input.elevator_group_id,
                floor_number=input.floor_number,
                name=input.name,
                zone_id=input.zone_id,
                relay_device_id=input.relay_device_id,
                relay_number=input.relay_number,
                order=input.order,
            )
            db.add(floor)
            await db.flush()
            return ElevatorFloor.from_pydantic(floor)

    @strawberry.mutation
    async def update_elevator_floor(self, info: strawberry.Info, id: int, input: ElevatorFloorUpdateInput) -> ElevatorFloor:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            floor = await db.get(models.ElevatorFloor, id)
            if not floor:
                raise NotFoundException("Етаж")
            if input.floor_number is not None:
                floor.floor_number = input.floor_number
            if input.name is not None:
                floor.name = input.name
            if input.zone_id is not None:
                floor.zone_id = input.zone_id
            if input.relay_device_id is not None:
                floor.relay_device_id = input.relay_device_id
            if input.relay_number is not None:
                floor.relay_number = input.relay_number
            if input.order is not None:
                floor.order = input.order
            if input.is_active is not None:
                floor.is_active = input.is_active
            await db.flush()
            return ElevatorFloor.from_pydantic(floor)

    @strawberry.mutation
    async def delete_elevator_floor(self, info: strawberry.Info, id: int) -> bool:
        current_user = get_current_user(info)
        async with atomic_transaction(info.context["db"]) as db:
            floor = await db.get(models.ElevatorFloor, id)
            if not floor:
                raise NotFoundException("Етаж")
            await db.delete(floor)
            await db.flush()
            return True
