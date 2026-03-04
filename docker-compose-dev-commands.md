# ---------------------------------------------------------------------------
# Development Commands for WorkingTime
# ---------------------------------------------------------------------------

# 🚀 START SERVICES
# ---------------------------------------------------------------------------

# Start Production Services (backend + frontend + nginx):
docker compose up -d

# Start Development Services (hot reload, monitoring):
docker compose --profile dev up -d

# Start Only Backend (for API testing):
docker compose up -d db backend

# Start Only Frontend (for UI testing):
docker compose up -d db backend frontend

# Start Full Development Stack (with monitoring):
docker compose --profile dev --profile monitoring up -d

# 🛑 STOP SERVICES
# ---------------------------------------------------------------------------

# Stop All Services:
docker compose down

# Stop Development Services Only:
docker compose --profile dev down

# Stop with Volume Cleanup:
docker compose down -v

# 📋 VIEW STATUS
# ---------------------------------------------------------------------------

# View All Running Services:
docker compose ps

# View Logs for All Services:
docker compose logs -f

# View Logs for Specific Service:
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 🗄️ DATABASE OPERATIONS
# ---------------------------------------------------------------------------

# Access Database:
docker compose exec -it chronos-DB psql -U postgres -d workingtimedb

# Database Backup:
docker compose exec chronos-DB pg_dump -U postgres workingtimedb > backup.sql

# Restore Database:
docker compose exec -i chronos-DB psql -U postgres workingtimedb < backup.sql

# 🧪 TESTING & DEVELOPMENT
# ---------------------------------------------------------------------------

# Run Database Migrations:
docker compose exec -it chronos-API python -m alembic upgrade head

# Create New Migration:
docker compose exec -it chronos-API python -m alembic revision --autogenerate -m "description"

# Rollback Migration:
docker compose exec -it chronos-API python -m alembic downgrade -1

# Seed RBAC Data (after initial setup):
docker compose exec -it chronos-API python scripts/seed_rbac.py

# Performance Testing:
docker compose exec -it chronos-API python scripts/performance_testing.py

# Google Calendar Sync Status:
docker compose exec -it chronos-API python scripts/google_sync_status.py

# Health Check:
docker compose exec -it chronos-API python scripts/health_monitor.py

# 🔧 DEVELOPMENT ACCESS
# ---------------------------------------------------------------------------

# Access Backend Shell:
docker compose exec -it chronos-API bash

# Access Frontend Shell:
docker compose exec -it chronos-FE bash

# Install New Dependencies (Backend):
docker compose exec -it chronos-API pip install package-name

# Install New Dependencies (Frontend):
docker compose exec -it chronos-FE npm install package-name

# 📊 MONITORING
# ---------------------------------------------------------------------------

# Access Prometheus:
curl http://localhost:9090
# Web UI: http://localhost:9090

# Access Grafana:
curl http://localhost:3002
# Web UI: http://localhost:3002 (admin/admin123)

# View Database Metrics:
curl http://localhost:9187/metrics

# 🌐 SERVICE URLs
# ---------------------------------------------------------------------------

# Production Services:
# Frontend: http://localhost:3000
# Backend API: http://localhost:14240
# Nginx Proxy Manager: http://localhost:81

# Development Services:
# Frontend Dev: http://localhost:3001
# Backend Dev API: http://localhost:14241
# Monitoring: http://localhost:9090 (Prometheus)
# Dashboards: http://localhost:3002 (Grafana)

# 📱 ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------
# Create .env file with:
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
# POSTGRES_DB=workingtimedb
# JWT_SECRET_KEY=your-secret-key-here
# BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
# GOOGLE_CLIENT_ID=your-google-client-id
# GOOGLE_CLIENT_SECRET=your-google-client-secret
# DEBUG=false
# DB_POOL_SIZE=20
# DB_MAX_OVERFLOW=30
# TIMEZONE=Europe/Sofia
# VITE_API_URL=http://localhost:14240
# VITE_ENABLE_RBC=true
# VITE_ENABLE_GOOGLE_CALENDAR=true

# 🔄 HOT RELOAD (Development Only)
# ---------------------------------------------------------------------------
# Frontend changes auto-reload via Vite
# Backend changes auto-reload via Uvicorn
# Volume mounts ensure live code changes

# 🚨 TROUBLESHOOTING
# ---------------------------------------------------------------------------

# Check Port Availability:
netstat -tlnp | grep :3000
netstat -tlnp | grep :14240

# Clear Docker Caches:
docker system prune -a

# Rebuild Services:
docker compose up --build -d

# View Resource Usage:
docker stats

# Check Service Health:
docker compose ps --format "table {{.Names}}\t{{.Status}}"

# 📈 PERFORMANCE TESTING
# ---------------------------------------------------------------------------

# Load Test API:
docker compose exec -it chronos-API python scripts/load_test.py

# Database Performance:
docker compose exec -it chronos-DB psql -U postgres -d workingtimedb -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"

# Index Usage Analysis:
docker compose exec -it chronos-API python scripts/index_analysis.py

# ---------------------------------------------------------------------------
# 🎯 QUICK START GUIDE
# ---------------------------------------------------------------------------

# 1. For Development:
#    docker-compose --profile dev up -d
#    Frontend: http://localhost:3001
#    Backend: http://localhost:14241

# 2. For Production Testing:
#    docker-compose up -d
#    Frontend: http://localhost:3000
#    Backend: http://localhost:14240

# 3. For Full Monitoring:
#    docker compose --profile dev --profile monitoring up -d
#    Grafana: http://localhost:3002
#    Prometheus: http://localhost:9090

# ---------------------------------------------------------------------------