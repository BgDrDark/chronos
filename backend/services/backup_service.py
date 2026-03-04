import json
from datetime import datetime, date
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import delete, text
from backend.database import models

# Helper to serialize dates and datetimes
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class BackupService:
    # Order matters for dependencies!
    # Parents first for Export/Import
    models_map = {
        "roles": models.Role,
        "companies": models.Company,
        "departments": models.Department,
        "positions": models.Position,
        "users": models.User,
        "global_settings": models.GlobalSetting,
        "shifts": models.Shift,
        "public_holidays": models.PublicHoliday,
        "leave_balances": models.LeaveBalance,
        "leave_requests": models.LeaveRequest,
        "timelogs": models.TimeLog,
        "schedules": models.WorkSchedule,
        "payrolls": models.Payroll,
        "payslips": models.Payslip,
        "bonuses": models.Bonus,
        "notifications": models.Notification,
        "user_sessions": models.UserSession,
        "auth_keys": models.AuthKey
    }
    
    # Sensitive fields to exclude from backup
    SENSITIVE_FIELDS = {
        "users": ["hashed_password", "qr_secret", "qr_token", "locked_until"],
        "auth_keys": ["secret"],
        "user_sessions": ["refresh_token_jti"],
        "api_keys": ["hashed_key"],
    }

    @staticmethod
    def _filter_sensitive_fields(table_name: str, record_dict: dict) -> dict:
        """Filter out sensitive fields from a record"""
        if table_name in BackupService.SENSITIVE_FIELDS:
            for field in BackupService.SENSITIVE_FIELDS[table_name]:
                if field in record_dict:
                    record_dict[field] = "[REDACTED]"
        return record_dict

    @staticmethod
    def create_backup(db: Session) -> Dict[str, Any]:
        backup_data = {
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "type": "full_backup"
            },
            "data": {}
        }

        for key, model in BackupService.models_map.items():
            records = db.query(model).all()
            # Convert SQLAlchemy objects to dicts
            # We filter out internal SQLAlchemy state
            serialized_records = []
            for r in records:
                r_dict = r.__dict__.copy()
                if '_sa_instance_state' in r_dict:
                    del r_dict['_sa_instance_state']
                # Filter sensitive fields
                r_dict = BackupService._filter_sensitive_fields(key, r_dict)
                serialized_records.append(r_dict)
            
            backup_data["data"][key] = serialized_records

        return backup_data

    @staticmethod
    def restore_backup(db: Session, backup_data: Dict[str, Any]):
        # 1. Verification
        if "data" not in backup_data:
            raise ValueError("Invalid backup format")

        try:
            # 2. Clean Database (Reverse Order to respect FKs)
            # We delete children first, then parents
            reversed_models = list(BackupService.models_map.items())
            reversed_models.reverse()

            for key, model in reversed_models:
                db.execute(delete(model))
            
            db.flush() # Ensure deletions happen before insertions

            # 3. Insert Data (Normal Order)
            for key, model in BackupService.models_map.items():
                if key in backup_data["data"]:
                    records = backup_data["data"][key]
                    for r_data in records:
                        # Filter sensitive fields before restore
                        r_data = BackupService._filter_sensitive_fields(key, r_data)
                        # Handle potential nulls or conversions if necessary
                        # SQLAlchemy handles ISO strings for DateTime usually, but let's be safe if needed
                        # Ideally, simple instantiation works if keys match columns
                        obj = model(**r_data)
                        db.add(obj)
                    db.flush() # Flush after each table to ensure IDs are available for next tables
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def archive_old_data(db: Session, cutoff_date: date) -> Dict[str, Any]:
        """
        Archives transactional data older than cutoff_date.
        Does NOT delete Structural data (Users, Companies, Shifts, etc.)
        """
        
        # Tables considered "Transactional" that can be pruned
        transactional_models = {
            "timelogs": (models.TimeLog, models.TimeLog.start_time),
            "schedules": (models.WorkSchedule, models.WorkSchedule.date),
            "payslips": (models.Payslip, models.Payslip.period_end),
            "leave_requests": (models.LeaveRequest, models.LeaveRequest.end_date),
            "notifications": (models.Notification, models.Notification.created_at),
            "user_sessions": (models.UserSession, models.UserSession.last_used_at),
            # Bonuses are tricky, usually attached to a date. Assuming 'date' column
            "bonuses": (models.Bonus, models.Bonus.date) 
        }

        archive_data = {
            "metadata": {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "type": "archive",
                "cutoff_date": cutoff_date.isoformat()
            },
            "data": {}
        }

        try:
            for key, (model, date_col) in transactional_models.items():
                # 1. Select Data
                records = db.query(model).filter(date_col < cutoff_date).all()
                
                serialized_records = []
                ids_to_delete = []
                for r in records:
                    r_dict = r.__dict__.copy()
                    if '_sa_instance_state' in r_dict:
                        del r_dict['_sa_instance_state']
                    # Filter sensitive fields
                    r_dict = BackupService._filter_sensitive_fields(key, r_dict)
                    serialized_records.append(r_dict)
                    ids_to_delete.append(r.id)
                
                archive_data["data"][key] = serialized_records

                # 2. Delete Data
                if ids_to_delete:
                    # Batch delete is more efficient
                    db.query(model).filter(model.id.in_(ids_to_delete)).delete(synchronize_session=False)
            
            db.commit()
            return archive_data

        except Exception as e:
            db.rollback()
            raise e
