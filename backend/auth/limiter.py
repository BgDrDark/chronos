import time
from collections import defaultdict

from slowapi import Limiter

from backend.auth.security import get_client_ip

limiter = Limiter(key_func=get_client_ip)


class APIKeyRateLimiter:
    """In-memory sliding window rate limiter for API key authentication."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, api_key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[api_key] = [t for t in self._requests[api_key] if t > cutoff]
        if len(self._requests[api_key]) >= self.max_requests:
            return False
        self._requests[api_key].append(now)
        return True

    def get_remaining(self, api_key: str) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[api_key] = [t for t in self._requests[api_key] if t > cutoff]
        return max(0, self.max_requests - len(self._requests[api_key]))


api_key_limiter = APIKeyRateLimiter()
