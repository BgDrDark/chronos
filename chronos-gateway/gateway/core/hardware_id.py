import hashlib
import uuid
import platform
import subprocess
import os
import sys
from pathlib import Path

CONFIG_DIR = Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'ChronosGateway'


def get_hardware_uuid() -> str:
    """
    Генерира уникален хардуерен идентификатор базиран на:
    - Motherboard serial
    - CPU ID
    - BIOS UUID
    - Primary MAC address
    
    Това UUID е обвързано с хардуера и не може да се копира.
    """
    
    components = []
    
    if sys.platform == 'win32':
        mb_serial = _get_wmi_info("Win32_BaseBoard", "SerialNumber")
        if mb_serial:
            components.append(mb_serial)
        
        bios_uuid = _get_wmi_info("Win32_ComputerSystemProduct", "UUID")
        if bios_uuid:
            components.append(bios_uuid)
        
        cpu_id = _get_cpu_id()
        if cpu_id:
            components.append(cpu_id)
        
        mac = _get_primary_mac()
        if mac:
            components.append(mac)
    else:
        mac = _get_primary_mac()
        if mac:
            components.append(mac)
        
        try:
            with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                components.append(f.read().strip())
        except:
            pass
    
    if not components:
        return _get_or_create_fallback_uuid()
    
    combined = "|".join(components)
    hw_uuid = hashlib.sha256(combined.encode()).hexdigest()[:64]
    
    return hw_uuid


def _get_wmi_info(wmi_class: str, attribute: str) -> str:
    """Извлича информация от WMI (Windows)"""
    if sys.platform != 'win32':
        return None
        
    try:
        result = subprocess.run(
            ["powershell", "-Command", 
             f"Get-WmiObject -Class {wmi_class} | "
             f"Select-Object -ExpandProperty {attribute}"],
            capture_output=True, text=True, timeout=5
        )
        value = result.stdout.strip()
        if value and value != "None" and value.upper() != "TO BE FILLED BY O.E.M.":
            return value
    except:
        pass
    return None


def _get_cpu_id() -> str:
    """CPU ID чрез WMI"""
    return _get_wmi_info("Win32_Processor", "ProcessorId")


def _get_primary_mac() -> str:
    """Първи MAC адрес"""
    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ["powershell", "-Command", 
                 "Get-NetAdapter | Where-Object Status -eq 'Up' | "
                 "Select-Object -First 1 -ExpandProperty MacAddress"],
                capture_output=True, text=True, timeout=5
            )
            mac = result.stdout.strip()
            if mac:
                return mac.replace('-', ':')
        except:
            pass
    else:
        try:
            mac = os.popen("cat /sys/class/net/*/address 2>/dev/null | head -1").read().strip()
            if mac:
                return mac
        except:
            pass
    return None


def _get_or_create_fallback_uuid() -> str:
    """Fallback: генерира и запазва UUID"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    uuid_file = CONFIG_DIR / 'machine.uuid'
    
    if uuid_file.exists():
        return uuid_file.read_text().strip()
    
    new_uuid = uuid.uuid4().hex
    uuid_file.write_text(new_uuid)
    return new_uuid


def get_mac_address() -> str:
    """Връща MAC адреса на първия мрежов интерфейс"""
    return _get_primary_mac() or "unknown"


if __name__ == "__main__":
    print(f"Hardware UUID: {get_hardware_uuid()}")
