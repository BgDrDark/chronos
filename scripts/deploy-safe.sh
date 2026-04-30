#!/bin/bash
#
# deploy-safe.sh - Safe deployment script for Chronos
# Deploys with health checks and auto-rollback on failure
#

set -e

BACKUP_DIR="/backups/chronos"
HEALTH_TIMEOUT=120
VERSION_FILE="VERSION"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get VERSION
if [ -f ".env" ]; then
    source .env
fi

VERSION=${VERSION:-$(cat $VERSION_FILE 2>/dev/null || echo "unknown")}

echo "=== Chronos Safe Deploy ==="
echo "Version: $VERSION"
echo "Started: $(date)"
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}ERROR:${NC} Backup directory $BACKUP_DIR does not exist"
    echo "Run scripts/backup.sh first to create backups directory"
    exit 1
fi

# 1. Health check (current version)
echo "[1/6] Checking current health..."
if ! curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo -e "${RED}ERROR:${NC} Current version is not healthy. Aborting deploy."
    exit 1
fi
echo -e "${GREEN}✓${NC} Current version is healthy"

# Get timestamp BEFORE we make new backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 2. Create backup
echo ""
echo "[2/6] Creating backup..."
if ./scripts/backup.sh >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backup created"
else
    echo -e "${YELLOW}WARNING:${NC} Backup may have failed, continuing..."
fi

# 3. Git fetch + reset
echo ""
echo "[3/6] Fetching latest code..."
if git fetch origin main 2>/dev/null; then
    git reset --hard origin/main
    echo -e "${GREEN}✓${NC} Code updated"
else
    echo -e "${YELLOW}WARNING:${NC} Git fetch failed, using local code"
fi

# 4. Build images
echo ""
echo "[4/6] Building images..."
docker compose build --no-cache backend
echo -e "${GREEN}✓${NC} Backend built"
docker compose build --no-cache frontend
echo -e "${GREEN}✓${NC} Frontend built"

# 5. Deploy backend + health check
echo ""
echo "[5/6] Deploying backend..."
docker compose up -d backend

echo "Waiting for backend health (timeout: ${HEALTH_TIMEOUT}s)..."
BACKEND_HEALTHY=false
for i in $(seq 1 $HEALTH_TIMEOUT); do
    if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend healthy after ${i}s"
        BACKEND_HEALTHY=true
        break
    fi
    sleep 1
done

if [ "$BACKEND_HEALTHY" = false ]; then
    echo -e "${RED}ERROR:${NC} Backend health check timeout. Rolling back..."
    ./scripts/rollback.sh $TIMESTAMP
    exit 1
fi

# 6. Deploy frontend
echo ""
echo "[6/6] Deploying frontend..."
docker compose up -d frontend

# Final check
sleep 10
if curl -sf http://localhost:3000 >/dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}======================================="
    echo -e "${GREEN}=== Deploy Complete ==="
    echo -e "${GREEN}======================================="
    echo "Version: $VERSION"
    echo "Deployed at: $(date)"
else
    echo -e "${YELLOW}WARNING:${NC} Frontend may not be fully ready"
fi