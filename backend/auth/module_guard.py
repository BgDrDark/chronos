from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.database import get_db
from backend.services.module_service import ModuleService
import logging

logger = logging.getLogger(__name__)

class ModuleDisabledException(Exception):
    """Custom exception when a module is disabled."""
    def __init__(self, module_code: str):
        self.module_code = module_code
        self.message = f"МОДУЛЪТ Е ДЕАКТИВИРАН: Модул '{module_code}' е деактивиран от администратор."
        super().__init__(self.message)

def require_module(module_code: str):
    """
    Decorator to ensure a module is enabled before allowing access to an endpoint.
    Expects 'db' to be present in the function arguments (usually via Depends).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = kwargs.get('db')
            if not db:
                # If db is not in kwargs, it might be in args or we need to get it from Depends
                # For FastAPI, it's usually passed as a kwarg
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session required for module check"
                )
            
            is_enabled = await ModuleService.is_enabled(db, module_code)
            if not is_enabled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Module Disabled",
                        "message": f"Модулът '{module_code}' е деактивиран от администратор.",
                        "module_code": module_code
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_module_dep(module_code: str):
    """
    FastAPI dependency factory to ensure a module is enabled.
    Usage: router = APIRouter(dependencies=[Depends(require_module_dep("module_name"))])
    """
    async def dependency(db: AsyncSession = Depends(get_db)):
        is_enabled = await ModuleService.is_enabled(db, module_code)
        if not is_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Module Disabled",
                    "message": f"Модулът '{module_code}' е деактивиран от администратор.",
                    "module_code": module_code
                }
            )
    return dependency

async def check_module_enabled(module_code: str, db: AsyncSession):
    """Utility function for manual module checks within functions."""
    is_enabled = await ModuleService.is_enabled(db, module_code)
    if not is_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Module '{module_code}' is disabled"
        )

async def verify_module_enabled(module_code: str, db: AsyncSession):
    """Utility function for GraphQL resolvers. Raises ModuleDisabledException instead of generic Exception."""
    is_enabled = await ModuleService.is_enabled(db, module_code)
    if not is_enabled:
        raise ModuleDisabledException(module_code)
