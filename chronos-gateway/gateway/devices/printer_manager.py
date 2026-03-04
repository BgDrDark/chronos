import socket
import logging
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PrinterManager:
    """
    Управление на принтери
    
    Поддържа:
    - Network printers (RAW, LPD)
    - USB printers
    - Windows shared printers
    """
    
    def __init__(self):
        self.printers: Dict[str, dict] = {}
    
    def add_printer(
        self,
        printer_id: str,
        name: str,
        printer_type: str,
        ip_address: Optional[str] = None,
        port: int = 9100,
        protocol: str = "raw",
        windows_name: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        is_default: bool = False
    ) -> dict:
        """Добавяне на принтер"""
        if is_default:
            for p in self.printers.values():
                p["is_default"] = False
        
        self.printers[printer_id] = {
            "id": printer_id,
            "name": name,
            "type": printer_type,  # "network", "usb", "windows"
            "ip_address": ip_address,
            "port": port,
            "protocol": protocol,
            "windows_name": windows_name,
            "manufacturer": manufacturer,
            "model": model,
            "is_default": is_default,
            "is_active": True,
            "last_test": None,
            "last_error": None,
        }
        
        return self.printers[printer_id]
    
    def remove_printer(self, printer_id: str) -> bool:
        """Премахва принтер"""
        return self.printers.pop(printer_id, None) is not None
    
    def get_printer(self, printer_id: str) -> Optional[dict]:
        """Връща принтер"""
        return self.printers.get(printer_id)
    
    def get_default_printer(self) -> Optional[dict]:
        """Връща подразбиращия се принтер"""
        for printer in self.printers.values():
            if printer.get("is_default"):
                return printer
        
        if self.printers:
            return next(iter(self.printers.values()))
        return None
    
    def set_default(self, printer_id: str) -> bool:
        """Задава подразбиращ принтер"""
        if printer_id not in self.printers:
            return False
        
        for p in self.printers.values():
            p["is_default"] = False
        
        self.printers[printer_id]["is_default"] = True
        return True
    
    def get_all_printers(self) -> List[dict]:
        """Връща всички принтери"""
        return list(self.printers.values())
    
    def print_data(self, printer_id: str, data: bytes) -> bool:
        """Принтиране на данни"""
        printer = self.printers.get(printer_id)
        if not printer:
            logger.error(f"Printer {printer_id} not found")
            return False
        
        if not printer.get("is_active", True):
            logger.error(f"Printer {printer_id} is inactive")
            return False
        
        try:
            if printer["type"] == "network":
                success = self._print_network(printer, data)
            elif printer["type"] == "windows":
                success = self._print_windows(printer, data)
            elif printer["type"] == "usb":
                success = self._print_usb(printer, data)
            else:
                logger.error(f"Unknown printer type: {printer['type']}")
                return False
            
            if success:
                printer["last_error"] = None
            else:
                printer["last_error"] = "Print failed"
            
            return success
            
        except Exception as e:
            logger.error(f"Print error: {e}")
            printer["last_error"] = str(e)
            return False
    
    def _print_network(self, printer: dict, data: bytes) -> bool:
        """Принтиране към мрежов принтер"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((printer["ip_address"], printer["port"]))
                sock.sendall(data)
            logger.info(f"Printed to network printer: {printer['name']}")
            return True
        except socket.timeout:
            logger.error(f"Network printer timeout: {printer['ip_address']}")
            return False
        except ConnectionRefusedError:
            logger.error(f"Network printer refused connection: {printer['ip_address']}")
            return False
        except Exception as e:
            logger.error(f"Network print error: {e}")
            return False
    
    def _print_windows(self, printer: dict, data: bytes) -> bool:
        """Принтиране чрез Windows Print Spooler"""
        if sys.platform != 'win32':
            logger.error("Windows print only available on Windows")
            return False
        
        try:
            import win32print
            import win32api
            
            hprinter = win32print.OpenPrinter(printer["windows_name"])
            try:
                job = win32print.StartDocPrinter(
                    hprinter, 1, ("Chronos Receipt", None, "RAW")
                )
                try:
                    win32print.WritePrinter(hprinter, data)
                finally:
                    win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            
            logger.info(f"Printed to Windows printer: {printer['name']}")
            return True
        except ImportError:
            logger.error("win32print module not available")
            return False
        except Exception as e:
            logger.error(f"Windows print error: {e}")
            return False
    
    def _print_usb(self, printer: dict, data: bytes) -> bool:
        """USB принтиране"""
        logger.warning("USB printing not fully implemented")
        return False
    
    def test_printer(self, printer_id: str) -> dict:
        """Тест на принтер"""
        printer = self.printers.get(printer_id)
        if not printer:
            return {"status": "error", "message": "Printer not found"}
        
        test_data = b"\x1B@\x1B\x61\x01--- TEST PRINT ---\x1B\x64\x03\n"
        
        success = self.print_data(printer_id, test_data)
        
        printer["last_test"] = datetime.utcnow()
        
        return {
            "status": "success" if success else "error",
            "printer_id": printer_id,
            "printer_name": printer["name"],
        }
    
    def get_status(self) -> dict:
        """Връща статус на всички принтери"""
        active = sum(1 for p in self.printers.values() if p.get("is_active", True))
        
        return {
            "total": len(self.printers),
            "active": active,
            "printers": list(self.printers.values())
        }


import sys
