from .base import BaseRepository
from .user_repo import UserRepository, user_repo
from .company_repo import CompanyRepository, company_repo
from .time_repo import TimeTrackingRepository, time_repo
from .payroll_repo import PayrollRepository, payroll_repo
from .trz_repo import TRZRepository, trz_repo
from .production_repo import ProductionRepository, production_repo
from .warehouse_repo import WarehouseRepository, warehouse_repo
from .access_repo import AccessRepository, access_repo
from .settings_repo import SettingsRepository, settings_repo
from .vehicle_repo import VehicleRepository, vehicle_repo

__all__ = [
    "BaseRepository",
    "UserRepository",
    "CompanyRepository",
    "TimeTrackingRepository",
    "PayrollRepository",
    "TRZRepository",
    "ProductionRepository",
    "WarehouseRepository",
    "AccessRepository",
    "SettingsRepository",
    "VehicleRepository",
    # Singleton instances
    "user_repo",
    "company_repo",
    "time_repo",
    "payroll_repo",
    "trz_repo",
    "production_repo",
    "warehouse_repo",
    "access_repo",
    "settings_repo",
    "vehicle_repo",
]