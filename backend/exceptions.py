from fastapi import status
from typing import Optional, Any
from datetime import datetime


class CHRONOSException(Exception):
    """
    Базова грешка за CHRONOS.
    
    Полета:
    - status_code: HTTP status code
    - error_code: кратък код за парсиране ( напр. USER_NOT_FOUND)
    - detail: съобщение за потребителя
    - original_error: оригиналната грешка за chaining
    - context: допълнителни данни за debugging
    - timestamp: ISO timestamp на грешката
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    detail: str = "Вътрешна грешка"
    
    def __init__(
        self,
        detail: str = None,
        error_code: str = None,
        original_error: Exception = None,
        context: dict = None
    ):
        self.detail = detail or self.__class__.detail
        self.error_code = error_code or self.__class__.error_code
        self.original_error = original_error
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.detail)
    
    def to_dict(self) -> dict:
        """Конвертиране към dict за JSON response"""
        return {
            "error": self.error_code,
            "message": self.detail,
            "timestamp": self.timestamp,
            "context": self.context,
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.detail}"


class ErrorResponse:
    """
    Консистентен формат за грешки в API responses.
    """
    def __init__(
        self,
        error: str,
        message: str,
        timestamp: str,
        context: dict = None
    ):
        self.error = error
        self.message = message
        self.timestamp = timestamp
        self.context = context or {}
    
    def to_dict(self) -> dict:
        return {
            "error": self.error,
            "message": self.message,
            "timestamp": self.timestamp,
            "context": self.context,
        }


# =============================================================================
# NOT FOUND EXCEPTIONS
# =============================================================================

class NotFoundException(CHRONOSException):
    """Грешка когато ресурсът не е намерен"""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    detail = "Ресурсът не е намерен"
    
    @classmethod
    def user(cls, user_id: int = None, username: str = None):
        """Потребител не е намерен"""
        context = {}
        msg = "Потребител не е намерен"
        if user_id:
            msg += f" (ID: {user_id})"
            context["id"] = user_id
        if username:
            msg += f" ({username})"
            context["username"] = username
        context["resource"] = "user"
        return cls(detail=msg, error_code="USER_NOT_FOUND", context=context)
    
    @classmethod
    def vehicle(cls, vehicle_id: int = None, plate: str = None):
        """Превозно средство не е намерено"""
        context = {}
        msg = "Превозно средство не е намерено"
        if vehicle_id:
            msg += f" (ID: {vehicle_id})"
            context["id"] = vehicle_id
        if plate:
            msg += f" ({plate})"
            context["plate"] = plate
        context["resource"] = "vehicle"
        return cls(detail=msg, error_code="VEHICLE_NOT_FOUND", context=context)
    
    @classmethod
    def recipe(cls, recipe_id: int = None, name: str = None):
        """Рецепта не е намерена"""
        context = {}
        msg = "Рецепта не е намерена"
        if recipe_id:
            msg += f" (ID: {recipe_id})"
            context["id"] = recipe_id
        if name:
            msg += f" ({name})"
            context["name"] = name
        context["resource"] = "recipe"
        return cls(detail=msg, error_code="RECIPE_NOT_FOUND", context=context)
    
    @classmethod
    def ingredient(cls, ingredient_id: int = None, name: str = None):
        """Съставка не е намерена"""
        context = {}
        msg = "Съставка не е намерена"
        if ingredient_id:
            msg += f" (ID: {ingredient_id})"
            context["id"] = ingredient_id
        if name:
            msg += f" ({name})"
            context["name"] = name
        context["resource"] = "ingredient"
        return cls(detail=msg, error_code="INGREDIENT_NOT_FOUND", context=context)
    
    @classmethod
    def order(cls, order_id: int = None):
        """Поръчка не е намерена"""
        context = {}
        msg = "Поръчка не е намерена"
        if order_id:
            msg += f" (ID: {order_id})"
            context["id"] = order_id
        context["resource"] = "order"
        return cls(detail=msg, error_code="ORDER_NOT_FOUND", context=context)
    
    @classmethod
    def request(cls, request_id: int = None):
        """Заявка не е намерена"""
        context = {}
        msg = "Заявка не е намерена"
        if request_id:
            msg += f" (ID: {request_id})"
            context["id"] = request_id
        context["resource"] = "request"
        return cls(detail=msg, error_code="REQUEST_NOT_FOUND", context=context)
    
    @classmethod
    def session(cls, session_id: int = None):
        """Сесия не е намерена"""
        context = {}
        msg = "Сесия не е намерена"
        if session_id:
            msg += f" (ID: {session_id})"
            context["id"] = session_id
        context["resource"] = "session"
        return cls(detail=msg, error_code="SESSION_NOT_FOUND", context=context)
    
    @classmethod
    def record(cls, record_type: str, record_id: int = None):
        """Запис не е намерен"""
        msg = f"{record_type} не е намерен"
        context = {"resource": record_type.lower(), "record_type": record_type}
        if record_id:
            msg += f" (ID: {record_id})"
            context["id"] = record_id
        error_code = f"{record_type.upper().replace(' ', '_')}_NOT_FOUND"
        return cls(detail=msg, error_code=error_code, context=context)
    
    @classmethod
    def resource(cls, resource_type: str, resource_id: Any = None):
        """Generic resource not found"""
        msg = f"{resource_type} не е намерен"
        context = {"resource": resource_type.lower()}
        if resource_id:
            msg += f" (ID: {resource_id})"
            context["id"] = resource_id
        error_code = f"{resource_type.upper().replace(' ', '_')}_NOT_FOUND"
        return cls(detail=msg, error_code=error_code, context=context)


# =============================================================================
# PERMISSION DENIED EXCEPTIONS
# =============================================================================

class PermissionDeniedException(CHRONOSException):
    """Грешка при липса на права"""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "PERMISSION_DENIED"
    detail = "Нямате права за това действие"
    
    @classmethod
    def for_resource(cls, resource_type: str, action: str = "edit"):
        """Няма права за конкретен ресурс и действие"""
        actions = {
            "view": "преглеждате",
            "edit": "редактирате",
            "delete": "изтриете",
            "create": "създадете",
            "access": "достъпите",
        }
        action_text = actions.get(action, action)
        return cls(
            detail=f"Нямате права да {action_text} този {resource_type}",
            error_code=f"{resource_type.upper()}_{action.upper()}_FORBIDDEN",
            context={"resource": resource_type, "action": action}
        )
    
    @classmethod
    def for_action(cls, action: str):
        """Няма права за общо действие"""
        return cls(
            detail=f"Нямате права да извършите това действие: {action}",
            error_code="ACTION_FORBIDDEN",
            context={"action": action}
        )
    
    @classmethod
    def not_owner(cls, resource_type: str):
        """Не сте собственик на ресурса"""
        return cls(
            detail=f"Вие не сте собственик на този {resource_type}",
            error_code=f"{resource_type.upper()}_NOT_OWNER",
            context={"resource": resource_type}
        )


# =============================================================================
# VALIDATION EXCEPTIONS
# =============================================================================

class ValidationException(CHRONOSException):
    """Грешка при валидация"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    detail = "Невалидни данни"
    
    @classmethod
    def field(cls, field_name: str, reason: str = None):
        """Невалидно конкретно поле"""
        msg = f"Невалидно поле: {field_name}"
        if reason:
            msg += f" - {reason}"
        return cls(
            detail=msg,
            error_code="VALIDATION_FIELD_ERROR",
            context={"field": field_name, "reason": reason}
        )
    
    @classmethod
    def required_field(cls, field_name: str):
        """Задължително поле липсва"""
        return cls(
            detail=f"Задължителното поле '{field_name}' липсва",
            error_code="VALIDATION_REQUIRED_FIELD",
            context={"field": field_name, "required": True}
        )
    
    @classmethod
    def email(cls, reason: str = None):
        """Невалиден имейл"""
        msg = "Невалиден имейл адрес"
        if reason:
            msg += f": {reason}"
        return cls(
            detail=msg,
            error_code="VALIDATION_EMAIL_ERROR",
            context={"field": "email", "reason": reason}
        )
    
    @classmethod
    def password(cls, reason: str = None):
        """Невалидна парола"""
        msg = "Невалидна парола"
        if reason:
            msg += f": {reason}"
        return cls(
            detail=msg,
            error_code="VALIDATION_PASSWORD_ERROR",
            context={"field": "password", "reason": reason}
        )
    
    @classmethod
    def invalid_value(cls, field_name: str, value: Any, allowed_values: list = None):
        """Невалидна стойност"""
        msg = f"Невалидна стойност за '{field_name}': {value}"
        context = {"field": field_name, "value": value}
        if allowed_values:
            msg += f". Позволени стойности: {', '.join(map(str, allowed_values))}"
            context["allowed_values"] = allowed_values
        return cls(
            detail=msg,
            error_code="VALIDATION_INVALID_VALUE",
            context=context
        )


# =============================================================================
# DATABASE EXCEPTIONS
# =============================================================================

class DatabaseException(CHRONOSException):
    """Грешка в базата данни"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "DB_ERROR"
    detail = "Грешка в базата данни"
    
    @classmethod
    def duplicate(cls, resource: str = "Запис"):
        """Дублиращ се запис"""
        return cls(
            detail=f"{resource} вече съществува",
            error_code="DB_DUPLICATE_ERROR",
            context={"resource": resource, "type": "duplicate"}
        )
    
    @classmethod
    def foreign_key(cls, reference: str = None):
        """Нарушена foreign key референция"""
        msg = "Невалидна референция"
        if reference:
            msg += f": {reference}"
        return cls(
            detail=msg,
            error_code="DB_FOREIGN_KEY_ERROR",
            context={"reference": reference, "type": "foreign_key"}
        )
    
    @classmethod
    def constraint(cls, constraint_name: str = None):
        """Наруш constraint"""
        msg = "Нарушено е ограничение в базата данни"
        if constraint_name:
            msg += f": {constraint_name}"
        return cls(
            detail=msg,
            error_code="DB_CONSTRAINT_ERROR",
            context={"constraint": constraint_name, "type": "constraint"}
        )
    
    @classmethod
    def connection(cls, original_error: Exception = None):
        """Грешка при връзка с базата данни"""
        return cls(
            detail="Грешка при връзка с базата данни",
            error_code="DB_CONNECTION_ERROR",
            original_error=original_error,
            context={"type": "connection"}
        )


# =============================================================================
# AUTHENTICATION EXCEPTIONS
# =============================================================================

class AuthenticationException(CHRONOSException):
    """Грешка при автентикация"""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"
    detail = "Не сте автентикирани"
    
    @classmethod
    def invalid_credentials(cls):
        """Невалидни credentials"""
        return cls(
            detail="Невалиден имейл или парола",
            error_code="AUTH_INVALID_CREDENTIALS"
        )
    
    @classmethod
    def token_expired(cls):
        """Изтекъл токен"""
        return cls(
            detail="Сесията е изтекла. Моля, влезте отново.",
            error_code="AUTH_TOKEN_EXPIRED"
        )
    
    @classmethod
    def token_invalid(cls):
        """Невалиден токен"""
        return cls(
            detail="Невалиден токен за автентикация",
            error_code="AUTH_TOKEN_INVALID"
        )


# =============================================================================
# OTHER EXCEPTIONS
# =============================================================================

class DuplicateException(CHRONOSException):
    """Грешка при дублиращ се запис"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "DUPLICATE_ERROR"
    detail = "Записът вече съществува"
    
    @classmethod
    def with_name(cls, name: str, resource_type: str = "Запис"):
        """Дублиращ се запис с име"""
        return cls(
            detail=f"{resource_type} с име '{name}' вече съществува",
            error_code="DUPLICATE_NAME_ERROR",
            context={"name": name, "resource": resource_type}
        )


class InvalidOperationException(CHRONOSException):
    """Грешка при невалидна операция"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "INVALID_OPERATION"
    detail = "Невалидна операция"
    
    @classmethod
    def cannot_complete(cls, reason: str):
        """Операцията не може да бъде извършена"""
        return cls(
            detail=f"Операцията не може да бъде извършена: {reason}",
            error_code="OPERATION_CANNOT_COMPLETE",
            context={"reason": reason}
        )


class RetentionPeriodException(CHRONOSException):
    """Грешка при опит за изтриване на документ в давностен период"""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "RETENTION_PERIOD_VIOLATION"
    detail = "Документът не може да бъде изтрит"
    years = 10
    
    def __init__(self, *args, years: int = None, **kwargs):
        super().__init__(*args, **kwargs)
        if years is not None:
            self.years = years
    
    def to_dict(self) -> dict:
        return {
            "error": self.error_code,
            "message": self.detail,
            "timestamp": self.timestamp,
            "context": {
                "years": self.years,
                **self.context
            }
        }
    
    @classmethod
    def invoice(cls, invoice_id: int, years: int = 10):
        """Изтриване на фактура преди изтичане на давностния период"""
        return cls(
            detail=f"Фактура (ID: {invoice_id}) не може да бъде изтрита. Законова давност: {years} години",
            error_code="INVOICE_RETENTION_VIOLATION",
            context={"resource": "invoice", "id": invoice_id},
            years=years
        )
    
    @classmethod
    def cash_receipt(cls, receipt_id: int, years: int = 10):
        """Изтриване на касов ордер преди изтичане на давностния период"""
        return cls(
            detail=f"Касов ордер (ID: {receipt_id}) не може да бъде изтрит. Законова давност: {years} години",
            error_code="CASH_RECEIPT_RETENTION_VIOLATION",
            context={"resource": "cash_receipt", "id": receipt_id},
            years=years
        )
    
    @classmethod
    def cash_journal_entry(cls, entry_id: int, years: int = 10):
        """Изтриване на касова книга преди изтичане на давностния период"""
        return cls(
            detail=f"Запис от касова книга (ID: {entry_id}) не може да бъде изтрит. Законова давност: {years} години",
            error_code="CASH_JOURNAL_RETENTION_VIOLATION",
            context={"resource": "cash_journal_entry", "id": entry_id},
            years=years
        )
    
    @classmethod
    def bank_transaction(cls, transaction_id: int, years: int = 10):
        """Изтриване на банкова транзакция преди изтичане на давностния период"""
        return cls(
            detail=f"Банкова транзакция (ID: {transaction_id}) не може да бъде изтрита. Законова давност: {years} години",
            error_code="BANK_TRANSACTION_RETENTION_VIOLATION",
            context={"resource": "bank_transaction", "id": transaction_id},
            years=years
        )


# =============================================================================
# BACKWARDS COMPATIBLE ALIASES
# =============================================================================

# Функции за съвместимост със съществуващия код
def not_found(detail: str = None, resource_type: str = None, resource_id: Any = None):
    """Alias за backwards compatibility"""
    if resource_type and resource_id:
        return NotFoundException.resource(resource_type, resource_id)
    if resource_type:
        return NotFoundException.resource(resource_type)
    return NotFoundException(detail=detail or "Ресурсът не е намерен")


def bad_request(detail: str = None):
    """Alias за backwards compatibility"""
    return ValidationException(detail=detail or "Невалидни данни")


def permission_denied(detail: str = None):
    """Alias за backwards compatibility"""
    return PermissionDeniedException(detail=detail or "Нямате права за това действие")


def unauthorized(detail: str = None):
    """Alias за backwards compatibility"""
    return AuthenticationException(detail=detail or "Не сте автентикирани")


def internal_server_error(detail: str = None):
    """Alias за backwards compatibility"""
    return CHRONOSException(detail=detail or "Вътрешна грешка на сървъра")


# Запазване на оригиналните функции от error_handling.py
# Тези ще бъдат премахнати след пълна миграция
def get_error_message(error: Exception) -> str:
    """Извличане на потребителско съобщение от грешка"""
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
