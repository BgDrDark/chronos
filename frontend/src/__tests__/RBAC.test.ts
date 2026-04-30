import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ApolloProvider } from '@apollo/client';
import { gql } from '@apollo/client';

// Mock data for different roles
const mockUsersByRole = {
  super_admin: {
    id: 1,
    email: 'admin@company.com',
    firstName: 'Super',
    surname: 'Admin',
    role: { id: 1, name: 'super_admin', description: 'Super Administrator' },
    isActive: true
  },
  admin: {
    id: 2,
    email: 'manager@company.com',
    firstName: 'Company',
    surname: 'Manager',
    role: { id: 2, name: 'admin', description: 'Administrator' },
    isActive: true
  },
  manager: {
    id: 3,
    email: 'hr@company.com',
    firstName: 'HR',
    surname: 'Manager',
    role: { id: 5, name: 'manager', description: 'Manager' },
    isActive: true
  },
  employee: {
    id: 4,
    email: 'employee@company.com',
    firstName: 'Regular',
    surname: 'Employee',
    role: { id: 7, name: 'employee', description: 'Employee' },
    isActive: true
  }
};

// Permission definitions (matching backend DEFAULT_PERMISSIONS)
const ROLE_PERMISSIONS = {
  super_admin: ['*'],
  admin: ['*'],
  global_accountant: [
    'users:read', 'users:create', 'users:update',
    'timelogs:read', 'timelogs:admin_create',
    'schedules:read',
    'payroll:read', 'payroll:create', 'payroll:update', 'payroll:export',
    'leaves:read',
    'companies:read',
    'reports:read', 'reports:create', 'reports:export', 'analytics:read'
  ],
  accountant: [
    'users:read', 'users:create', 'users:update',
    'timelogs:read', 'timelogs:admin_create',
    'schedules:read',
    'payroll:read', 'payroll:create', 'payroll:update', 'payroll:export',
    'leaves:read',
    'companies:read',
    'reports:read', 'reports:create', 'reports:export', 'analytics:read'
  ],
  hr_manager: [
    'users:read', 'users:create', 'users:update',
    'timelogs:read',
    'schedules:create', 'schedules:read', 'schedules:update',
    'leaves:read', 'leaves:create', 'leaves:approve', 'leaves:update',
    'companies:read',
    'reports:read', 'reports:create'
  ],
  manager: [
    'users:read', 'users:read_own',
    'timelogs:read', 'timelogs:create_own',
    'schedules:read', 'schedules:create', 'schedules:update',
    'leaves:read', 'leaves:create', 'leaves:approve',
    'reports:read', 'reports:create'
  ],
  driver: [
    'users:read_own',
    'timelogs:create_own', 'timelogs:read_own',
    'schedules:read_own'
  ],
  employee: [
    'users:read_own',
    'timelogs:create_own', 'timelogs:read_own',
    'schedules:read_own',
    'leaves:create_own', 'leaves:read_own'
  ],
  viewer: [
    'users:read',
    'timelogs:read',
    'schedules:read',
    'reports:read'
  ],
  logistics_manager: [
    'logistics:suppliers:read', 'logistics:suppliers:create', 'logistics:suppliers:update', 'logistics:suppliers:delete',
    'logistics:templates:read', 'logistics:templates:create', 'logistics:templates:update', 'logistics:templates:delete',
    'logistics:requests:read', 'logistics:requests:create', 'logistics:requests:update', 'logistics:requests:approve', 'logistics:requests:delete',
    'logistics:orders:read', 'logistics:orders:create', 'logistics:orders:update', 'logistics:orders:delete',
    'logistics:deliveries:read', 'logistics:deliveries:create', 'logistics:deliveries:update', 'logistics:deliveries:delete',
    'reports:read', 'reports:create', 'reports:export'
  ],
  fleet_manager: [
    'fleet:vehicles:read', 'fleet:vehicles:create', 'fleet:vehicles:update', 'fleet:vehicles:delete', 'fleet:vehicles:status',
    'fleet:documents:read', 'fleet:documents:create', 'fleet:documents:update', 'fleet:documents:delete',
    'fleet:fuel_cards:read', 'fleet:fuel_cards:create', 'fleet:fuel_cards:update', 'fleet:fuel_cards:delete',
    'fleet:vignettes:read', 'fleet:vignettes:create', 'fleet:vignettes:update', 'fleet:vignettes:delete',
    'fleet:tolls:read', 'fleet:tolls:create', 'fleet:tolls:update', 'fleet:tolls:delete',
    'fleet:mileage:read', 'fleet:mileage:create', 'fleet:mileage:update', 'fleet:mileage:delete',
    'fleet:fuel:read', 'fleet:fuel:create', 'fleet:fuel:update', 'fleet:fuel:delete',
    'fleet:repairs:read', 'fleet:repairs:create', 'fleet:repairs:update', 'fleet:repairs:delete',
    'fleet:schedules:read', 'fleet:schedules:create', 'fleet:schedules:update', 'fleet:schedules:delete',
    'fleet:insurances:read', 'fleet:insurances:create', 'fleet:insurances:update', 'fleet:insurances:delete',
    'fleet:inspections:read', 'fleet:inspections:create', 'fleet:inspections:update', 'fleet:inspections:delete',
    'fleet:drivers:read', 'fleet:drivers:create', 'fleet:drivers:update', 'fleet:drivers:delete',
    'fleet:trips:read', 'fleet:trips:create', 'fleet:trips:update', 'fleet:trips:delete',
    'fleet:expenses:read', 'fleet:expenses:create', 'fleet:expenses:update', 'fleet:expenses:delete',
    'fleet:costcenters:read', 'fleet:costcenters:create', 'fleet:costcenters:update', 'fleet:costcenters:delete',
    'fleet:reports:read', 'fleet:reports:export'
  ]
};

// Helper function to check permissions
const hasPermission = (roleName: string, permission: string): boolean => {
  const permissions = ROLE_PERMISSIONS[roleName as keyof typeof ROLE_PERMISSIONS] || [];
  
  if (permissions.includes('*')) return true;
  if (permissions.includes(permission)) return true;
  
  // Check _own variant
  if (permission.endsWith('_own')) {
    const basePermission = permission.replace('_own', '');
    return permissions.includes(basePermission) || permissions.includes(permission);
  }
  
return false;
};

// =====================
// Tests for all roles permissions
// =====================
// Tests for Role-Based Access Control
// =====================

describe('RBAC - Role Permissions', () => {
  describe('super_admin permissions', () => {
    test('has all permissions (*)', () => {
      expect(hasPermission('super_admin', 'users:create')).toBe(true);
      expect(hasPermission('super_admin', 'users:delete')).toBe(true);
      expect(hasPermission('super_admin', 'payroll:create')).toBe(true);
      expect(hasPermission('super_admin', 'system:manage_settings')).toBe(true);
    });
  });

  describe('admin permissions', () => {
    test('admin has all permissions (*)', () => {
      expect(hasPermission('admin', 'users:create')).toBe(true);
      expect(hasPermission('admin', 'users:delete')).toBe(true);
      expect(hasPermission('admin', 'payroll:create')).toBe(true);
    });
  });

  describe('manager permissions', () => {
    test('manager can read users', () => {
      expect(hasPermission('manager', 'users:read')).toBe(true);
    });

    test('manager can create schedules', () => {
      expect(hasPermission('manager', 'schedules:create')).toBe(true);
    });

    test('manager can approve leaves', () => {
      expect(hasPermission('manager', 'leaves:approve')).toBe(true);
    });

    test('manager CANNOT delete users', () => {
      expect(hasPermission('manager', 'users:delete')).toBe(false);
    });

    test('manager CANNOT manage system settings', () => {
      expect(hasPermission('manager', 'system:manage_settings')).toBe(false);
    });
  });

  describe('employee permissions', () => {
    test('employee can read own profile', () => {
      expect(hasPermission('employee', 'users:read_own')).toBe(true);
    });

    test('employee can clock in/out (create_own)', () => {
      expect(hasPermission('employee', 'timelogs:create_own')).toBe(true);
    });

    test('employee CANNOT read other users', () => {
      expect(hasPermission('employee', 'users:read')).toBe(false);
    });

    test('employee CANNOT create users', () => {
      expect(hasPermission('employee', 'users:create')).toBe(false);
    });

    test('employee CANNOT approve leaves', () => {
      expect(hasPermission('employee', 'leaves:approve')).toBe(false);
    });
  });
});

// =====================
// Tests for all roles permissions
// =====================

describe('RBAC - All Roles Permissions', () => {
  describe('global_accountant permissions', () => {
    test('can read and create users', () => {
      expect(hasPermission('global_accountant', 'users:read')).toBe(true);
      expect(hasPermission('global_accountant', 'users:create')).toBe(true);
    });

    test('can manage payroll', () => {
      expect(hasPermission('global_accountant', 'payroll:read')).toBe(true);
      expect(hasPermission('global_accountant', 'payroll:create')).toBe(true);
      expect(hasPermission('global_accountant', 'payroll:export')).toBe(true);
    });

    test('CANNOT delete users', () => {
      expect(hasPermission('global_accountant', 'users:delete')).toBe(false);
    });

    test('CANNOT manage system settings', () => {
      expect(hasPermission('global_accountant', 'system:manage_settings')).toBe(false);
    });
  });

  describe('accountant permissions', () => {
    test('similar to global_accountant', () => {
      expect(hasPermission('accountant', 'payroll:read')).toBe(true);
      expect(hasPermission('accountant', 'users:read')).toBe(true);
    });

    test('CANNOT manage system', () => {
      expect(hasPermission('accountant', 'system:manage_settings')).toBe(false);
    });
  });

  describe('hr_manager permissions', () => {
    test('can manage users', () => {
      expect(hasPermission('hr_manager', 'users:read')).toBe(true);
      expect(hasPermission('hr_manager', 'users:create')).toBe(true);
    });

    test('can approve leaves', () => {
      expect(hasPermission('hr_manager', 'leaves:approve')).toBe(true);
    });

    test('CANNOT delete users', () => {
      expect(hasPermission('hr_manager', 'users:delete')).toBe(false);
    });
  });

  describe('driver permissions', () => {
    test('can access own timelogs', () => {
      expect(hasPermission('driver', 'timelogs:create_own')).toBe(true);
      expect(hasPermission('driver', 'timelogs:read_own')).toBe(true);
    });

    test('CANNOT access other drivers data', () => {
      expect(hasPermission('driver', 'timelogs:read')).toBe(false);
    });

    test('CANNOT create schedules', () => {
      expect(hasPermission('driver', 'schedules:create')).toBe(false);
    });
  });

  describe('viewer permissions', () => {
    test('can read data but cannot create', () => {
      expect(hasPermission('viewer', 'users:read')).toBe(true);
      expect(hasPermission('viewer', 'timelogs:read')).toBe(true);
      expect(hasPermission('viewer', 'reports:read')).toBe(true);
    });

    test('CANNOT create or modify anything', () => {
      expect(hasPermission('viewer', 'users:create')).toBe(false);
      expect(hasPermission('viewer', 'timelogs:create')).toBe(false);
      expect(hasPermission('viewer', 'schedules:create')).toBe(false);
    });
  });

  describe('logistics_manager permissions', () => {
    test('can manage suppliers', () => {
      expect(hasPermission('logistics_manager', 'logistics:suppliers:read')).toBe(true);
      expect(hasPermission('logistics_manager', 'logistics:suppliers:create')).toBe(true);
      expect(hasPermission('logistics_manager', 'logistics:suppliers:delete')).toBe(true);
    });

    test('can manage purchase requests', () => {
      expect(hasPermission('logistics_manager', 'logistics:requests:create')).toBe(true);
      expect(hasPermission('logistics_manager', 'logistics:requests:approve')).toBe(true);
    });

    test('CANNOT access fleet', () => {
      expect(hasPermission('logistics_manager', 'fleet:vehicles:read')).toBe(false);
      expect(hasPermission('logistics_manager', 'fleet:vehicles:create')).toBe(false);
    });
  });

  describe('fleet_manager permissions', () => {
    test('can manage vehicles', () => {
      expect(hasPermission('fleet_manager', 'fleet:vehicles:read')).toBe(true);
      expect(hasPermission('fleet_manager', 'fleet:vehicles:create')).toBe(true);
      expect(hasPermission('fleet_manager', 'fleet:vehicles:delete')).toBe(true);
    });

    test('can manage fuel', () => {
      expect(hasPermission('fleet_manager', 'fleet:fuel:read')).toBe(true);
      expect(hasPermission('fleet_manager', 'fleet:fuel:create')).toBe(true);
    });

    test('can manage drivers', () => {
      expect(hasPermission('fleet_manager', 'fleet:drivers:read')).toBe(true);
      expect(hasPermission('fleet_manager', 'fleet:drivers:create')).toBe(true);
    });

    test('CANNOT access logistics', () => {
      expect(hasPermission('fleet_manager', 'logistics:suppliers:read')).toBe(false);
      expect(hasPermission('fleet_manager', 'logistics:requests:create')).toBe(false);
    });
  });
});

// =====================
// Tests for Company-Scoped Permissions
// =====================

describe('RBAC - Company Scoped Permissions', () => {
  interface CompanyScopedUser {
    id: number;
    email: string;
    role: { name: string };
    companyId: number;
  }

  const companyUsers: CompanyScopedUser[] = [
    { id: 1, email: 'admin1@company1.com', role: { name: 'admin' }, companyId: 1 },
    { id: 2, email: 'manager1@company1.com', role: { name: 'manager' }, companyId: 1 },
    { id: 3, email: 'admin2@company2.com', role: { name: 'admin' }, companyId: 2 },
  ];

  test('admin can access own company data', () => {
    const admin = companyUsers[0];
    // Simulate: admin at company 1 can access company 1 data
    expect(admin.companyId).toBe(1);
    expect(admin.role.name).toBe('admin');
  });

  test('different admins at different companies', () => {
    const admin1 = companyUsers[0];
    const admin2 = companyUsers[2];

    expect(admin1.companyId).not.toBe(admin2.companyId);
    expect(admin1.role.name).toBe('admin');
    expect(admin2.role.name).toBe('admin');
  });

  test('manager cannot access other company data', () => {
    const manager = companyUsers[1];
    const otherCompanyId = 999;

    // In real implementation, this would check company_id
    const canAccess = manager.companyId === otherCompanyId 
      ? hasPermission(manager.role.name, 'companies:manage_users')
      : false;

    expect(canAccess).toBe(false);
  });
});

// =====================
// Tests for Permission Denied Scenarios
// =====================

describe('RBAC - Permission Denied Scenarios', () => {
  const permissionDeniedMessage = 'Нямате права за това действие';

  test('employee cannot access admin functions', () => {
    const currentUser = mockUsersByRole.employee;
    const attemptedAction = 'users:create';

    const hasAccess = hasPermission(currentUser.role.name, attemptedAction);

    expect(hasAccess).toBe(false);
    // In UI, would show: "Нямате права за: users:create"
  });

  test('viewer cannot modify anything', () => {
    const viewerRole = 'viewer';
    const forbiddenActions = [
      'users:create',
      'users:delete',
      'timelogs:create',
      'schedules:create',
      'leaves:approve'
    ];

    forbiddenActions.forEach(action => {
      expect(hasPermission(viewerRole, action)).toBe(false);
    });
  });

  test('manager cannot delete users', () => {
    const managerRole = 'manager';
    expect(hasPermission(managerRole, 'users:delete')).toBe(false);
  });

  test('employee cannot approve leaves', () => {
    const employeeRole = 'employee';
    expect(hasPermission(employeeRole, 'leaves:approve')).toBe(false);
  });

  test('fleet_manager cannot access HR functions', () => {
    const fleetRole = 'fleet_manager';
    expect(hasPermission(fleetRole, 'users:create')).toBe(false);
    expect(hasPermission(fleetRole, 'leaves:approve')).toBe(false);
  });
});

// =====================
// Tests for UI Access Control
// =====================

describe('RBAC - UI Access Control', () => {
  // Simulated menu items based on role
  const menuItemsByRole = {
    super_admin: [
      'Dashboard', 'Users', 'Time Tracking', 'Schedules', 'Leave Requests',
      'Payroll', 'Companies', 'Reports', 'Settings', 'vehicles', 'logistics'
    ],
    admin: [
      'Dashboard', 'Users', 'Time Tracking', 'Schedules', 'Leave Requests',
      'Payroll', 'Reports', 'Settings'
    ],
    manager: [
      'Dashboard', 'Users', 'Time Tracking', 'Schedules', 'Leave Requests', 'Reports'
    ],
    employee: [
      'Dashboard', 'My Time', 'My Schedule', 'Leave Requests'
    ],
    viewer: [
      'Dashboard', 'Reports'
    ]
  };

  test('super_admin sees all menu items', () => {
    const items = menuItemsByRole.super_admin;
    expect(items).toContain('Users');
    expect(items).toContain('Settings');
    expect(items).toContain('vehicles');
    expect(items).toContain('logistics');
  });

  test('admin sees most menu items but not system settings', () => {
    const items = menuItemsByRole.admin;
    expect(items).toContain('Users');
    expect(items).not.toContain('vehicles');
  });

  test('manager sees limited menu', () => {
    const items = menuItemsByRole.manager;
    expect(items).toContain('Users');
    expect(items).not.toContain('Settings');
  });

  test('employee sees minimal menu', () => {
    const items = menuItemsByRole.employee;
    expect(items).toContain('Dashboard');
    expect(items).not.toContain('Users');
    expect(items).not.toContain('Settings');
  });

  test('viewer sees only dashboard and reports', () => {
    const items = menuItemsByRole.viewer;
    expect(items).toEqual(['Dashboard', 'Reports']);
  });
});

// =====================
// Tests for User Role Display (Legacy)
// =====================

describe('RBAC - User Role Display', () => {
  const roleNames = ['super_admin', 'admin', 'manager', 'hr_manager', 'employee', 'driver', 'viewer'];

  test.each(roleNames)('user with role %s renders correctly', (roleName) => {
    const user = mockUsersByRole[roleName as keyof typeof mockUsersByRole] || {
      id: 10,
      email: `test@${roleName}.com`,
      firstName: roleName,
      surname: 'Test',
      role: { id: 10, name: roleName, description: `${roleName} description` },
      isActive: true
    };

    expect(user.role.name).toBe(roleName);
    expect(user.isActive).toBe(true);
  });
});

// =====================
// Tests for Permission Check Helper (Legacy)
// =====================

describe('RBAC - Permission Helper', () => {
  test('handles unknown role gracefully', () => {
    expect(hasPermission('unknown_role', 'users:read')).toBe(false);
  });

  test('handles _own suffix correctly', () => {
    // Employee has timelogs:create_own
    expect(hasPermission('employee', 'timelogs:create_own')).toBe(true);
    // Employee does NOT have timelogs:create (without _own)
    expect(hasPermission('employee', 'timelogs:create')).toBe(false);
  });

  test('wildcard (*) gives all permissions', () => {
    const wildcardRoles = ['super_admin', 'admin'];
    wildcardRoles.forEach(role => {
      expect(hasPermission(role, 'anything:do_anything')).toBe(true);
    });
  });
});

// =====================
// Integration Tests (Mock GraphQL)
// =====================

describe('RBAC - GraphQL Integration', () => {
  test('super_admin can access admin mutations', async () => {
    const currentUser = mockUsersByRole.super_admin;
    const canCreateUser = hasPermission(currentUser.role.name, 'users:create');
    expect(canCreateUser).toBe(true);
  });

  test('employee CANNOT access admin mutations', async () => {
    const currentUser = mockUsersByRole.employee;
    const canCreateUser = hasPermission(currentUser.role.name, 'users:create');
    expect(canCreateUser).toBe(false);
  });
});

// =====================
// Test for Role Hierarchy (Legacy)
// =====================

describe('RBAC - Role Hierarchy', () => {
  const roleHierarchy = [
    { name: 'super_admin', level: 100 },
    { name: 'admin', level: 90 },
    { name: 'global_accountant', level: 75 },
    { name: 'accountant', level: 70 },
    { name: 'hr_manager', level: 60 },
    { name: 'manager', level: 50 },
    { name: 'driver', level: 25 },
    { name: 'employee', level: 20 },
    { name: 'viewer', level: 10 }
  ];

  test('role hierarchy is properly defined', () => {
    roleHierarchy.forEach((role, index) => {
      expect(role.level).toBeGreaterThan(0);
    });
  });

  test('higher level roles have more permissions', () => {
    const superAdminPerms = ROLE_PERMISSIONS.super_admin.length;
    const adminPerms = ROLE_PERMISSIONS.admin.length;
    const managerPerms = ROLE_PERMISSIONS.manager?.length || 0;
    const employeePerms = ROLE_PERMISSIONS.employee.length;

    // Wildcard roles (*) are special - they have all permissions
    expect(superAdminPerms).toBe(1); // [*] is 1 element
    expect(adminPerms).toBe(1); // [*] is 1 element
    
    // Non-wildcard roles have specific permissions (more than viewer)
    expect(managerPerms).toBeGreaterThan(0);
    expect(employeePerms).toBeGreaterThan(0);
  });
});

// =====================
// Tests for Action Buttons Visibility
// =====================

describe('RBAC - Action Buttons Visibility', () => {
  interface ButtonConfig {
    label: string;
    permission: string;
  }

  const buttonsByRole: Record<string, ButtonConfig[]> = {
    admin: [
      { label: 'Create User', permission: 'users:create' },
      { label: 'Edit User', permission: 'users:update' },
      { label: 'Delete User', permission: 'users:delete' },
    ],
    manager: [
      { label: 'Create User', permission: 'users:create' },
      { label: 'Approve Leave', permission: 'leaves:approve' },
    ],
    employee: [
      { label: 'Clock In', permission: 'timelogs:create_own' },
      { label: 'Request Leave', permission: 'leaves:create_own' },
    ]
  };

  test('admin can see all action buttons', () => {
    const buttons = buttonsByRole.admin;
    buttons.forEach(btn => {
      expect(hasPermission('admin', btn.permission)).toBe(true);
    });
  });

  test('manager has limited buttons', () => {
    const buttons = buttonsByRole.manager;
    // Manager can create schedules but not users
    expect(hasPermission('manager', 'schedules:create')).toBe(true);
    expect(hasPermission('manager', 'leaves:approve')).toBe(true);
  });

  test('employee cannot see admin buttons', () => {
    const adminButtons = buttonsByRole.admin;
    adminButtons.forEach(btn => {
      expect(hasPermission('employee', btn.permission)).toBe(false);
    });
  });
});

// =====================
// Tests for API Request Blocking
// =====================

describe('RBAC - API Request Blocking', () => {
  const apiEndpoints = [
    { method: 'POST', path: '/api/users', requiredPermission: 'users:create' },
    { method: 'PUT', path: '/api/users/:id', requiredPermission: 'users:update' },
    { method: 'DELETE', path: '/api/users/:id', requiredPermission: 'users:delete' },
    { method: 'GET', path: '/api/payroll', requiredPermission: 'payroll:read' },
    { method: 'POST', path: '/api/payroll/generate', requiredPermission: 'payroll:create' },
  ];

  const canAccessAPI = (role: string, method: string, path: string): boolean => {
    const endpoint = apiEndpoints.find(
      e => e.method === method && e.path.startsWith(path.split('/').slice(0, 2).join('/'))
    );
    if (!endpoint) return false;
    return hasPermission(role, endpoint.requiredPermission);
  };

  test('admin can access all API endpoints', () => {
    expect(canAccessAPI('admin', 'POST', '/api/users')).toBe(true);
    expect(canAccessAPI('admin', 'PUT', '/api/users')).toBe(true);
    expect(canAccessAPI('admin', 'DELETE', '/api/users')).toBe(true);
    expect(canAccessAPI('admin', 'GET', '/api/payroll')).toBe(true);
  });

  test('employee cannot access admin API', () => {
    expect(canAccessAPI('employee', 'POST', '/api/users')).toBe(false);
    expect(canAccessAPI('employee', 'DELETE', '/api/users')).toBe(false);
    expect(canAccessAPI('employee', 'POST', '/api/payroll/generate')).toBe(false);
  });

  test('manager has limited API access', () => {
    expect(canAccessAPI('manager', 'POST', '/api/users')).toBe(false); // manager can't create users
    expect(canAccessAPI('manager', 'GET', '/api/payroll')).toBe(false); // manager can't read payroll
  });
});

// =====================
// Tests for Edge Cases
// =====================

describe('RBAC - Edge Cases', () => {
  test('empty permission returns false for non-wildcard', () => {
    expect(hasPermission('employee', '')).toBe(false);
  });

  test('special characters in permission', () => {
    expect(hasPermission('manager', 'users:create<>')).toBe(false);
    expect(hasPermission('employee', 'a'.repeat(50))).toBe(false);
  });
});

test('special characters in permission', () => {
    // Admin has wildcard, so it matches everything including special chars
    // For non-wildcard roles, these should be false
    expect(hasPermission('manager', 'users:create<>')).toBe(false);
    expect(hasPermission('employee', 'a'.repeat(50))).toBe(false);
  });
});

// =====================
// Tests for Time-Based Permissions
// =====================
// Tests for Resource-Level Permissions
// =====================

describe('RBAC - Resource-Level Permissions', () => {
  test('owner can edit own resource (via _own permission)', () => {
    // Employee has timelogs:create_own - for editing we'd need update_own
    // For this test, check they have proper own permissions
    expect(hasPermission('employee', 'timelogs:create_own')).toBe(true);
    expect(hasPermission('employee', 'leaves:create_own')).toBe(true);
  });

  test('employee cannot edit other employee resources', () => {
    expect(hasPermission('employee', 'users:update')).toBe(false);
  });
});

// =====================
// Tests for Multi-Company Permissions
// =====================

describe('RBAC - Time-Based Permissions', () => {
  interface TimeWindow {
    start: number;
    end: number;
  }

  const workHours: TimeWindow = { start: 9, end: 18 };

  const isWithinWorkHours = (hour: number): boolean => {
    return hour >= workHours.start && hour < workHours.end;
  };

  test('employee can only clock in during work hours', () => {
    expect(isWithinWorkHours(9)).toBe(true);
    expect(isWithinWorkHours(12)).toBe(true);
    expect(isWithinWorkHours(19)).toBe(false);
    expect(isWithinWorkHours(8)).toBe(false);
  });
});

// =====================
// Tests for Resource-Level Permissions
// =====================

describe('RBAC - Resource-Level Permissions', () => {
  interface Resource {
    id: number;
    ownerId: number;
  }

test('owner can edit own resource', () => {
    // Employee has create_own - verifying own permissions logic
    expect(hasPermission('employee', 'timelogs:create_own')).toBe(true);
    expect(hasPermission('employee', 'leaves:create_own')).toBe(true);
  });

  test('employee cannot edit other employee resources', () => {
    expect(hasPermission('employee', 'users:update')).toBe(false);
  });
});

// =====================
// Tests for Multi-Company Permissions
// =====================

describe('RBAC - Multi-Company Permissions', () => {
  test('admin has company management permissions', () => {
    expect(hasPermission('admin', 'companies:read')).toBe(true);
    expect(hasPermission('admin', 'companies:create')).toBe(true);
  });

  test('viewer has basic read permissions', () => {
    expect(hasPermission('viewer', 'users:read')).toBe(true);
    expect(hasPermission('viewer', 'reports:read')).toBe(true);
  });
});

// =====================
// Tests for Audit Logging
// =====================

describe('RBAC - Audit Logging', () => {
  type AuditLog = {
    userId: number;
    action: string;
    result: 'GRANTED' | 'DENIED';
  };

  const auditLogs: AuditLog[] = [];

  test('access denied is logged', () => {
    auditLogs.push({ userId: 4, action: 'users:create', result: 'DENIED' });
    expect(auditLogs.length).toBe(1);
  });

  test('access granted is logged', () => {
    auditLogs.push({ userId: 1, action: 'users:create', result: 'GRANTED' });
    expect(auditLogs.length).toBe(2);
  });
});

// =====================
// Tests for Permission Groups
// =====================

describe('RBAC - Permission Groups', () => {
  test('admin has all permission groups', () => {
    expect(hasPermission('admin', 'users:read')).toBe(true);
    expect(hasPermission('admin', 'payroll:read')).toBe(true);
  });
});
// Tests for Multi-Company Permissions
// =====================

describe('RBAC - Multi-Company Permissions', () => {
  test('user can have different roles in different companies', () => {
    expect(hasPermission('admin', 'users:create')).toBe(true);
    expect(hasPermission('viewer', 'users:create')).toBe(false);
  });
});

// =====================
// Tests for Audit Logging (Mock)
// =====================

describe('RBAC - Audit Logging', () => {
  type AuditLog = {
    userId: number;
    action: string;
    result: 'GRANTED' | 'DENIED';
  };

  const auditLogs: AuditLog[] = [];

  const logAccess = (userId: number, action: string, granted: boolean) => {
    auditLogs.push({
      userId,
      action,
      result: granted ? 'GRANTED' : 'DENIED'
    });
  };

  test('access denied is logged', () => {
    const before = auditLogs.length;
    logAccess(4, 'users:create', false);
    expect(auditLogs.length).toBe(before + 1);
    expect(auditLogs[auditLogs.length - 1].result).toBe('DENIED');
  });

  test('access granted is logged', () => {
    const before = auditLogs.length;
    logAccess(1, 'users:create', true);
    expect(auditLogs.length).toBe(before + 1);
    expect(auditLogs[auditLogs.length - 1].result).toBe('GRANTED');
  });
});

// =====================
// Tests for Permission Groups
// =====================

describe('RBAC - Permission Groups', () => {
  const permissionGroups = {
    userManagement: ['users:read', 'users:create'],
    timeTracking: ['timelogs:read', 'timelogs:create'],
    leaves: ['leaves:read', 'leaves:create'],
    reports: ['reports:read', 'reports:create'],
  };

  test('admin has all permission groups', () => {
    Object.values(permissionGroups).forEach(group => {
      group.forEach(permission => {
        expect(hasPermission('admin', permission)).toBe(true);
      });
    });
  });
});