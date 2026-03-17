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


def handle_db_error(error: Exception) -> HTTPException:
    """
    Обработка на грешки от базата данни.
    Връща HTTPException с коректен status code и съобщение.
    """
    error_str = str(error).lower()
    
    if "duplicate key" in error_str:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Записът вече съществува"
        )
    
    if "foreign key" in error_str:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидна референция"
        )
    
    if "not null" in error_str:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задължително поле липсва"
        )
    
    if "unique constraint" in error_str:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Записът вече съществува"
        )
    
    if "check constraint" in error_str:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидна стойност"
        )
    
    logger.error(f"Database error: {error}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Грешка в базата данни"
    )


def handle_validation_error(error: Exception) -> HTTPException:
    """Обработка на грешки при валидация"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=get_error_message(error)
    )


def permission_denied(detail: str = "Нямате права за това действие") -> HTTPException:
    """Създаване на HTTPException за липса на права"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def not_found(detail: str = "Ресурсът не е намерен") -> HTTPException:
    """Създаване на HTTPException за ненамерен ресурс"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def bad_request(detail: str = "Невалидни данни") -> HTTPException:
    """Създаване на HTTPException за лоша заявка"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def unauthorized(detail: str = "Не сте автентикирани") -> HTTPException:
    """Създаване на HTTPException за неавтентикиран потребител"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail
    )


def internal_server_error(detail: str = "Вътрешна грешка на сървъра") -> HTTPException:
    """Създаване на HTTPException за вътрешна грешка"""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """Логиране на грешка с контекст"""
    if context:
        logger.error(f"{context}: {error}", exc_info=True)
    else:
        logger.error(str(error), exc_info=True)
