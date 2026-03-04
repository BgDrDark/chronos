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
        
        if resource_type == "users":
            return user_id == resource_id
        elif resource_type == "timelogs":
            from backend.database.models import TimeLog
            result = await self.db.execute(
                select(TimeLog.user_id).where(TimeLog.id == resource_id)
            )
            return user_id == result.scalar_one_or_none()
        elif resource_type == "payroll":
            from backend.database.models import Payroll
            result = await self.db.execute(
                select(Payroll.user_id).where(Payroll.id == resource_id)
            )
            return user_id == result.scalar_one_or_none()
        
        return False
    
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
}


DEFAULT_ROLES = {
    "super_admin": {
        "description": "Super Administrator with full system access",
        "priority": 100,
        "is_system_role": True,
        "permissions": list(DEFAULT_PERMISSIONS.keys())
    },
    "company_admin": {
        "description": "Company Administrator with company-scoped access",
        "priority": 80,
        "permissions": [
            "users:read", "users:create", "users:update", "users:delete", "users:manage_roles",
            "timelogs:read", "timelogs:admin_create", "timelogs:update", "timelogs:delete",
            "schedules:read", "schedules:create", "schedules:update", "schedules:delete", "schedules:approve_swaps",
            "payroll:read", "payroll:create", "payroll:update", "payroll:export",
            "leaves:read", "leaves:approve", "leaves:update", "leaves:delete",
            "companies:read", "companies:update", "companies:manage_users",
            "reports:read", "reports:create", "reports:export", "analytics:read",
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
            "users:read",  # Only team members
            "timelogs:read", "timelogs:admin_create",  # For team members
            "schedules:read", "schedules:create", "schedules:update", "schedules:approve_swaps",
            "payroll:read",
            "leaves:read", "leaves:approve",
            "reports:read", "analytics:read",
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