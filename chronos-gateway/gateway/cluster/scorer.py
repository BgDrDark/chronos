import psutil
import platform
import logging

logger = logging.getLogger(__name__)

def calculate_hardware_score() -> int:
    """
    Изчислява 'рейтинг на мощност' на машината.
    Формула: (Ядра * 1000) + (RAM_GB * 500)
    """
    try:
        # 1. Брой логически ядра
        cores = psutil.cpu_count(logical=True) or 1
        
        # 2. Обща RAM памет в GB
        ram_bytes = psutil.virtual_memory().total
        ram_gb = round(ram_bytes / (1024**3))
        
        # 3. Изчисляване на скор
        score = (cores * 1000) + (ram_gb * 500)
        
        logger.info(f"Hardware Score Calculated: {score} (Cores: {cores}, RAM: {ram_gb}GB)")
        return score
    except Exception as e:
        logger.error(f"Failed to calculate hardware score: {e}")
        return 1000 # Default fallback score

def get_mac_address_value() -> int:
    """Връща MAC адреса като число за tie-breaker"""
    try:
        from gateway.core.hardware_id import get_mac_address
        mac = get_mac_address().replace(':', '').replace('-', '')
        return int(mac, 16)
    except:
        return 0
