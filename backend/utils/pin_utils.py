import base64
import hashlib
import hmac
import os

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


PIN_ITERATIONS = 200_000


def hash_pin(pin: str) -> str:
    """Return a salted PBKDF2 hash in the form ``pbkdf2$iterations$salt$hash``."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, PIN_ITERATIONS)
    salt_b64 = base64.b64encode(salt).decode()
    digest_b64 = base64.b64encode(digest).decode()
    return f"pbkdf2${PIN_ITERATIONS}${salt_b64}${digest_b64}"


def verify_pin(pin: str, stored: str | None) -> bool:
    """Verify a PIN against a PBKDF2 hash or a legacy unsalted SHA-256 hash."""
    if not stored:
        return False

    if stored.startswith("pbkdf2$"):
        try:
            _, iterations, salt_b64, hash_b64 = stored.split("$")
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(hash_b64)
            actual = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, int(iterations))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(actual, expected)

    # Legacy: unsalted SHA-256
    return hmac.compare_digest(hashlib.sha256(pin.encode()).hexdigest(), stored)
