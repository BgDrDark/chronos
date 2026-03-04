from slowapi import Limiter
from backend.auth.security import get_client_ip

limiter = Limiter(key_func=get_client_ip)
