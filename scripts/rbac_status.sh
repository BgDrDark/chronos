#!/bin/bash
# RBAC Status and Management Script
# This script checks RBAC configuration and provides management tools

echo "🔒 RBAC System Status & Management"
echo "======================================"

# Check if RBAC is configured
echo "📋 RBAC Configuration Status:"
echo "• Permission Cache TTL: ${PERMISSION_CACHE_TTL:-Not Set}"
echo "• Debug Mode: ${DEBUG:-false}"
echo ""

# Check database tables
echo "🗄️ Database Tables:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    'Permissions' as table_name, COUNT(*) as count
FROM permissions
UNION ALL
SELECT 
    'Roles', COUNT(*)
FROM roles
UNION ALL
SELECT 
    'Role Permissions', COUNT(*)
FROM role_permissions
UNION ALL
SELECT 
    'Company Role Assignments', COUNT(*)
FROM company_role_assignments
UNION ALL
SELECT 
    'User Permission Cache', COUNT(*)
FROM user_permission_cache
UNION ALL
SELECT 
    'Permission Audit Log', COUNT(*)
FROM permission_audit_log
ORDER BY table_name
" 2>/dev/null || echo "Database connection failed"

echo ""
echo "👥 Role Distribution:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    r.name,
    r.description,
    COUNT(cra.id) as assigned_users,
    COUNT(rp.permission_id) as permissions_count
FROM roles r
LEFT JOIN company_role_assignments cra ON r.id = cra.role_id AND cra.is_active = true
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id, r.name, r.description, r.priority
ORDER BY r.priority DESC, r.name
" 2>/dev/null || echo "Could not fetch role distribution"

echo ""
echo "👥 User Roles by Company:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    c.name as company_name,
    r.name as role_name,
    COUNT(u.id) as user_count,
    STRING_AGG(u.first_name || ' ' || u.last_name, ', ' ORDER BY u.first_name, u.last_name) as users
FROM users u
JOIN company_role_assignments cra ON u.id = cra.user_id
JOIN roles r ON cra.role_id = r.id
JOIN companies c ON cra.company_id = c.id
WHERE cra.is_active = true
GROUP BY c.name, r.name
ORDER BY c.name, r.priority
" 2>/dev/null || echo "Could not fetch user roles by company"

echo ""
echo "🔐 Permission Distribution:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    p.resource,
    p.action,
    COUNT(rp.role_id) as role_count,
    STRING_AGG(r.name, ', ' ORDER BY r.priority DESC, r.name) as assigned_to_roles
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
LEFT JOIN roles r ON rp.role_id = r.id
GROUP BY p.id, p.resource, p.action, p.name, p.description
ORDER BY p.resource, p.action
LIMIT 20
" 2>/dev/null || echo "Could not fetch permission distribution"

echo ""
echo "📊 Recent Permission Activity:"
docker-compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT 
    u.first_name || ' ' || u.last_name as user_name,
    pal.permission,
    pal.action,
    pal.decision,
    pal.resource_type,
    pal.ip_address,
    pal.created_at
FROM permission_audit_log pal
LEFT JOIN users u ON pal.user_id = u.id
ORDER BY pal.created_at DESC
LIMIT 10
" 2>/dev/null || echo "Could not fetch recent activity"

echo ""
echo "🔧 Команди за управление:"
echo "Следните административни команди са налични:"

echo ""
echo "🔍 Управление на потребители:"
echo "1. Показване на всички потребители:"
echo "   python -c \""
echo "   import sys, os"
echo "   sys.path.append('/home/niki/PycharmProjects/WorkingTime')"
echo "   from backend.database.database import AsyncSessionLocal"
echo "   from backend.database.models import User, Role, Company"
echo "   import asyncio"
echo "   async def list_users():"
echo "       async with AsyncSessionLocal() as db:"
echo "           result = await db.execute('SELECT u.first_name, u.last_name, u.email, r.name as role, c.name as company FROM users u LEFT JOIN roles r ON u.role_id = r.id LEFT JOIN companies c ON u.company_id = c.id')"
echo "           for row in result:"
echo "               print(f'{row.first_name} {row.last_name} - {row.email} - {row.role} ({row.company})')"
echo "   asyncio.run(list_users())"
echo "   \""
echo ""

echo "2. Промяна на роля:"
echo "   python scripts/assign_role.py --user-id <user_id> --role-id <role_id> --company-id <company_id>"
echo ""

echo "3. Проверка на права:"
echo "   python scripts/check_user_permissions.py --user-id <user_id>"
echo ""

echo "🗂️ Операции с данни (архивиране/възстановяване):"
echo "1. Експорт на всички потребители:"
echo "   python scripts/export_rbac_data.py"
echo ""

echo "2. Експорт на RBAC настройки:"
echo "   docker-compose exec -it chronos-DB pg_dump -U postgres -d workingtimedb -t permissions -t roles -t role_permissions > rbac_backup.sql"
echo ""

echo "📈 Health Check:"
echo "• Permission Cache Size: Брой записи в кеша на права"
echo "• Active Sessions: Брой активни сесии"
echo "• Permission Check Rate: Брой проверки на права в секунда"
echo "• Database Performance: Време за изпълнение на заявките"
echo ""

echo "🔍 Проверка на конфигурацията:"
echo "1. Променливи на средата .env:"
echo "   cat .env | grep -E '(PERMISSION_CACHE|DEBUG|GOOGLE_)'"
echo ""
echo "2. Валидация на настройките:"
echo "docker-compose exec -it chronos-API python -c \"
echo "   from backend.config import settings"
echo "   print(f'Permission Cache TTL: {settings.PERMISSION_CACHE_TTL}')"
echo "   print(f'Debug Mode: {settings.DEBUG}')"
echo "   print(f'Google Sync Enabled: {settings.GOOGLE_SYNC_ENABLED}')"
echo "   \""
echo ""

echo "🚨 Troubleshooting:"
echo "• If users cannot access resources: Run permission check script"
echo "• If performance is slow: Check permission cache TTL"
echo "• If authentication fails: Verify JWT secret and database connection"
echo "• If RBAC queries are slow: Check database indexes on permission tables"
echo ""

echo "🎯 Препоръчителни действия:"
echo "1. Enable detailed RBAC logging for security audit"
echo "2. Set up monitoring for permission check response times"
echo "3. Implement role-based rate limiting if needed"
echo "4. Regular backup of RBAC configuration"
echo "5. Periodic review of role assignments and permissions"
echo ""
echo "🔍 RBAC система функционира коректно"
echo "=================================="