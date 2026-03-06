import logging
import random
import string
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AccessCode:
    """Код за еднократен достъп"""
    code: str
    code_type: str = "one_time"
    zones: List[str] = field(default_factory=list)
    uses_remaining: int = 1
    expires_at: Optional[datetime] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    active: bool = True
    
    def is_valid(self) -> Tuple[bool, str]:
        """Проверява дали кодът е валиден"""
        if not self.active:
            return False, "Кодът е деактивиран"
        
        if self.expires_at and datetime.now() > self.expires_at:
            return False, "Кодът е изтекъл"
        
        if self.uses_remaining == 0:
            return False, "Кодът е използван"
        
        return True, "OK"
    
    def can_access_zone(self, zone_id: str) -> Tuple[bool, str]:
        """Проверява дали кодът има достъп до зоната"""
        if not self.zones:
            return True, "OK"
        
        if zone_id in self.zones:
            return True, "OK"
        
        return False, f"Кодът няма достъп до зона {zone_id}"
    
    def use(self) -> bool:
        """Отбелязва кода като използван"""
        valid, _ = self.is_valid()
        if not valid:
            return False
        
        if self.code_type == "one_time":
            self.uses_remaining = 0
        elif self.code_type == "daily":
            pass
        else:
            self.uses_remaining -= 1
        
        self.last_used_at = datetime.now()
        return True
    
    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "code_type": self.code_type,
            "zones": self.zones,
            "uses_remaining": self.uses_remaining,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AccessCode':
        expires_at = data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        
        created_at = data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        last_used_at = data.get("last_used_at")
        if last_used_at:
            if isinstance(last_used_at, str):
                last_used_at = datetime.fromisoformat(last_used_at.replace("Z", "+00:00"))
        
        return cls(
            code=data.get("code", ""),
            code_type=data.get("code_type", "one_time"),
            zones=data.get("zones", []),
            uses_remaining=data.get("uses_remaining", 1),
            expires_at=expires_at,
            created_by=data.get("created_by", ""),
            created_at=created_at or datetime.now(),
            last_used_at=last_used_at,
            active=data.get("active", True)
        )


class CodeManager:
    """
    Мениджър на еднократните кодове за достъп
    
    Поддържа типове кодове:
    - one_time: Еднократно използване
    - daily: Валиден за целия ден
    - guest: Валиден за X часа
    - permanent: Постоянен код
    """
    
    def __init__(self, prefix: str = "G"):
        self.codes: Dict[str, AccessCode] = {}
        self.prefix = prefix
    
    def generate_code(self, length: int = 6) -> str:
        """Генерира случаен код"""
        chars = string.digits
        code = ''.join(random.choices(chars, k=length))
        return f"{self.prefix}{code}"
    
    def create_code(self, code_config: dict) -> str:
        """
        Създава нов код
        
        code_config = {
            "code": "G123456",  # или None за автоматично генериране
            "type": "one_time",  # one_time, daily, guest, permanent
            "zones": ["zone_1", "zone_2"],
            "expires_hours": 24,  # за guest тип
            "max_uses": 1,
            "created_by": "admin"
        }
        """
        code = code_config.get("code")
        if not code:
            code = self.generate_code()
        
        code_type = code_config.get("code_type", "one_time")
        
        if code in self.codes:
            logger.warning(f"Code {code} already exists, updating")
        
        expires_hours = code_config.get("expires_hours")
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
        elif code_type == "daily":
            expires_at = datetime.now().replace(hour=23, minute=59, second=59)
        
        max_uses = code_config.get("max_uses", -1)
        if code_type == "one_time":
            max_uses = 1
        elif code_type == "permanent":
            max_uses = -1
        
        access_code = AccessCode(
            code=code,
            code_type=code_type,
            zones=code_config.get("zones", []),
            uses_remaining=max_uses,
            expires_at=expires_at,
            created_by=code_config.get("created_by", "system"),
            active=True
        )
        
        self.codes[code] = access_code
        logger.info(f"Created code: {code} (type: {code_type})")
        
        return code
    
    def validate_code(self, code: str, zone_id: str) -> Tuple[bool, str, Optional[AccessCode]]:
        """
        Валидира кода
        
        Returns:
            (valid, message, code_data)
        """
        access_code = self.codes.get(code)
        
        if not access_code:
            return False, "Невалиден код", None
        
        valid, msg = access_code.is_valid()
        if not valid:
            return False, msg, access_code
        
        can_access, msg = access_code.can_access_zone(zone_id)
        if not can_access:
            return False, msg, access_code
        
        return True, "OK", access_code
    
    def use_code(self, code: str, user_id: str = "") -> Tuple[bool, str]:
        """
        Отбелязва кода като използван
        
        Returns:
            (success, message)
        """
        access_code = self.codes.get(code)
        
        if not access_code:
            return False, "Кодът не съществува"
        
        success = access_code.use()
        
        if success:
            logger.info(f"Code {code} used by {user_id}")
            return True, "Кодът е използван"
        
        return False, "Кодът не може да бъде използван"
    
    def revoke_code(self, code: str) -> bool:
        """Отнема кода"""
        access_code = self.codes.get(code)
        if not access_code:
            return False
        
        access_code.active = False
        logger.info(f"Code {code} revoked")
        return True
    
    def get_code(self, code: str) -> Optional[AccessCode]:
        """Връща кода"""
        return self.codes.get(code)
    
    def get_codes(self, filters: Optional[dict] = None) -> List[dict]:
        """
        Връща списък с кодове
        
        filters = {
            "code_type": "one_time",
            "active": True,
            "zone": "zone_1"
        }
        """
        result = []
        
        for code in self.codes.values():
            if filters:
                if "code_type" in filters and code.code_type != filters["code_type"]:
                    continue
                if "active" in filters and code.active != filters["active"]:
                    continue
                if "zone" in filters and filters["zone"] not in code.zones:
                    continue
            
            result.append(code.to_dict())
        
        return result
    
    def delete_code(self, code: str) -> bool:
        """Изтрива кода"""
        if code in self.codes:
            del self.codes[code]
            logger.info(f"Deleted code: {code}")
            return True
        return False
    
    def cleanup_expired(self):
        """Почиства изтеклите кодове"""
        now = datetime.now()
        expired = []
        
        for code, access_code in self.codes.items():
            if access_code.expires_at and now > access_code.expires_at:
                expired.append(code)
        
        for code in expired:
            del self.codes[code]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired codes")


code_manager = CodeManager()
