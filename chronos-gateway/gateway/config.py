import os
import yaml
from pathlib import Path
from typing import Optional, Any

BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / 'config.yaml'


class Config:
    def __init__(self, config_path: Optional[str] = None):
        self._config = {}
        self._config_path = config_path or str(CONFIG_FILE)
        self._load()
    
    def _load(self):
        if os.path.exists(self._config_path):
            with open(self._config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
            if self._deep_merge_defaults():
                self._save()
        else:
            self._config = self._get_defaults()
            self._save()
        self._ensure_cluster_secret()
        self._load_sqlite_overrides()
    
    def _ensure_cluster_secret(self):
        """Кластърният shared_secret винаги идва от backend-а — никога не го генерираме локално.
        Ако липсва, оставяме празен (ще се запълни след регистрация).
        Ако все още е 'chronos_cluster_secret', изчистваме го.
        """
        logger = __import__('logging').getLogger(__name__)
        current = self._config.get('cluster', {}).get('shared_secret', '')
        if not current:
            return
        if current == 'chronos_cluster_secret':
            self._config.setdefault('cluster', {})['shared_secret'] = ''
            self._save()
            logger.info("Cleared deprecated default cluster secret (will be fetched from backend on registration)")
    
    def _load_sqlite_overrides(self):
        """Зарежда настройки от SQLite gateway_settings които презаписват config.yaml.
        Позволява runtime промени (напр. backend URL) да се запазят през рестарти."""
        try:
            from gateway.database.sqlite_manager import config_db
            url = config_db.get_setting("backend_url")
            if url:
                self._config.setdefault('backend', {})['url'] = url
            fallback = config_db.get_setting("fallback_url")
            if fallback:
                self._config.setdefault('backend', {})['fallback_url'] = fallback
        except Exception:
            pass

    def _deep_merge_defaults(self) -> bool:
        """Добавя липсващи ключове от defaults в self._config.
        Връща True ако е имало промяна (за да се презапише файла)."""
        changed = False
        defaults = self._get_defaults()

        def _merge(current, default, path=""):
            nonlocal changed
            for key, val in default.items():
                if key not in current:
                    current[key] = val
                    changed = True
                elif isinstance(val, dict) and isinstance(current[key], dict):
                    _merge(current[key], val, f"{path}.{key}")
                # ако е списък — не сливаме, остава файловата стойност

        _merge(self._config, defaults)
        return changed
    
    def _save(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def _get_defaults(self):
        return {
            'gateway': {
                'id': 'auto',
                'alias': '',
                'hardware_uuid': '',
                'system_mode': 'normal',
            },
            'cluster': {
                'enabled': False,
                'priority': 'auto', # auto or 1, 2, 3...
                'shared_secret': '',
                'discovery_port': 8891,
                'heartbeat_interval': 5,
                'master_timeout': 60,
            },
            'network': {
                'ip': '0.0.0.0',
                'terminal_port': 1424,
                'web_port': 8889,
            },
            'backend': {
                'url': 'https://dev.oblak24.org',
                'fallback_url': 'https://dev.oblak24.org',
                'api_key': '',
                'verify_ssl': True,
            },
            'mtls': {
                'enabled': False,
                'cert_file': '',
                'key_file': '',
                'ca_file': '',
            },
            'activity': {
                'heartbeat_interval': 30,
                'timeout': 120,
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/gateway.log',
                'max_size': '10MB',
                'backup_count': 5,
            },
            'printers': [],
            'system': {
                'timezone': 'Europe/Sofia',
            },
            'scim': {
                'enabled': False,
                'api_token': '',
            },
            'access_control': {
                'enabled': False,
                'auto_reset_time': '23:00',
                'auto_reset_enabled': True,
                'anti_passback': {
                    'enabled': False,
                    'default_type': 'soft',
                    'timeout_minutes': 5,
                },
                'rate_limit': {
                    'enabled': True,
                    'max_attempts': 5,
                    'window_minutes': 1,
                    'lockout_minutes': 5,
                },
                'one_time_codes': {
                    'enabled': True,
                    'prefix': 'G',
                },
                'zones': [],
                'doors': [],
                'hardware': {
                    'devices': []
                }
            },
        }
    
    def get(self, key: str, default=None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
    
    @property
    def gateway_id(self) -> str:
        return str(self.get('gateway.id', 'auto'))
    
    @property
    def alias(self) -> str:
        return self.get('gateway.alias', '')
    
    @property
    def hardware_uuid(self) -> str:
        return self.get('gateway.hardware_uuid', '')
    
    @hardware_uuid.setter
    def hardware_uuid(self, value: str):
        self.set('gateway.hardware_uuid', value)
    
    @property
    def terminal_port(self) -> int:
        return self.get('network.terminal_port', 1424)
    
    @property
    def web_port(self) -> int:
        return self.get('network.web_port', 8889)
    
    @property
    def backend_url(self) -> str:
        return self.get('backend.url', 'https://dev.oblak24.org')
    
    @property
    def fallback_url(self) -> str:
        return self.get('backend.fallback_url', '')
    
    @property
    def api_key(self) -> str:
        return self.get('backend.api_key', '')
    
    @property
    def heartbeat_interval(self) -> int:
        return self.get('activity.heartbeat_interval', 30)
    
    @property
    def heartbeat_timeout(self) -> int:
        return self.get('activity.timeout', 120)
    
    @property
    def timezone(self) -> str:
        return self.get('system.timezone', 'Europe/Sofia')
    
    @property
    def access_control_enabled(self) -> bool:
        return self.get('access_control.enabled', False)
    
    @property
    def access_control_config(self) -> dict:
        return self.get('access_control', {})

    @property
    def scim_enabled(self) -> bool:
        return self.get('scim.enabled', False)

    @property
    def scim_api_token(self) -> str:
        return self.get('scim.api_token', '')


config = Config()
