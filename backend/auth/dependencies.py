from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.auth.rbac_service import PermissionService
from backend.auth.jwt_utils import get_current_user
from backend.database.database import get_db
from backend.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user_required(
    current_user: User = Depends(get_current_user)
) -> User:
    """Alias за get_current_user - всички protected endpoints го използват"""
    return current_user


def require_permission(permission: str):
    """
    Декоратор/зависимост за проверка на разрешения.
    
    Използване:
    
    @router.post("/endpoint")
    async def create_something(
        current_user: User = Depends(require_permission("timelogs:create"))
    ):
        ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user_required),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        perm_service = PermissionService(db)
        has_perm = await perm_service.check_permission(
            current_user.id, 
            permission,
            company_id=getattr(current_user, 'company_id', None)
        )
        
        if not has_perm:
            await perm_service.log_permission_decision(
                user_id=current_user.id,
                permission=permission,
                decision=False
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Нямате разрешение за: {permission}"
            )
        
        await perm_service.log_permission_decision(
            user_id=current_user.id,
            permission=permission,
            decision=True
        )
        
        return current_user
    
    return permission_checker
