import logging
from typing import Optional, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def get_error_message(error: Exception) -> str:
    """
    Извличане на потребителско съобщение от грешка.
    Поддържа различни типове грешки.
    """
    if hasattr(error, 'detail'):
        detail = error.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict) and 'message' in detail:
            return detail['message']
    
    if hasattr(error, 'message'):
        return str(error.message)
    
    if hasattr(error, 'args') and error.args:
        return str(error.args[0])
    
    return str(error)


def handle_db_error(error: Exception) -> Exception:
    """
    Обработка на грешки от базата данни.
    Връща DatabaseException с коректен error_code и съобщение.
    
    Забележка: Сега връща DatabaseException вместо HTTPException,
    тъй като exception_handler в main.py автоматично го конвертира.
    """
    from backend.exceptions import DatabaseException
    
    error_str = str(error).lower()
    
    if "duplicate key" in error_str or "unique constraint" in error_str:
        return DatabaseException.duplicate("Запис")
    
    if "foreign key" in error_str:
        return DatabaseException.foreign_key("референция")
    
    if "not null" in error_str:
        return DatabaseException.constraint("Задължително поле липсва")
    
    if "check constraint" in error_str:
        return DatabaseException.constraint("Проверка за валидност")
    
    logger.error(f"Database error: {error}")
    return DatabaseException(
        detail="Грешка в базата данни",
        original_error=error
    )


def handle_validation_error(error: Exception) -> Exception:
    """
    Обработка на грешки при валидация.
    Връща ValidationException.
    """
    from backend.exceptions import ValidationException
    
    return ValidationException(detail=get_error_message(error))


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """Логиране на грешка с контекст"""
    if context:
        logger.error(f"{context}: {error}", exc_info=True)
    else:
        logger.error(str(error), exc_info=True)


# =============================================================================
# BACKWARDS COMPATIBILITY - DEPRECATED
# =============================================================================
# Следните функции са deprecated и ще бъдат премахнати.
# Използвай директно exceptions.py

def permission_denied(detail: str = "Нямате права за това действие") -> HTTPException:
    """DEPRECATED: Използвай PermissionDeniedException"""
    from backend.exceptions import PermissionDeniedException
    return PermissionDeniedException(detail=detail)


def not_found(detail: str = "Ресурсът не е намерен") -> HTTPException:
    """DEPRECATED: Използвай NotFoundException"""
    from backend.exceptions import NotFoundException
    return NotFoundException(detail=detail)


def bad_request(detail: str = "Невалидни данни") -> HTTPException:
    """DEPRECATED: Използвай ValidationException"""
    from backend.exceptions import ValidationException
    return ValidationException(detail=detail)


def unauthorized(detail: str = "Не сте автентикирани") -> HTTPException:
    """DEPRECATED: Използвай AuthenticationException"""
    from backend.exceptions import AuthenticationException
    return AuthenticationException(detail=detail)


def internal_server_error(detail: str = "Вътрешна грешка на сървъра") -> HTTPException:
    """DEPRECATED: Използвай CHRONOSException"""
    from backend.exceptions import CHRONOSException
    return CHRONOSException(detail=detail)
