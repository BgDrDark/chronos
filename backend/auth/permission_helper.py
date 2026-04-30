from functools import wraps
from typing import Optional, List
import strawberry
from strawberry.types import Info

from backend.auth.rbac_service import PermissionService
from backend.exceptions import PermissionDeniedException, AuthenticationException


def get_permission_error_message(permission: str) -> str:
    """Get translated error message for missing permission"""
    translations = {
        "users:create": "Нямате права да създавате потребители",
        "users:update": "Нямате права да променяте потребители",
        "users:delete": "Нямате права да изтривате потребители",
        "users:read": "Нямате права да прегледждате потребители",
        "users:manage_roles": "Нямате права да управлявате роли",
        "timelogs:create": "Нямате права да създавате часове",
        "timelogs:create_own": "Нямате права да отбелязвате часове",
        "timelogs:read": "Нямате права да преглеждате часове",
        "timelogs:update": "Нямате права да променяте часове",
        "timelogs:admin_create": "Нямате права да създавате часове за други",
        "schedules:create": "Нямате права да създавате смени",
        "schedules:update": "Нямате права да променяте смени",
        "schedules:read": "Нямате права да преглеждате смени",
        "schedules:approve_swaps": "Нямате права да одобрявате размени",
        "payroll:read": "Нямате права да преглеждате заплати",
        "payroll:create": "Нямате права да създавате заплати",
        "payroll:update": "Нямате права да променяте заплати",
        "payroll:export": "Нямате права да експортирате заплати",
        "leaves:create": "Нямате права да създавате отпуски",
        "leaves:read": "Нямате права да преглеждате отпуски",
        "leaves:approve": "Нямате права да одобрявате отпуски",
        "leaves:update": "Нямате права да променяте отпуски",
        "companies:create": "Нямате права да създавате фирми",
        "companies:update": "Нямате права да променяте фирми",
        "companies:read": "Нямате права да преглеждате фирми",
        "companies:manage_users": "Нямате права да управлявате потребители",
        "system:manage_settings": "Нямате права да управлявате настройки",
        "system:manage_roles": "Нямате права да управлявате роли",
        "reports:read": "Нямате права да преглеждате отчети",
        "reports:create": "Нямате права да създавате отчети",
        "reports:export": "Нямате права да експортирате отчети",
    }
    return translations.get(permission, f"Нямате права за: {permission}")


async def check_permission(
    current_user,
    permission: str,
    db,
    company_id: Optional[int] = None
) -> bool:
    """Check if user has permission"""
    if not current_user:
        raise AuthenticationException(detail="Не сте идентифицирани в системата")
    
    perm_service = PermissionService(db)
    has_perm = await perm_service.check_permission(
        current_user.id,
        permission,
        company_id=company_id or getattr(current_user, 'company_id', None)
    )
    
    if not has_perm:
        raise PermissionDeniedException(
            detail=get_permission_error_message(permission)
        )
    
    return True


def require_permission(permission: str):
    """
    Decorator for GraphQL resolvers to check permissions.
    
    Usage:
    
    @strawberry.mutation
    @require_permission("users:create")
    async def create_user(self, user_input: UserInput, info: strawberry.Info) -> User:
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            info = kwargs.get('info')
            if not info:
                raise PermissionDeniedException(detail="Missing info context")
            
            current_user = info.context.get('current_user')
            db = info.context.get('db')
            
            if not current_user:
                raise AuthenticationException(detail="Не сте идентифицирани в системата")
            
            if not db:
                raise PermissionDeniedException(detail="Missing database context")
            
            company_id = kwargs.get('company_id') or getattr(current_user, 'company_id', None)
            
            perm_service = PermissionService(db)
            has_perm = await perm_service.check_permission(
                current_user.id,
                permission,
                company_id=company_id
            )
            
            if not has_perm:
                raise PermissionDeniedException(
                    detail=get_permission_error_message(permission)
                )
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permissions(permissions: List[str]):
    """
    Decorator for GraphQL resolvers to check multiple permissions.
    User needs ALL permissions to proceed.
    
    Usage:
    
    @strawberry.mutation
    @require_permissions(["users:create", "users:read"])
    async def create_user(self, user_input: UserInput, info: strawberry.Info) -> User:
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            info = kwargs.get('info')
            if not info:
                raise PermissionDeniedException(detail="Missing info context")
            
            current_user = info.context.get('current_user')
            db = info.context.get('db')
            
            if not current_user:
                raise AuthenticationException(detail="Не сте идентифицирани в системата")
            
            if not db:
                raise PermissionDeniedException(detail="Missing database context")
            
            company_id = kwargs.get('company_id') or getattr(current_user, 'company_id', None)
            
            perm_service = PermissionService(db)
            
            for perm in permissions:
                has_perm = await perm_service.check_permission(
                    current_user.id,
                    perm,
                    company_id=company_id
                )
                
                if not has_perm:
                    raise PermissionDeniedException(
                        detail=get_permission_error_message(perm)
                    )
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


async def require_role(current_user, allowed_roles: List[str], info) -> bool:
    """
    Legacy support: Check if user has one of the allowed roles.
    This is kept for backward compatibility during migration.
    
    Usage:
    
    if current_user.role.name not in ["admin", "super_admin"]:
        raise PermissionDeniedException.for_action("manage")
    
    # Can be replaced with:
    await require_role(current_user, ["admin", "super_admin"], info)
    """
    if not current_user:
        raise AuthenticationException(detail="Не сте идентифицирани в системата")
    
    if not allowed_roles:
        return True
    
    user_role = getattr(current_user, 'role', None)
    if not user_role:
        return False
    
    role_name = getattr(user_role, 'name', None)
    if role_name not in allowed_roles:
        raise PermissionDeniedException(
            detail=f"Нямате права за това действие. Необходима роля: {allowed_roles}"
        )
    
    return True


async def require_permission_or_role(
    current_user,
    permission: str,
    db,
    fallback_roles: List[str],
    company_id: Optional[int] = None
) -> bool:
    """
    Hybrid permission check: tries permission system first, falls back to role check.
    
    This allows gradual migration - uses new RBAC if permissions exist in DB,
    otherwise falls back to legacy role.name check.
    
    Usage:
    
    # Before:
    if current_user.role.name not in ["admin", "super_admin"]:
        raise PermissionDeniedException.for_action("manage")
    
    # After (with migration):
    await require_permission_or_role(
        current_user,
        "users:create",  # New permission
        db,
        ["admin", "super_admin"],  # Fallback roles
    )
    """
    if not current_user:
        raise AuthenticationException(detail="Не сте идентифицирани в системата")
    
    try:
        perm_service = PermissionService(db)
        has_perm = await perm_service.check_permission(
            current_user.id,
            permission,
            company_id=company_id or getattr(current_user, 'company_id', None)
        )
        
        if has_perm:
            return True
    except Exception:
        pass
    
    user_role = getattr(current_user, 'role', None)
    if not user_role:
        raise PermissionDeniedException(detail="Нямате права за това действие")
    
    role_name = getattr(user_role, 'name', None)
    if role_name not in fallback_roles:
        raise PermissionDeniedException(
            detail=f"Нямате права за това действие"
        )
    
    return True


ROLE_PERMISSION_MAP = {
    "super_admin": ["*"],
    "admin": ["*"],
    "global_accountant": [
        "users:read", "users:create", "users:update",
        "timelogs:read", "timelogs:admin_create",
        "schedules:read",
        "payroll:read", "payroll:create", "payroll:update", "payroll:export",
        "leaves:read",
        "companies:read",
        "reports:read", "reports:create", "reports:export", "analytics:read",
    ],
    "accountant": [
        "users:read", "users:create", "users:update",
        "timelogs:read", "timelogs:admin_create",
        "schedules:read",
        "payroll:read", "payroll:create", "payroll:update", "payroll:export",
        "leaves:read",
        "companies:read",
        "reports:read", "reports:create", "reports:export", "analytics:read",
    ],
    "hr_manager": [
        "users:read", "users:create", "users:update",
        "timelogs:read",
        "schedules:create", "schedules:read", "schedules:update",
        "leaves:read", "leaves:create", "leaves:approve", "leaves:update",
        "companies:read",
        "reports:read", "reports:create",
    ],
    "manager": [
        "users:read", "users:read_own",
        "timelogs:read", "timelogs:create_own",
        "schedules:read", "schedules:create", "schedules:update",
        "leaves:read", "leaves:create", "leaves:approve",
        "reports:read", "reports:create",
    ],
    "driver": [
        "users:read_own",
        "timelogs:create_own", "timelogs:read_own",
        "schedules:read_own",
    ],
    "employee": [
        "users:read_own",
        "timelogs:create_own", "timelogs:read_own",
        "schedules:read_own",
        "leaves:create_own", "leaves:read_own",
    ],
    "viewer": [
        "users:read",
        "timelogs:read",
        "schedules:read",
        "reports:read",
    ],
    "logistics_manager": [
        "logistics:suppliers:read", "logistics:suppliers:create", "logistics:suppliers:update", "logistics:suppliers:delete",
        "logistics:templates:read", "logistics:templates:create", "logistics:templates:update", "logistics:templates:delete",
        "logistics:requests:read", "logistics:requests:create", "logistics:requests:update", "logistics:requests:approve", "logistics:requests:delete",
        "logistics:orders:read", "logistics:orders:create", "logistics:orders:update", "logistics:orders:delete",
        "logistics:deliveries:read", "logistics:deliveries:create", "logistics:deliveries:update", "logistics:deliveries:delete",
        "reports:read", "reports:create", "reports:export",
    ],
    "fleet_manager": [
        "fleet:vehicles:read", "fleet:vehicles:create", "fleet:vehicles:update", "fleet:vehicles:delete", "fleet:vehicles:status",
        "fleet:documents:read", "fleet:documents:create", "fleet:documents:update", "fleet:documents:delete",
        "fleet:fuel_cards:read", "fleet:fuel_cards:create", "fleet:fuel_cards:update", "fleet:fuel_cards:delete",
        "fleet:vignettes:read", "fleet:vignettes:create", "fleet:vignettes:update", "fleet:vignettes:delete",
        "fleet:tolls:read", "fleet:tolls:create", "fleet:tolls:update", "fleet:tolls:delete",
        "fleet:mileage:read", "fleet:mileage:create", "fleet:mileage:update", "fleet:mileage:delete",
        "fleet:fuel:read", "fleet:fuel:create", "fleet:fuel:update", "fleet:fuel:delete",
        "fleet:repairs:read", "fleet:repairs:create", "fleet:repairs:update", "fleet:repairs:delete",
        "fleet:schedules:read", "fleet:schedules:create", "fleet:schedules:update", "fleet:schedules:delete",
        "fleet:insurances:read", "fleet:insurances:create", "fleet:insurances:update", "fleet:insurances:delete",
        "fleet:inspections:read", "fleet:inspections:create", "fleet:inspections:update", "fleet:inspections:delete",
        "fleet:drivers:read", "fleet:drivers:create", "fleet:drivers:update", "fleet:drivers:delete",
        "fleet:trips:read", "fleet:trips:create", "fleet:trips:update", "fleet:trips:delete",
        "fleet:expenses:read", "fleet:expenses:create", "fleet:expenses:update", "fleet:expenses:delete",
        "fleet:costcenters:read", "fleet:costcenters:create", "fleet:costcenters:update", "fleet:costcenters:delete",
        "fleet:reports:read", "fleet:reports:export",
    ],
}