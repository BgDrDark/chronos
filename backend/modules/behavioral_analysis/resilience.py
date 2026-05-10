import logging
import time
from functools import wraps
from typing import Callable, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class CircuitBreakerError(Exception):
    """Raised when a circuit breaker is open and execution is blocked"""
    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)
        self.message = message

class CircuitBreaker:
    """Circuit breaker for behavioral analysis computations"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    logger.info("Circuit breaker moving to half-open state")
                    self.state = "half-open"
                else:
                    raise CircuitBreakerError("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e

        return wrapper

    def _on_success(self):
        self.failure_count = 0
        self.state = "closed"
        logger.debug("Circuit breaker reset to closed state")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

# Global instance for behavioral analysis
ba_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)

async def safe_execute(func: Callable, fallback: Any = None, *args, **kwargs) -> Any:
    """Execute a function with circuit breaker protection"""
    try:
        return await ba_circuit_breaker.call(func)(*args, **kwargs)
    except CircuitBreakerError:
        logger.error("Behavioral analysis circuit breaker open, using fallback")
        return fallback
    except Exception as e:
        logger.error(f"Behavioral analysis execution failed: {e}")
        return fallback
