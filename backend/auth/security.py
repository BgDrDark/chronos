from passlib.context import CryptContext
from fastapi import Request
from cryptography.fernet import Fernet
from backend.config import settings
import os
import re # For regex password validation

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend import crud # Import crud for global settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

async def validate_password_complexity(db: AsyncSession, password: str):
    """
    Validate password complexity based on global settings.
    Raises ValueError with descriptive message if validation fails.
    """
    min_len = int(await crud.get_global_setting(db, "pwd_min_length") or "8")
    max_len = int(await crud.get_global_setting(db, "pwd_max_length") or "32")
    req_upper = (await crud.get_global_setting(db, "pwd_require_upper") or "false") == "true"
    req_lower = (await crud.get_global_setting(db, "pwd_require_lower") or "false") == "true"
    req_digit = (await crud.get_global_setting(db, "pwd_require_digit") or "false") == "true"
    req_special = (await crud.get_global_setting(db, "pwd_require_special") or "false") == "true"
    
    if len(password) < min_len:
        raise ValueError(f"Паролата трябва да е поне {min_len} символа.")
    if len(password) > max_len:
        raise ValueError(f"Паролата не може да бъде по-дълга от {max_len} символа.")
    
    if req_upper and not any(c.isupper() for c in password):
        raise ValueError("Паролата трябва да съдържа поне една главна буква.")
    if req_lower and not any(c.islower() for c in password):
        raise ValueError("Паролата трябва да съдържа поне една малка буква.")
    if req_digit and not any(c.isdigit() for c in password):
        raise ValueError("Паролата трябва да съдържа поне една цифра.")
    if req_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Паролата трябва да съдържа поне един специален символ (!@#$%^&*...).")

# Initialize Fernet with ENCRYPTION_KEY from settings
# NO FALLBACK - key MUST be provided in .env (or auto-generated)

def get_cipher_suite() -> Fernet:
    """
    Initialize Fernet cipher with ENCRYPTION_KEY from settings.
    Raises RuntimeError if key is not configured.
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY не е дефиниран в .env! "
            "Генерирай с: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(key.encode())
    except Exception as e:
        raise RuntimeError(f"Невалиден ENCRYPTION_KEY: {e}")

# Initialize cipher suite at module load time
try:
    cipher_suite = get_cipher_suite()
except RuntimeError as e:
    print(f"ERROR: {e}")
    cipher_suite = None


def encrypt_data(data: str) -> str:
    if not data: return None
    if not cipher_suite:
        raise RuntimeError("ENCRYPTION_KEY не е конфигуриран. Моля, добавете го в .env")
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data: return None
    if not cipher_suite:
        raise RuntimeError("ENCRYPTION_KEY не е конфигуриран. Моля, добавете го в .env")
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return "[Decryption Error]"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_client_ip(request: Request) -> str:
    """
    Извлича реалния IP адрес на клиента, като взема предвид прокси сървъри.
    Приоритет: Cloudflare (CF-Connecting-IP) -> X-Forwarded-For -> X-Real-IP -> client.host
    """
    # 1. Cloudflare специфичен хедър (най-надежден при ползване на CF)
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    
    # 2. Стандартен Forwarded хедър (може да съдържа списък, вземаме първия)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # 3. X-Real-IP хедър (често задаван от Nginx Proxy Manager)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
        
    # 4. Директна връзка (ако няма прокси)
    return request.client.host if request.client else "unknown"