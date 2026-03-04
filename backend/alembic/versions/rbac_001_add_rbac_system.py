"""Add RBAC system

Revision ID: rbac_001
Revises: 8f309b6300c1
Create Date: 2026-02-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'rbac_001'
down_revision = '8f309b6300c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('resource', 'action', name='uq_resource_action')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    op.create_index(op.f('ix_permissions_resource'), 'permissions', ['resource'], unique=False)
    op.create_index(op.f('ix_permissions_action'), 'permissions', ['action'], unique=False)
    
    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    op.create_index(op.f('ix_role_permissions_id'), 'role_permissions', ['id'], unique=False)
    
    # Create company_role_assignments table
    op.create_table('company_role_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'company_id', 'role_id')
    )
    op.create_index(op.f('ix_company_role_assignments_id'), 'company_role_assignments', ['id'], unique=False)
    
    # Create user_permission_cache table
    op.create_table('user_permission_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('permission_name', sa.String(length=100), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_permission_cache_id'), 'user_permission_cache', ['id'], unique=False)
    op.create_index('ix_user_permission_cache_lookup', 'user_permission_cache', ['user_id', 'company_id', 'permission_name'], unique=False)
    op.create_index('ix_user_permission_cache_expires', 'user_permission_cache', ['expires_at'], unique=False)
    
    # Create permission_audit_log table
    op.create_table('permission_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('permission', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permission_audit_log_id'), 'permission_audit_log', ['id'], unique=False)
    
    # Update existing roles table
    op.add_column('roles', sa.Column('is_system_role', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('roles', sa.Column('priority', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('roles', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('roles', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Populate permissions
    permissions_data = [
        # User Management
        ('users:read', 'users', 'read', 'View user information'),
        ('users:read_own', 'users', 'read_own', 'View own user information'),
        ('users:create', 'users', 'create', 'Create new users'),
        ('users:update', 'users', 'update', 'Update user information'),
        ('users:update_own', 'users', 'update_own', 'Update own profile'),
        ('users:delete', 'users', 'delete', 'Delete users'),
        ('users:manage_roles', 'users', 'manage_roles', 'Assign user roles'),
        
        # Time Management
        ('timelogs:read', 'timelogs', 'read', 'View time logs'),
        ('timelogs:read_own', 'timelogs', 'read_own', 'View own time logs'),
        ('timelogs:create', 'timelogs', 'create', 'Create time logs'),
        ('timelogs:create_own', 'timelogs', 'create_own', 'Clock in/out for self'),
        ('timelogs:update', 'timelogs', 'update', 'Modify time logs'),
        ('timelogs:delete', 'timelogs', 'delete', 'Delete time logs'),
        ('timelogs:admin_create', 'timelogs', 'admin_create', 'Create time logs for others'),
        
        # Schedule Management
        ('schedules:read', 'schedules', 'read', 'View schedules'),
        ('schedules:read_own', 'schedules', 'read_own', 'View own schedule'),
        ('schedules:create', 'schedules', 'create', 'Create schedules'),
        ('schedules:update', 'schedules', 'update', 'Update schedules'),
        ('schedules:delete', 'schedules', 'delete', 'Delete schedules'),
        ('schedules:approve_swaps', 'schedules', 'approve_swaps', 'Approve shift swaps'),
        
        # Payroll Management
        ('payroll:read', 'payroll', 'read', 'View payroll information'),
        ('payroll:read_own', 'payroll', 'read_own', 'View own payroll'),
        ('payroll:create', 'payroll', 'create', 'Create payroll records'),
        ('payroll:update', 'payroll', 'update', 'Update payroll records'),
        ('payroll:delete', 'payroll', 'delete', 'Delete payroll records'),
        ('payroll:export', 'payroll', 'export', 'Export payroll data'),
        
        # Leave Management
        ('leaves:read', 'leaves', 'read', 'View leave requests'),
        ('leaves:read_own', 'leaves', 'read_own', 'View own leave requests'),
        ('leaves:create', 'leaves', 'create', 'Create leave requests'),
        ('leaves:create_own', 'leaves', 'create_own', 'Create own leave requests'),
        ('leaves:approve', 'leaves', 'approve', 'Approve/reject leave requests'),
        ('leaves:update', 'leaves', 'update', 'Update leave requests'),
        ('leaves:delete', 'leaves', 'delete', 'Delete leave requests'),
        
        # Company Management
        ('companies:read', 'companies', 'read', 'View company information'),
        ('companies:create', 'companies', 'create', 'Create companies'),
        ('companies:update', 'companies', 'update', 'Update company information'),
        ('companies:delete', 'companies', 'delete', 'Delete companies'),
        ('companies:manage_users', 'companies', 'manage_users', 'Manage company users'),
        
        # System Administration
        ('system:backup', 'system', 'backup', 'Create system backups'),
        ('system:restore', 'system', 'restore', 'Restore from backup'),
        ('system:read_audit', 'system', 'read_audit', 'View audit logs'),
        ('system:manage_settings', 'system', 'manage_settings', 'Manage global settings'),
        ('system:manage_roles', 'system', 'manage_roles', 'Manage roles and permissions'),
        
        # Reports & Analytics
        ('reports:read', 'reports', 'read', 'View reports'),
        ('reports:create', 'reports', 'create', 'Generate reports'),
        ('reports:export', 'reports', 'export', 'Export reports'),
        ('analytics:read', 'analytics', 'read', 'View analytics'),
    ]
    
    op.bulk_insert(
        sa.table('permissions',
            sa.column('name', sa.String),
            sa.column('resource', sa.String),
            sa.column('action', sa.String),
            sa.column('description', sa.String),
            sa.column('created_at', sa.DateTime)
        ),
        [
            {'name': name, 'resource': resource, 'action': action, 'description': description, 'created_at': sa.func.now()}
            for name, resource, action, description in permissions_data
        ]
    )


def downgrade() -> None:
    # Drop RBAC tables
    op.drop_index(op.f('ix_permission_audit_log_id'), table_name='permission_audit_log')
    op.drop_table('permission_audit_log')
    
    op.drop_index('ix_user_permission_cache_expires', table_name='user_permission_cache')
    op.drop_index('ix_user_permission_cache_lookup', table_name='user_permission_cache')
    op.drop_index(op.f('ix_user_permission_cache_id'), table_name='user_permission_cache')
    op.drop_table('user_permission_cache')
    
    op.drop_index(op.f('ix_company_role_assignments_id'), table_name='company_role_assignments')
    op.drop_table('company_role_assignments')
    
    op.drop_index(op.f('ix_role_permissions_id'), table_name='role_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index(op.f('ix_permissions_action'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_resource'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_table('permissions')
    
    # Remove added columns from roles
    op.drop_column('roles', 'updated_at')
    op.drop_column('roles', 'created_at')
    op.drop_column('roles', 'priority')
    op.drop_column('roles', 'is_system_role')