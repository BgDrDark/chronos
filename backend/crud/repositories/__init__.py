from .access_repo import AccessRepository, access_repo
from .base import BaseRepository
from .company_repo import CompanyRepository, company_repo
from .notification_repo import NotificationRepository, notification_repo
from .payroll_repo import PayrollRepository, payroll_repo
from .production_repo import ProductionRepository, production_repo
from .push_subscription_repo import PushSubscriptionRepository, push_subscription_repo
from .settings_repo import SettingsRepository, settings_repo
from .time_repo import TimeTrackingRepository, time_repo
from .trz_repo import TRZRepository, trz_repo
from .user_repo import UserRepository, user_repo
from .vehicle_repo import VehicleRepository, vehicle_repo
from .warehouse_repo import WarehouseRepository, warehouse_repo

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
    "NotificationRepository",
    "PushSubscriptionRepository",
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
    "notification_repo",
    "push_subscription_repo",
]
