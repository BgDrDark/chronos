import logging
from typing import Any

from sqlalchemy import select
from strawberry.types import Info

from backend.auth.rbac_service import PermissionService
from backend.database.models import (
    Batch,
    CashJournalEntry,
    Company,
    Ingredient,
    InventorySession,
    Invoice,
    LeaveRequest,
    ProductionOrder,
    Recipe,
    ScheduleTemplate,
    Shift,
    ShiftSwapRequest,
    StorageZone,
    TimeLog,
    User,
    WorkSchedule,
)
from backend.exceptions import NotFoundException, PermissionDeniedException

logger = logging.getLogger(__name__)

_MODEL_COMPANY_MAP = {
    "User": (User, "company_id"),
    "Recipe": (Recipe, "company_id"),
    "ProductionOrder": (ProductionOrder, "company_id"),
    "Ingredient": (Ingredient, "company_id"),
    "StorageZone": (StorageZone, "company_id"),
    "InventorySession": (InventorySession, "company_id"),
    "CashJournalEntry": (CashJournalEntry, "company_id"),
    "Invoice": (Invoice, "company_id"),
    "Shift": (Shift, "company_id"),
    "ScheduleTemplate": (ScheduleTemplate, "company_id"),
    "Company": (Company, None),
    "UserPayroll": (User, "company_id"),
}

_INDIRECT_COMPANY_MAP = {
    "LeaveRequest": (LeaveRequest, "user_id", User, "company_id"),
    "TimeLog": (TimeLog, "user_id", User, "company_id"),
    "WorkSchedule": (WorkSchedule, "user_id", User, "company_id"),
    "ShiftSwapRequest": (ShiftSwapRequest, "requestor_id", User, "company_id"),
    "Batch": (Batch, "ingredient_id", Ingredient, "company_id"),
}


async def _resolve_resource_company_id(db, model_type: str, resource_id: int) -> int | None:
    if model_type in _MODEL_COMPANY_MAP:
        model_cls, company_col = _MODEL_COMPANY_MAP[model_type]
        if company_col is None:
            return resource_id
        stmt = select(getattr(model_cls, company_col)).where(model_cls.id == resource_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    if model_type in _INDIRECT_COMPANY_MAP:
        src_model, src_fk, target_model, target_col = _INDIRECT_COMPANY_MAP[model_type]
        stmt = (
            select(getattr(target_model, target_col))
            .join(target_model, getattr(src_model, src_fk) == target_model.id)
            .where(src_model.id == resource_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    raise ValueError(f"Unknown model type for company access check: {model_type}")


async def require_permission(
    info: Info,
    permission: str,
    company_id: int | None = None,
    resource_id: int | None = None,
) -> bool:
    """
    Helper function to check permissions in GraphQL resolvers.
    
    Use this for complex operations that need multiple permission checks
    or for queries that need permission verification.
    
    Args:
        info: Strawberry Info object containing context
        permission: Permission string (e.g., "users:create")
        company_id: Optional company ID for company-scoped operations
        resource_id: Optional resource ID for ownership checks
        
    Returns:
        True if permission is granted
        
    Raises:
        PermissionDeniedException: If permission is denied
        
    Example:
        @strawberry.mutation
        async def create_user(self, info: Info, input: CreateUserInput) -> User:
            await require_permission(info, "users:create", company_id=input.company_id)
            # ... proceed with operation
    """
    current_user = info.context.get("current_user")
    
    if not current_user:
        raise PermissionDeniedException(
            detail="Authentication required",
            context={"permission": permission},
        )
    
    db = info.context.get("db")
    if not db:
        raise PermissionDeniedException(
            detail="System error: database unavailable",
            context={"permission": permission},
        )
    
    permission_service = PermissionService(db)
    
    has_permission = await permission_service.check_permission(
        user_id=current_user.id,
        permission=permission,
        company_id=company_id,
        resource_id=resource_id,
    )
    
    await permission_service.log_permission_decision(
        user_id=current_user.id,
        permission=permission,
        decision=has_permission,
        resource_type=permission.split(":")[0] if ":" in permission else None,
        resource_id=resource_id,
        context={
            "company_id": company_id,
            "ip_address": info.context.get("ip_address"),
        },
    )
    
    if not has_permission:
        raise PermissionDeniedException(
            detail=f"Нямате разрешение за: {permission}",
            context={
                "permission": permission,
                "user_id": current_user.id,
                "company_id": company_id,
            },
        )
    
    return True


async def check_company_access(
    info_or_db,
    target_company_id_or_user,
    model_type: str | None = None,
    resource_id: int | None = None,
) -> int | None:
    if model_type is not None:
        assert resource_id is not None
        return await _check_company_access_legacy(
            info_or_db, target_company_id_or_user, model_type, resource_id
        )

    info = info_or_db
    target_company_id = target_company_id_or_user

    current_user = info.context.get("current_user")

    if not current_user:
        raise PermissionDeniedException(
            detail="Authentication required",
            context={"target_company_id": target_company_id},
        )

    if current_user.role and current_user.role.name == "super_admin":
        return None

    if target_company_id and current_user.company_id != target_company_id:
        raise PermissionDeniedException(
            detail="Нямате достъп до данни на друга компания",
            context={
                "user_company_id": current_user.company_id,
                "target_company_id": target_company_id,
            },
        )

    return current_user.company_id


async def _check_company_access_legacy(
    db, current_user, model_type: str, resource_id: int
) -> int | None:
    if not current_user:
        raise PermissionDeniedException(
            detail="Authentication required",
            context={"model_type": model_type, "resource_id": resource_id},
        )

    if current_user.role and current_user.role.name == "super_admin":
        return None

    target_company_id = await _resolve_resource_company_id(db, model_type, resource_id)

    if target_company_id is None:
        raise NotFoundException(
            detail=f"{model_type} with id {resource_id} not found",
            context={"model_type": model_type, "resource_id": resource_id},
        )

    if current_user.company_id != target_company_id:
        raise PermissionDeniedException(
            detail="Нямате достъп до данни на друга компания",
            context={
                "user_company_id": current_user.company_id,
                "target_company_id": target_company_id,
            },
        )

    return current_user.company_id


async def check_resource_ownership(
    info: Info,
    resource_type: str,
    resource_id: int,
    permission: str,
) -> bool:
    """
    Check if the current user owns the specified resource.
    
    Args:
        info: Strawberry Info object containing context
        resource_type: Type of resource (e.g., "timelogs", "payroll")
        resource_id: ID of the resource to check
        permission: Permission to check (e.g., "timelogs:update_own")
        
    Returns:
        True if user owns the resource or has full permission
        
    Raises:
        PermissionDeniedException: If user doesn't own the resource
        
    Example:
        @strawberry.mutation
        async def update_time_log(self, info: Info, id: int, ...) -> TimeLog:
            await check_resource_ownership(info, "timelogs", id, "timelogs:update_own")
            # ... proceed with operation
    """
    current_user = info.context.get("current_user")
    
    if not current_user:
        raise PermissionDeniedException(
            detail="Authentication required",
            context={"resource_type": resource_type, "resource_id": resource_id},
        )
    
    db = info.context.get("db")
    if not db:
        raise PermissionDeniedException(
            detail="System error: database unavailable",
            context={"resource_type": resource_type},
        )
    
    permission_service = PermissionService(db)
    
    has_permission = await permission_service.check_permission(
        user_id=current_user.id,
        permission=permission,
        resource_id=resource_id,
    )
    
    await permission_service.log_permission_decision(
        user_id=current_user.id,
        permission=permission,
        decision=has_permission,
        resource_type=resource_type,
        resource_id=resource_id,
        context={"ip_address": info.context.get("ip_address")},
    )
    
    if not has_permission:
        raise PermissionDeniedException(
            detail=f"Нямате достъп до този {resource_type}",
            context={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "permission": permission,
            },
        )
    
    return True


def get_current_user(info: Info) -> Any:
    """
    Get the current authenticated user from context.
    
    Args:
        info: Strawberry Info object containing context
        
    Returns:
        The current user object
        
    Raises:
        PermissionDeniedException: If no user is authenticated
    """
    current_user = info.context.get("current_user")
    
    if not current_user:
        raise PermissionDeniedException(
            detail="Authentication required",
            context={},
        )
    
    return current_user


def get_db_session(info: Info):
    """
    Get the database session from context.
    
    Args:
        info: Strawberry Info object containing context
        
    Returns:
        The async database session
        
    Raises:
        PermissionDeniedException: If no session is available
    """
    db = info.context.get("db")
    
    if not db:
        raise PermissionDeniedException(
            detail="System error: database unavailable",
            context={},
        )
    
    return db
