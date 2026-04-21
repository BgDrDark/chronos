import logging
from strawberry.extensions import Extension
from starlette.responses import JSONResponse
from backend.exceptions import (
    CHRONOSException,
    ValidationException,
    PermissionDeniedException
)

logger = logging.getLogger(__name__)


class ChronosErrorExtension(Extension):
    """Strawberry GraphQL extension for error handling
    
    This extension intercepts errors during GraphQL execution and converts them
    to CHRONOSException format for consistent API responses.
    """
    
    async def on_error(self, error: Exception) -> Exception:
        """Handle errors during GraphQL execution"""
        
        if isinstance(error, CHRONOSException):
            logger.warning(f"CHRONOS error in GraphQL: {error}")
            return error
        
        if isinstance(error, ValidationException):
            logger.warning(f"Validation error in GraphQL: {error}")
            return error
        
        if isinstance(error, PermissionDeniedException):
            logger.warning(f"Permission error in GraphQL: {error}")
            return error
        
        if isinstance(error, ValueError):
            logger.warning(f"Value error in GraphQL: {error}")
            return ValidationException(detail=str(error))
        
        if isinstance(error, PermissionError):
            logger.warning(f"Permission error in GraphQL: {error}")
            return PermissionDeniedException(detail=str(error))
        
        # Unknown error
        logger.error(f"Unexpected GraphQL error: {error}", exc_info=True)
        return CHRONOSException(
            detail="Вътрешна грешка",
            error_code="INTERNAL_ERROR"
        )
