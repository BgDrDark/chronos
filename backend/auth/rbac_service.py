from functools import wraps
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from backend.database.models import (
    User, Role, Permission, RolePermission, CompanyRoleAssignment,
    UserPermissionCache, PermissionAuditLog
)

logger = logging.getLogger(__name__)

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._permission_cache = {}
    
    async def get_user_permissions(
        self, 
        user_id: int, 
        company_id: Optional[int] = None
    ) -> Set[str]:
        """Get all permissions for a user, optionally scoped to company"""
        cache_key = f"user_{user_id}_company_{company_id}"
        
        # Check cache first (5 minutes)
        if cache_key in self._permission_cache:
            cached = self._permission_cache[cache_key]
            if cached['expires_at'] > datetime.now():
                return set(cached['permissions'])
        
        # Build permissions from roles
        permissions = set()
        
        # Get user roles with company assignments
        query = select(Role, CompanyRoleAssignment).join(
            CompanyRoleAssignment, Role.id == CompanyRoleAssignment.role_id
        ).where(
            CompanyRoleAssignment.user_id == user_id,
            CompanyRoleAssignment.is_active == True
        )
        
        if company_id:
            query = query.where(CompanyRoleAssignment.company_id == company_id)
        
        result = await self.db.execute(query)
        for role, assignment in result:
            # Get role permissions
            role_perms_query = select(Permission.name).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == Permission.id
            )
            role_perms_result = await self.db.execute(role_perms_query)
            permissions.update([row[0] for row in role_perms_result])
        
        # Cache for 5 minutes
        self._permission_cache[cache_key] = {
            'permissions': list(permissions),
            'expires_at': datetime.now() + timedelta(minutes=5)
        }
        
        return permissions
    
    async def check_permission(
        self, 
        user_id: int, 
        permission: str,
        company_id: Optional[int] = None,
        resource_id: Optional[int] = None
    ) -> bool:
        """Check if user has specific permission with optional resource ownership"""
        permissions = await self.get_user_permissions(user_id, company_id)
        
        # Direct permission check
        if permission in permissions:
            return True
        
        # Check ownership permissions
        if "_own" in permission:
            base_permission = permission.replace("_own", "")
            if base_permission in permissions:
                # Verify resource ownership
                return await self._verify_ownership(user_id, resource_id, permission.split(":")[0])
        
        return False
    
    async def _verify_ownership(self, user_id: int, resource_id: Optional[int], resource_type: str) -> bool:
        """Verify if user owns resource"""
        if not resource_id:
            return False
        
        if resource_type == "users":
            return user_id == resource_id
        elif resource_type == "timelogs":
            from backend.database.models import TimeLog
            result = await self.db.execute(
                select(TimeLog.user_id).where(TimeLog.id == resource_id)
            )
            resource_user_id = result.scalar_one_or_none()
            return user_id == resource_user_id
        elif resource_type == "payroll":
            from backend.database.models import Payroll
            result = await self.db.execute(
                select(Payroll.user_id).where(Payroll.id == resource_id)
            )
            resource_user_id = result.scalar_one_or_none()
            return user_id == resource_user_id
        
        return False
    
    async def clear_cache(self, user_id: Optional[int] = None):
        """Clear permission cache for a user or all users"""
        if user_id:
            keys_to_remove = [k for k in self._permission_cache.keys() if f"user_{user_id}" in k]
            for key in keys_to_remove:
                del self._permission_cache[key]
        else:
            self._permission_cache = {}
    
    async def verify_company_access(
        self,
        user_id: int,
        company_id: int,
        permission: str
    ) -> bool:
        """Verify user has permission for specific company"""
        assignment_stmt = select(CompanyRoleAssignment).where(
            CompanyRoleAssignment.user_id == user_id,
            CompanyRoleAssignment.company_id == company_id,
            CompanyRoleAssignment.is_active == True
        )
        result = await self.db.execute(assignment_stmt)
        assignment = result.scalars().first()
        
        if not assignment:
            return False
        
        return await self.check_permission(user_id, permission, company_id=company_id)
    
    async def log_permission_decision(
        self,
        user_id: int,
        permission: str,
        decision: bool,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        context: Optional[dict] = None
    ):
        """Log every permission decision for audit trail"""
        try:
            audit_entry = PermissionAuditLog(
                user_id=user_id,
                permission=permission,
                decision="GRANTED" if decision else "DENIED",
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=context.get('ip_address') if context else None,
                user_agent=context.get('user_agent') if context else None,
            )
            
            self.db.add(audit_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log permission decision: {e}")
    
    async def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's roles with company assignments"""
        query = select(Role, CompanyRoleAssignment).join(
            CompanyRoleAssignment, Role.id == CompanyRoleAssignment.role_id
        ).where(
            CompanyRoleAssignment.user_id == user_id,
            CompanyRoleAssignment.is_active == True
        )
        
        result = await self.db.execute(query)
        roles = []
        for role, assignment in result:
            roles.append({
                "id": role.id,
                "name": role.name,
                "company_id": assignment.company_id,
                "is_active": assignment.is_active,
                "priority": role.priority
            })
        
        return roles

    async def assign_role_to_user(
        self, 
        user_id: int, 
        company_id: int, 
        role_id: int,
        assigned_by: int
    ) -> bool:
        """Assign role to user in specific company"""
        # Check if assignment already exists
        result = await self.db.execute(
            select(CompanyRoleAssignment).where(
                and_(
                    CompanyRoleAssignment.user_id == user_id,
                    CompanyRoleAssignment.company_id == company_id,
                    CompanyRoleAssignment.role_id == role_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Reactivate if exists
            existing.is_active = True
            existing.assigned_by = assigned_by
            existing.assigned_at = datetime.now()
        else:
            # Create new assignment
            assignment = CompanyRoleAssignment(
                user_id=user_id,
                company_id=company_id,
                role_id=role_id,
                assigned_by=assigned_by
            )
            self.db.add(assignment)
        
        await self.db.commit()
        
        # Clear cache for this user
        self._clear_user_cache(user_id)
        
        return True
    
    def _clear_user_cache(self, user_id: int):
        """Clear permission cache for specific user"""
        keys_to_remove = [k for k in self._permission_cache.keys() if k.startswith(f"user_{user_id}_")]
        for key in keys_to_remove:
            del self._permission_cache[key]

    async def verify_company_access(self, current_user: User, target_company_id: Optional[int]):
        """
        Verify that the user has access to the target company.
        Super admins can access all companies.
        Others can only access their own company.
        """
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        if current_user.role.name == "super_admin":
            return # Full access
            
        if target_company_id and current_user.company_id != target_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нямате достъп до данни на друга компания"
            )
        return current_user.company_id


def require_permission(permission: str, company_scoped: bool = False):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs or request
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get database session
            db = kwargs.get('db')
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session required"
                )
            
            # Get company_id if company_scoped
            company_id = None
            if company_scoped:
                company_id = kwargs.get('company_id') or getattr(current_user, 'company_id', None)
            
            # Check permission
            permission_service = PermissionService(db)
            has_permission = await permission_service.check_permission(
                current_user.id, permission, company_id
            )
            
            if not has_permission:
                # Log permission denial
                await permission_service.log_permission_decision(
                    current_user.id, permission, False, company_id=company_id
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )
            
            # Log permission grant
            await permission_service.log_permission_decision(
                current_user.id, permission, True, company_id=company_id
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Default permissions setup
DEFAULT_PERMISSIONS = {
    # User Management
    "users:read": {"resource": "users", "action": "read", "description": "View user information"},
    "users:read_own": {"resource": "users", "action": "read_own", "description": "View own user information"},
    "users:create": {"resource": "users", "action": "create", "description": "Create new users"},
    "users:update": {"resource": "users", "action": "update", "description": "Update user information"},
    "users:update_own": {"resource": "users", "action": "update_own", "description": "Update own profile"},
    "users:delete": {"resource": "users", "action": "delete", "description": "Delete users"},
    "users:manage_roles": {"resource": "users", "action": "manage_roles", "description": "Assign user roles"},
    
    # Time Management
    "timelogs:read": {"resource": "timelogs", "action": "read", "description": "View time logs"},
    "timelogs:read_own": {"resource": "timelogs", "action": "read_own", "description": "View own time logs"},
    "timelogs:create": {"resource": "timelogs", "action": "create", "description": "Create time logs"},
    "timelogs:create_own": {"resource": "timelogs", "action": "create_own", "description": "Clock in/out for self"},
    "timelogs:update": {"resource": "timelogs", "action": "update", "description": "Modify time logs"},
    "timelogs:delete": {"resource": "timelogs", "action": "delete", "description": "Delete time logs"},
    "timelogs:admin_create": {"resource": "timelogs", "action": "admin_create", "description": "Create time logs for others"},
    
    # Schedule Management
    "schedules:read": {"resource": "schedules", "action": "read", "description": "View schedules"},
    "schedules:read_own": {"resource": "schedules", "action": "read_own", "description": "View own schedule"},
    "schedules:create": {"resource": "schedules", "action": "create", "description": "Create schedules"},
    "schedules:update": {"resource": "schedules", "action": "update", "description": "Update schedules"},
    "schedules:delete": {"resource": "schedules", "action": "delete", "description": "Delete schedules"},
    "schedules:approve_swaps": {"resource": "schedules", "action": "approve_swaps", "description": "Approve shift swaps"},
    
    # Payroll Management
    "payroll:read": {"resource": "payroll", "action": "read", "description": "View payroll information"},
    "payroll:read_own": {"resource": "payroll", "action": "read_own", "description": "View own payroll"},
    "payroll:create": {"resource": "payroll", "action": "create", "description": "Create payroll records"},
    "payroll:update": {"resource": "payroll", "action": "update", "description": "Update payroll records"},
    "payroll:delete": {"resource": "payroll", "action": "delete", "description": "Delete payroll records"},
    "payroll:export": {"resource": "payroll", "action": "export", "description": "Export payroll data"},
    
    # Leave Management
    "leaves:read": {"resource": "leaves", "action": "read", "description": "View leave requests"},
    "leaves:read_own": {"resource": "leaves", "action": "read_own", "description": "View own leave requests"},
    "leaves:create": {"resource": "leaves", "action": "create", "description": "Create leave requests"},
    "leaves:create_own": {"resource": "leaves", "action": "create_own", "description": "Create own leave requests"},
    "leaves:approve": {"resource": "leaves", "action": "approve", "description": "Approve/reject leave requests"},
    "leaves:update": {"resource": "leaves", "action": "update", "description": "Update leave requests"},
    "leaves:delete": {"resource": "leaves", "action": "delete", "description": "Delete leave requests"},
    
    # Company Management
    "companies:read": {"resource": "companies", "action": "read", "description": "View company information"},
    "companies:create": {"resource": "companies", "action": "create", "description": "Create companies"},
    "companies:update": {"resource": "companies", "action": "update", "description": "Update company information"},
    "companies:delete": {"resource": "companies", "action": "delete", "description": "Delete companies"},
    "companies:manage_users": {"resource": "companies", "action": "manage_users", "description": "Manage company users"},
    
    # System Administration
    "system:backup": {"resource": "system", "action": "backup", "description": "Create system backups"},
    "system:restore": {"resource": "system", "action": "restore", "description": "Restore from backup"},
    "system:read_audit": {"resource": "system", "action": "read_audit", "description": "View audit logs"},
    "system:manage_settings": {"resource": "system", "action": "manage_settings", "description": "Manage global settings"},
    "system:manage_roles": {"resource": "system", "action": "manage_roles", "description": "Manage roles and permissions"},
    "system:manage_modules": {"resource": "system", "action": "manage_modules", "description": "Enable or disable system modules"},
    
    # Reports & Analytics
    "reports:read": {"resource": "reports", "action": "read", "description": "View reports"},
    "reports:create": {"resource": "reports", "action": "create", "description": "Generate reports"},
    "reports:export": {"resource": "reports", "action": "export", "description": "Export reports"},
    "analytics:read": {"resource": "analytics", "action": "read", "description": "View analytics"},
    
    # Logistics
    "logistics:suppliers:read": {"resource": "logistics_suppliers", "action": "read", "description": "View suppliers"},
    "logistics:suppliers:create": {"resource": "logistics_suppliers", "action": "create", "description": "Create suppliers"},
    "logistics:suppliers:update": {"resource": "logistics_suppliers", "action": "update", "description": "Update suppliers"},
    "logistics:suppliers:delete": {"resource": "logistics_suppliers", "action": "delete", "description": "Delete suppliers"},
    "logistics:templates:read": {"resource": "logistics_templates", "action": "read", "description": "View request templates"},
    "logistics:templates:create": {"resource": "logistics_templates", "action": "create", "description": "Create request templates"},
    "logistics:templates:update": {"resource": "logistics_templates", "action": "update", "description": "Update request templates"},
    "logistics:templates:delete": {"resource": "logistics_templates", "action": "delete", "description": "Delete request templates"},
    "logistics:requests:read": {"resource": "logistics_requests", "action": "read", "description": "View purchase requests"},
    "logistics:requests:create": {"resource": "logistics_requests", "action": "create", "description": "Create purchase requests"},
    "logistics:requests:update": {"resource": "logistics_requests", "action": "update", "description": "Update purchase requests"},
    "logistics:requests:approve": {"resource": "logistics_requests", "action": "approve", "description": "Approve/reject purchase requests"},
    "logistics:requests:delete": {"resource": "logistics_requests", "action": "delete", "description": "Delete purchase requests"},
    "logistics:orders:read": {"resource": "logistics_orders", "action": "read", "description": "View purchase orders"},
    "logistics:orders:create": {"resource": "logistics_orders", "action": "create", "description": "Create purchase orders"},
    "logistics:orders:update": {"resource": "logistics_orders", "action": "update", "description": "Update purchase orders"},
    "logistics:orders:delete": {"resource": "logistics_orders", "action": "delete", "description": "Delete purchase orders"},
    "logistics:deliveries:read": {"resource": "logistics_deliveries", "action": "read", "description": "View deliveries"},
    "logistics:deliveries:create": {"resource": "logistics_deliveries", "action": "create", "description": "Create deliveries"},
    "logistics:deliveries:update": {"resource": "logistics_deliveries", "action": "update", "description": "Update deliveries"},
    "logistics:deliveries:delete": {"resource": "logistics_deliveries", "action": "delete", "description": "Delete deliveries"},
    
    # Fleet Management
    "fleet:vehicles:read": {"resource": "fleet_vehicles", "action": "read", "description": "View vehicles"},
    "fleet:vehicles:create": {"resource": "fleet_vehicles", "action": "create", "description": "Create vehicles"},
    "fleet:vehicles:update": {"resource": "fleet_vehicles", "action": "update", "description": "Update vehicles"},
    "fleet:vehicles:delete": {"resource": "fleet_vehicles", "action": "delete", "description": "Delete vehicles"},
    "fleet:vehicles:status": {"resource": "fleet_vehicles", "action": "status", "description": "Change vehicle status"},
    "fleet:documents:read": {"resource": "fleet_documents", "action": "read", "description": "View vehicle documents"},
    "fleet:documents:create": {"resource": "fleet_documents", "action": "create", "description": "Create vehicle documents"},
    "fleet:documents:update": {"resource": "fleet_documents", "action": "update", "description": "Update vehicle documents"},
    "fleet:documents:delete": {"resource": "fleet_documents", "action": "delete", "description": "Delete vehicle documents"},
    "fleet:fuel_cards:read": {"resource": "fleet_fuel_cards", "action": "read", "description": "View fuel cards"},
    "fleet:fuel_cards:create": {"resource": "fleet_fuel_cards", "action": "create", "description": "Create fuel cards"},
    "fleet:fuel_cards:update": {"resource": "fleet_fuel_cards", "action": "update", "description": "Update fuel cards"},
    "fleet:fuel_cards:delete": {"resource": "fleet_fuel_cards", "action": "delete", "description": "Delete fuel cards"},
    "fleet:vignettes:read": {"resource": "fleet_vignettes", "action": "read", "description": "View vignettes"},
    "fleet:vignettes:create": {"resource": "fleet_vignettes", "action": "create", "description": "Create vignettes"},
    "fleet:vignettes:update": {"resource": "fleet_vignettes", "action": "update", "description": "Update vignettes"},
    "fleet:vignettes:delete": {"resource": "fleet_vignettes", "action": "delete", "description": "Delete vignettes"},
    "fleet:tolls:read": {"resource": "fleet_tolls", "action": "read", "description": "View tolls"},
    "fleet:tolls:create": {"resource": "fleet_tolls", "action": "create", "description": "Create tolls"},
    "fleet:tolls:update": {"resource": "fleet_tolls", "action": "update", "description": "Update tolls"},
    "fleet:tolls:delete": {"resource": "fleet_tolls", "action": "delete", "description": "Delete tolls"},
    "fleet:mileage:read": {"resource": "fleet_mileage", "action": "read", "description": "View mileage records"},
    "fleet:mileage:create": {"resource": "fleet_mileage", "action": "create", "description": "Create mileage records"},
    "fleet:mileage:update": {"resource": "fleet_mileage", "action": "update", "description": "Update mileage records"},
    "fleet:mileage:delete": {"resource": "fleet_mileage", "action": "delete", "description": "Delete mileage records"},
    "fleet:fuel:read": {"resource": "fleet_fuel", "action": "read", "description": "View fuel records"},
    "fleet:fuel:create": {"resource": "fleet_fuel", "action": "create", "description": "Create fuel records"},
    "fleet:fuel:update": {"resource": "fleet_fuel", "action": "update", "description": "Update fuel records"},
    "fleet:fuel:delete": {"resource": "fleet_fuel", "action": "delete", "description": "Delete fuel records"},
    "fleet:repairs:read": {"resource": "fleet_repairs", "action": "read", "description": "View repairs"},
    "fleet:repairs:create": {"resource": "fleet_repairs", "action": "create", "description": "Create repairs"},
    "fleet:repairs:update": {"resource": "fleet_repairs", "action": "update", "description": "Update repairs"},
    "fleet:repairs:delete": {"resource": "fleet_repairs", "action": "delete", "description": "Delete repairs"},
    "fleet:schedules:read": {"resource": "fleet_schedules", "action": "read", "description": "View maintenance schedules"},
    "fleet:schedules:create": {"resource": "fleet_schedules", "action": "create", "description": "Create maintenance schedules"},
    "fleet:schedules:update": {"resource": "fleet_schedules", "action": "update", "description": "Update maintenance schedules"},
    "fleet:schedules:delete": {"resource": "fleet_schedules", "action": "delete", "description": "Delete maintenance schedules"},
    "fleet:insurances:read": {"resource": "fleet_insurances", "action": "read", "description": "View insurances"},
    "fleet:insurances:create": {"resource": "fleet_insurances", "action": "create", "description": "Create insurances"},
    "fleet:insurances:update": {"resource": "fleet_insurances", "action": "update", "description": "Update insurances"},
    "fleet:insurances:delete": {"resource": "fleet_insurances", "action": "delete", "description": "Delete insurances"},
    "fleet:inspections:read": {"resource": "fleet_inspections", "action": "read", "description": "View inspections (GTP)"},
    "fleet:inspections:create": {"resource": "fleet_inspections", "action": "create", "description": "Create inspections (GTP)"},
    "fleet:inspections:update": {"resource": "fleet_inspections", "action": "update", "description": "Update inspections (GTP)"},
    "fleet:inspections:delete": {"resource": "fleet_inspections", "action": "delete", "description": "Delete inspections (GTP)"},
    "fleet:pretrip:read": {"resource": "fleet_pretrip", "action": "read", "description": "View pre-trip inspections"},
    "fleet:pretrip:create": {"resource": "fleet_pretrip", "action": "create", "description": "Create pre-trip inspections"},
    "fleet:pretrip:update": {"resource": "fleet_pretrip", "action": "update", "description": "Update pre-trip inspections"},
    "fleet:drivers:read": {"resource": "fleet_drivers", "action": "read", "description": "View drivers"},
    "fleet:drivers:create": {"resource": "fleet_drivers", "action": "create", "description": "Assign drivers"},
    "fleet:drivers:update": {"resource": "fleet_drivers", "action": "update", "description": "Update drivers"},
    "fleet:drivers:delete": {"resource": "fleet_drivers", "action": "delete", "description": "Unassign drivers"},
    "fleet:trips:read": {"resource": "fleet_trips", "action": "read", "description": "View trips"},
    "fleet:trips:create": {"resource": "fleet_trips", "action": "create", "description": "Create trips"},
    "fleet:trips:update": {"resource": "fleet_trips", "action": "update", "description": "Update trips"},
    "fleet:trips:delete": {"resource": "fleet_trips", "action": "delete", "description": "Delete trips"},
    "fleet:expenses:read": {"resource": "fleet_expenses", "action": "read", "description": "View expenses"},
    "fleet:expenses:create": {"resource": "fleet_expenses", "action": "create", "description": "Create expenses"},
    "fleet:expenses:update": {"resource": "fleet_expenses", "action": "update", "description": "Update expenses"},
    "fleet:expenses:delete": {"resource": "fleet_expenses", "action": "delete", "description": "Delete expenses"},
    "fleet:costcenters:read": {"resource": "fleet_costcenters", "action": "read", "description": "View cost centers"},
    "fleet:costcenters:create": {"resource": "fleet_costcenters", "action": "create", "description": "Create cost centers"},
    "fleet:costcenters:update": {"resource": "fleet_costcenters", "action": "update", "description": "Update cost centers"},
    "fleet:costcenters:delete": {"resource": "fleet_costcenters", "action": "delete", "description": "Delete cost centers"},
    "fleet:reports:read": {"resource": "fleet_reports", "action": "read", "description": "View fleet reports"},
    "fleet:reports:export": {"resource": "fleet_reports", "action": "export", "description": "Export fleet reports"},
}


DEFAULT_ROLES = {
    "super_admin": {
        "description": "Super Administrator with full system access",
        "priority": 100,
        "is_system_role": True,
        "permissions": list(DEFAULT_PERMISSIONS.keys())
    },
    "admin": {
        "description": "Администратор с пълен достъп до системата",
        "priority": 90,
        "permissions": list(DEFAULT_PERMISSIONS.keys())
    },
    "global_accountant": {
        "description": "Главен счетоводител с достъп до всички фирми",
        "priority": 75,
        "permissions": [
            "users:read", "users:create", "users:update",
            "timelogs:read", "timelogs:admin_create",
            "schedules:read",
            "payroll:read", "payroll:create", "payroll:update", "payroll:export",
            "leaves:read",
            "companies:read",
            "reports:read", "reports:create", "reports:export", "analytics:read",
        ]
    },
    "accountant": {
        "description": "Счетоводител с достъп до конкретна фирма",
        "priority": 70,
        "permissions": [
            "users:read", "users:create", "users:update",
            "timelogs:read", "timelogs:admin_create",
            "schedules:read",
            "payroll:read", "payroll:create", "payroll:update", "payroll:export",
            "leaves:read",
            "companies:read",
            "reports:read", "reports:create", "reports:export", "analytics:read",
        ]
    },
    "logistics_manager": {
        "description": "Управление на логистиката",
        "priority": 65,
        "permissions": [
            "logistics:suppliers:read", "logistics:suppliers:create", "logistics:suppliers:update", "logistics:suppliers:delete",
            "logistics:templates:read", "logistics:templates:create", "logistics:templates:update", "logistics:templates:delete",
            "logistics:requests:read", "logistics:requests:create", "logistics:requests:update", "logistics:requests:approve", "logistics:requests:delete",
            "logistics:orders:read", "logistics:orders:create", "logistics:orders:update", "logistics:orders:delete",
            "logistics:deliveries:read", "logistics:deliveries:create", "logistics:deliveries:update", "logistics:deliveries:delete",
            "reports:read", "reports:create", "reports:export",
        ]
    },
    "fleet_manager": {
        "description": "Управление на автопарк",
        "priority": 65,
        "permissions": [
            "fleet:vehicles:read", "fleet:vehicles:create", "fleet:vehicles:update", "fleet:vehicles:delete", "fleet:vehicles:status",
            "fleet:documents:read", "fleet:documents:create", "fleet:documents:update", "fleet:documents:delete",
            "fleet:fuel_cards:read", "fleet:fuel_cards:create", "fleet:fuel_cards:update", "fleet:fuel_cards:delete",
            "fleet:vignettes:read", "fleet:vignettes:create", "fleet:vignettes:update", "fleet:vignettes:delete",
            "fleet:tolls:read", "fleet:tolls:create", "fleet:tolls:update", "fleet:tolls:delete",
            "fleet:mileage:read", "fleet:mileage:create", "fleet:mileage:update", "fleet:mileage:delete",
            "fleet:fuel:read", "fleet:fuel:create", "fleet:fuel:update", "fleet:fuel:delete",
            "fleet:repairs:read", "fleet:repairs:create", "fleet:repairs:update", "fleet:repairs:delete",
            "fleet:schedules:read", "fleet:schedules:create", "fleet:schedules:update", "fleet:schedules:delete",
            "fleet:insurances:read", "fleet:insurances:create", "fleet:insurances:update", "fleet:insurances:delete",
            "fleet:inspections:read", "fleet:inspections:create", "fleet:inspections:update", "fleet:inspections:delete",
            "fleet:drivers:read", "fleet:drivers:create", "fleet:drivers:update", "fleet:drivers:delete",
            "fleet:trips:read", "fleet:trips:create", "fleet:trips:update", "fleet:trips:delete",
            "fleet:expenses:read", "fleet:expenses:create", "fleet:expenses:update", "fleet:expenses:delete",
            "fleet:costcenters:read", "fleet:costcenters:create", "fleet:costcenters:update", "fleet:costcenters:delete",
            "fleet:reports:read", "fleet:reports:export",
        ]
    },
    "hr_manager": {
        "description": "HR Manager with people management permissions",
        "priority": 60,
        "permissions": [
            "users:read", "users:create", "users:update", "users:manage_roles",
            "timelogs:read", "timelogs:admin_create",
            "schedules:read", "schedules:create", "schedules:update", "schedules:approve_swaps",
            "payroll:read", "payroll:create", "payroll:update",
            "leaves:read", "leaves:approve", "leaves:update",
            "reports:read", "reports:create", "analytics:read",
        ]
    },
    "manager": {
        "description": "Manager with team oversight permissions",
        "priority": 50,
        "permissions": [
            "users:read",
            "timelogs:read", "timelogs:admin_create",
            "schedules:read", "schedules:create", "schedules:update", "schedules:approve_swaps",
            "payroll:read",
            "leaves:read", "leaves:approve",
            "reports:read", "analytics:read",
        ]
    },
    "driver": {
        "description": "Шофьор с достъп до своите данни",
        "priority": 25,
        "permissions": [
            "fleet:vehicles:read_own",
            "fleet:trips:read_own", "fleet:trips:create_own", "fleet:trips:update_own",
            "fleet:pretrip:create",
            "fleet:fuel:read_own",
        ]
    },
    "employee": {
        "description": "Standard Employee with self-service permissions",
        "priority": 20,
        "permissions": [
            "users:read_own", "users:update_own",
            "timelogs:read_own", "timelogs:create_own",
            "schedules:read_own",
            "payroll:read_own",
            "leaves:read_own", "leaves:create_own",
        ]
    },
    "viewer": {
        "description": "Read-only access for auditors and contractors",
        "priority": 10,
        "permissions": [
            "timelogs:read_own",
            "schedules:read_own",
            "payroll:read_own",
            "leaves:read_own",
        ]
    }
}