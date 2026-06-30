import hashlib

from cryptography.fernet import Fernet

from backend.config import settings


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY not configured")
    return Fernet(key.encode())


def encrypt_pin(pin: str) -> str:
    f = _get_fernet()
    return f.encrypt(pin.encode()).decode()


def decrypt_pin(encrypted: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def hash_pin_sha256(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()
