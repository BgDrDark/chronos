"""Maintenance rules for vehicles."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from backend.database.database import Base


class MaintenanceRule(Base):
    """Rules for automatic maintenance scheduling"""

    __tablename__ = "vehicle_maintenance_rules"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)  # 'mileage', 'time', 'both'
    interval_km = Column(Integer, nullable=True)
    interval_months = Column(Integer, nullable=True)
    description = Column(String(255), nullable=False)
    last_completed_date = Column(Date, nullable=True)
    last_completed_km = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
