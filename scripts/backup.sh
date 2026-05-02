#!/bin/bash
#
# backup.sh - Safe backup script for Chronos
# Creates backups of database, docker images, and configuration
#

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/chronos"
MAX_BACKUPS=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Chronos Backup ==="
echo "Started: $(date)"
echo ""

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Get PostgreSQL credentials from .env or use defaults
if [ -f ".env" ]; then
    source .env
fi

POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-chronosdb}
DB_HOST=${POSTGRES_HOST:-localhost}
BACKEND_NAME=${BACKEND_NAME:-chronos-backend}
FRONTEND_NAME=${FRONTEND_NAME:-chronos-frontend}

echo "Backup directory: $BACKUP_DIR"
echo "Database: $POSTGRES_DB"
echo ""

# Clean old backups (keep only MAX_BACKUPS)
echo "Cleaning old backups (keeping last $MAX_BACKUPS)..."
ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
ls -t $BACKUP_DIR/backend_*.tar 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
ls -t $BACKUP_DIR/frontend_*.tar 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
ls -t $BACKUP_DIR/config_*.tar.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# === 1. Database Backup ===
echo ""
echo "[1/3] Creating database backup..."
DB_BACKUP_FILE="$BACKUP_DIR/db_$TIMESTAMP.dump"

# Use docker exec since pg_dump is not available in the container
echo "Using docker exec for database backup..."
DB_CONTAINER=$(docker ps --filter "name=chronos-DB" --format "{{.Names}}" 2>/dev/null || docker ps --filter "name=db" --format "{{.Names}}" 2>/dev/null | head -1)

if [ -z "$DB_CONTAINER" ]; then
    echo -e "${RED}✗${NC} Database container not found"
    exit 1
fi

echo "Database container: $DB_CONTAINER"

docker exec "$DB_CONTAINER" pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "$DB_BACKUP_FILE" 2>/dev/null || {
    echo -e "${RED}✗${NC} Database backup failed"
    # Show error for debugging
    docker exec "$DB_CONTAINER" pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" 2>&1 | tail -5
    exit 1
}
echo -e "${GREEN}✓${NC} Database backup: db_$TIMESTAMP.dump"

# Verify backup
if [ -f "$DB_BACKUP_FILE" ] && [ -s "$DB_BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓${NC} Backup verified: $BACKUP_SIZE"
else
    echo -e "${RED}✗${NC} Backup file is empty or missing"
    exit 1
fi

# === 2. Docker Images Backup ===
echo ""
echo "[2/3] Creating image backups..."

# Get current images using docker inspect (more reliable than docker compose images)
BACKEND_IMAGE=$(docker inspect --format='{{.Config.Image}}' chronos-backend 2>/dev/null || echo "")
FRONTEND_IMAGE=$(docker inspect --format='{{.Config.Image}}' chronos-frontend 2>/dev/null || echo "")

if [ -n "$BACKEND_IMAGE" ]; then
    docker save "$BACKEND_IMAGE" -o "$BACKUP_DIR/backend_$TIMESTAMP.tar" 2>/dev/null || {
        echo -e "${YELLOW}!${NC} Failed to save backend image, skipping"
        BACKEND_IMAGE=""
    }
    if [ -f "$BACKUP_DIR/backend_$TIMESTAMP.tar" ]; then
        BACKEND_SIZE=$(du -h "$BACKUP_DIR/backend_$TIMESTAMP.tar" | cut -f1)
        echo -e "${GREEN}✓${NC} Backend image: backend_$TIMESTAMP.tar ($BACKEND_SIZE)"
    fi
else
    echo -e "${YELLOW}!${NC} Backend image not found, skipping"
fi

if [ -n "$FRONTEND_IMAGE" ]; then
    docker save "$FRONTEND_IMAGE" -o "$BACKUP_DIR/frontend_$TIMESTAMP.tar" 2>/dev/null || {
        echo -e "${YELLOW}!${NC} Failed to save frontend image, skipping"
        FRONTEND_IMAGE=""
    }
    if [ -f "$BACKUP_DIR/frontend_$TIMESTAMP.tar" ]; then
        FRONTEND_SIZE=$(du -h "$BACKUP_DIR/frontend_$TIMESTAMP.tar" | cut -f1)
        echo -e "${GREEN}✓${NC} Frontend image: frontend_$TIMESTAMP.tar ($FRONTEND_SIZE)"
    fi
else
    echo -e "${YELLOW}!${NC} Frontend image not found, skipping"
fi

# === 3. Configuration Backup ===
echo ""
echo "[3/3] Backing up configuration..."

if [ -f ".env" ]; then
    tar czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" .env docker-compose.yml 2>/dev/null
    echo -e "${GREEN}✓${NC} Configuration backed up"
else
    echo -e "${YELLOW}!${NC} No .env file found"
fi

echo ""
echo "=== Backup Complete ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# List current backups
echo "Current backups:"
ls -lh $BACKUP_DIR/ 2>/dev/null | grep -E "db_|backend_|frontend_|config_" || echo "No backups found"
