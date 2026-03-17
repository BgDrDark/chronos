from fastapi import status


class CHRONOSException(Exception):
    """Базова грешка за CHRONOS"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Вътрешна грешка"

    def __init__(self, detail: str = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class PermissionDeniedException(CHRONOSException):
    """Грешка при липса на права"""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Нямате права за това действие"


class NotFoundException(CHRONOSException):
    """Грешка когато ресурсът не е намерен"""
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Ресурсът не е намерен"


class ValidationException(CHRONOSException):
    """Грешка при валидация"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Невалидни данни"


class DatabaseException(CHRONOSException):
    """Грешка в базата данни"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Грешка в базата данни"


class AuthenticationException(CHRONOSException):
    """Грешка при автентикация"""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Не сте автентикирани"


class DuplicateException(CHRONOSException):
    """Грешка при дублиращ се запис"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Записът вече съществува"


class InvalidOperationException(CHRONOSException):
    """Грешка при невалидна операция"""
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Невалидна операция"
