import hmac
import hashlib
import time
import base64
import os

def generate_qr_secret():
    """Генерира случаен таен ключ за потребителя"""
    return base64.b32encode(os.urandom(20)).decode('utf-8')

def get_dynamic_qr_token(secret: str, interval: int = 30):
    """
    Генерира 8-цифрен динамичен код, базиран на времето (подобно на TOTP).
    """
    if not secret:
        return None
        
    # Нормализираме времето до текущия интервал
    counter = int(time.time() / interval)
    counter_bytes = counter.to_bytes(8, byteorder='big')
    
    # HMAC-SHA256
    secret_bytes = base64.b32decode(secret)
    h = hmac.new(secret_bytes, counter_bytes, hashlib.sha256).digest()
    
    # Динамично отместване (Truncation)
    offset = h[-1] & 0x0F
    code = (int.from_bytes(h[offset:offset+4], byteorder='big') & 0x7FFFFFFF) % 100000000
    
    # Връщаме 8-цифрен низ с водещи нули
    return str(code).zfill(8)

def verify_dynamic_qr_token(secret: str, token: str, window: int = 1):
    """
    Проверява токена с малък прозорец за толеранс (предишен/следващ интервал).
    """
    if not secret or not token:
        return False
        
    for i in range(-window, window + 1):
        # Генерираме код за отместения брояч
        counter = int(time.time() / 30) + i
        counter_bytes = counter.to_bytes(8, byteorder='big')
        
        secret_bytes = base64.b32decode(secret)
        h = hmac.new(secret_bytes, counter_bytes, hashlib.sha256).digest()
        
        offset = h[-1] & 0x0F
        code = (int.from_bytes(h[offset:offset+4], byteorder='big') & 0x7FFFFFFF) % 100000000
        
        if str(code).zfill(8) == token:
            return True
            
    return False
