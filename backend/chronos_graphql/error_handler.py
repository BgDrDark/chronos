import logging

from graphql import GraphQLError
from strawberry.extensions import Extension
from strawberry.types import ExecutionResult

from backend.exceptions import (
    AuthenticationException,
    CHRONOSException,
    PermissionDeniedException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class ChronosErrorExtension(Extension):
    """Strawberry GraphQL extension for error handling
    
    This extension intercepts errors during GraphQL execution and converts them
    to CHRONOSException format for consistent API responses.
    """

    async def on_error(self, error: Exception) -> Exception:
        """Handle errors during GraphQL execution"""
        if isinstance(error, AuthenticationException):
            logger.warning(f"Authentication error in GraphQL: {error}")
            return error

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
            error_code="INTERNAL_ERROR",
        )


def process_chronos_errors(result: ExecutionResult) -> None:
    """Add CHRONOSException context to GraphQL error extensions.
    
    Call this after schema.execute() to enrich error responses with
    field-level context for frontend form validation.
    """
    if not result.errors:
        return
    
    new_errors = []
    for err in result.errors:
        orig = err.original_error
        if isinstance(orig, CHRONOSException):
            new_errors.append(GraphQLError(
                message=str(orig),
                locations=err.locations,
                path=err.path,
                extensions={
                    "errorCode": orig.error_code,
                    "context": orig.context,
                    "timestamp": orig.timestamp,
                },
            ))
        else:
            new_errors.append(err)
    
    result.errors = new_errors
