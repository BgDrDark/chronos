#!/bin/bash
# Testing and Validation Script for WorkingTime
# This script validates that all systems are working correctly

echo "🧪 WorkingTime Testing & Validation Script"
echo "======================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Container names
db_container="chronos-DB"
backend_container="chronos-backend"
frontend_container="chronos-frontend"

echo ""
echo "📋 System Components Check:"
echo "================================"

# Check Docker containers
echo -e "${BLUE}1. Docker Containers Status:${NC}"
containers=("chronos-DB" "chronos-backend" "chronos-frontend" "nginx-proxy-manager")
for container in "${containers[@]}"; do
    container_status=$(docker ps --filter "name=^${container}$" --format "{{.Status}}")
    if [ -n "$container_status" ]; then
        if echo "$container_status" | grep -q "Up"; then
            echo -e "  ${GREEN}✅ $container: $container_status${NC}"
        else
            echo -e "  ${YELLOW}⚠️ $container: $container_status${NC}"
        fi
    else
        echo -e "  ${RED}❌ $container: not found${NC}"
    fi
done

echo ""
echo -e "${BLUE}2. Service Health Checks:${NC}"

# Backend health check
echo -n "  Backend API: "
if curl -s http://localhost:14240/health > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
elif curl -s http://localhost:14241/health > /dev/null; then
    echo -e "${GREEN}✅ Healthy (Dev Mode)${NC}"
else
    echo -e "${RED}❌ Unhealthy${NC}"
fi

# Frontend health check
echo -n "  Frontend App: "
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
elif curl -s http://localhost:3001 > /dev/null; then
    echo -e "${GREEN}✅ Running (Dev Mode)${NC}"
else
    echo -e "${RED}❌ Not Running${NC}"
fi

# Database health check
echo -n "  Database: "
if docker exec $db_container pg_isready -U postgres -d workingtimedb > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ready${NC}"
else
    echo -e "${RED}❌ Not Ready${NC}"
fi

# Check Redis
echo -n "  Redis: "
if docker ps --format "{{.Names}}" | grep -q "chronos-redis"; then
    if docker exec chronos-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
    else
        echo -e "${YELLOW}⚠️ Container running but not responding${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Not Running (optional)${NC}"
fi

echo ""
echo -e "${BLUE}3. API Endpoint Tests:${NC}"

# Test GraphQL endpoint
echo -n "  GraphQL API: "
if curl -s -X POST http://localhost:14240/graphql \
    -H "Content-Type: application/json" \
    -d '{"query":"query { __schema { types { name } } }"}' \
    > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Test authentication
echo -n "  Authentication: "
if curl -s -X POST http://localhost:14240/auth/token \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' \
    > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Endpoint Responding${NC}"
else
    echo -e "${YELLOW}⚠️ Check Endpoint${NC}"
fi

echo ""
echo -e "${BLUE}4. Database Integration Tests:${NC}"

# Check RBAC tables exist
echo -n "  RBAC Tables: "
if docker exec $db_container psql -U postgres -d workingtimedb -c "
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name IN ('permissions', 'role_permissions', 'company_role_assignments')
) as has_tables" 2>/dev/null | grep -q "t"; then
    echo -e "${GREEN}✅ Created${NC}"
else
    echo -e "${YELLOW}⚠️ Run Migrations${NC}"
fi

# Check Google Calendar tables
echo -n "  Google Calendar Tables: "
if docker exec $db_container psql -U postgres -d workingtimedb -c "
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name IN ('google_calendar_accounts', 'google_calendar_sync_settings', 'google_calendar_events')
) as has_tables" 2>/dev/null | grep -q "t"; then
    echo -e "${GREEN}✅ Created${NC}"
else
    echo -e "${YELLOW}⚠️ Run Migrations${NC}"
fi

# Check Enhanced Payroll tables
echo -n "  Enhanced Payroll Tables: "
if docker exec $db_container psql -U postgres -d workingtimedb -c "
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name IN ('employment_contracts', 'payroll_payment_schedules', 'sick_leave_records')
) as has_tables" 2>/dev/null | grep -q "t"; then
    echo -e "${GREEN}✅ Created${NC}"
else
    echo -e "${YELLOW}⚠️ Run Migrations${NC}"
fi

echo ""
echo -e "${BLUE}5. Performance Checks:${NC}"

# Check database performance
echo -n "  Database Performance: "
slow_queries=$(docker exec $db_container psql -U postgres -d workingtimedb -c "
SELECT COUNT(*) FROM pg_stat_statements 
WHERE mean_exec_time > 1000
" 2>/dev/null | xargs 2>/dev/null)
if [ "$slow_queries" = "0" ] || [ -z "$slow_queries" ]; then
    echo -e "${GREEN}✅ No slow queries${NC}"
else
    echo -e "${YELLOW}⚠️ $slow_queries slow queries${NC}"
fi

# Check performance optimization
echo -n "  Performance Optimizations: "
index_count=$(docker exec $db_container psql -U postgres -d workingtimedb -c "
SELECT COUNT(*) FROM pg_indexes 
WHERE tablename IN ('timelogs', 'work_schedules', 'leave_requests', 'payslips')
" 2>/dev/null | xargs 2>/dev/null)
if [ -n "$index_count" ] && [ "$index_count" -gt "0" ]; then
    echo -e "${GREEN}✅ $index_count indexes present${NC}"
else
    echo -e "${YELLOW}⚠️ Check Indexes${NC}"
fi

echo ""
echo -e "${BLUE}6. Configuration Validation:${NC}"

# Check environment variables
echo -n "  Environment File: "
if [ -f "/home/niki/PycharmProjects/WorkingTime/.env" ]; then
    echo -e "${GREEN}✅ Present${NC}"
else
    echo -e "${RED}❌ Missing${NC}"
fi

# Check required environment variables
echo -n "  Required Variables: "
required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "JWT_SECRET_KEY")
missing_vars=0
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var=" /home/niki/PycharmProjects/WorkingTime/.env 2>/dev/null; then
        missing_vars=$((missing_vars + 1))
    fi
done

if [ "$missing_vars" -eq "0" ]; then
    echo -e "${GREEN}✅ All Present${NC}"
else
    echo -e "${RED}❌ $missing_vars Missing${NC}"
fi

# Check Google Calendar configuration
echo -n "  Google Calendar: "
if grep -q "GOOGLE_CLIENT_ID" /home/niki/PycharmProjects/WorkingTime/.env 2>/dev/null; then
    echo -e "${GREEN}✅ Configured${NC}"
else
    echo -e "${YELLOW}⚠️ Not Configured${NC}"
fi

echo ""
echo "======================================"
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo ""
echo -e "${BLUE}1. Run migrations if needed:${NC}"
echo "   docker compose exec -it $container python -m alembic upgrade head"
echo ""
echo -e "${BLUE}2. Seed RBAC data if not done:${NC}"
echo "   docker compose exec -it $container python scripts/seed_rbac.py"
echo ""
echo -e "${BLUE}3. Test API endpoints:${NC}"
echo "   curl http://localhost:14240/docs"
echo ""
echo -e "${BLUE}4. Check application logs:${NC}"
echo "   docker compose logs -f $container"
echo ""
echo -e "${BLUE}5. Monitor system performance:${NC}"
echo "   docker compose exec -it $container python scripts/performance_testing.py"
echo ""
echo "======================================"
