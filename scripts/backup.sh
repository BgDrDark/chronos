#!/bin/bash
#
# backup.sh - Safe backup script for Chronos
# Creates backups of database and docker images
#

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/chronos"
MAX_BACKUPS=3

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
POSTGRES_DB=${POSTGRES_DB:-chronosdb}
DB_HOST=${POSTGRES_HOST:-localhost}

echo "Backup directory: $BACKUP_DIR"
echo ""

# Clean old backups (keep only MAX_BACKUPS)
echo "Cleaning old backups (keeping last $MAX_BACKUPS)..."
if ls $BACKUP_DIR/db_*.dump >/dev/null 2>&1; then
    ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
    ls -t $BACKUP_DIR/backend_*.tar 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
    ls -t $BACKUP_DIR/frontend_*.tar 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
fi

# Database Backup
echo "Creating database backup..."
if command -v pg_dump &> /dev/null; then
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U "$POSTGRES_USER" -h "$DB_HOST" -Fc "$POSTGRES_DB" -f "$BACKUP_DIR/db_$TIMESTAMP.dump" 2>/dev/null || \
    pg_dump -U "$POSTGRES_USER" -h "$DB_HOST" -Fc "$POSTGRES_DB" -f "$BACKUP_DIR/db_$TIMESTAMP.dump"
    echo -e "${GREEN}✓${NC} Database backup: db_$TIMESTAMP.dump"
else
    echo -e "${YELLOW}!${NC} pg_dump not found in PATH, skipping database backup"
fi

# Docker Images Backup
echo "Creating image backups..."

# Get current images
BACKEND_IMAGE=$(docker compose images -q backend 2>/dev/null || echo "")
FRONTEND_IMAGE=$(docker compose images -q frontend 2>/dev/null || echo "")

if [ -n "$BACKEND_IMAGE" ]; then
    docker save $BACKEND_IMAGE -o "$BACKUP_DIR/backend_$TIMESTAMP.tar"
    echo -e "${GREEN}✓${NC} Backend image: backend_$TIMESTAMP.tar"
else
    echo -e "${YELLOW}!${NC} Backend image not found, skipping"
fi

if [ -n "$FRONTEND_IMAGE" ]; then
    docker save $FRONTEND_IMAGE -o "$BACKUP_DIR/frontend_$TIMESTAMP.tar"
    echo -e "${GREEN}✓${NC} Frontend image: frontend_$TIMESTAMP.tar"
else
    echo -e "${YELLOW}!${NC} Frontend image not found, skipping"
fi

echo ""
echo "=== Backup Complete ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# List current backups
echo "Current backups:"
ls -lh $BACKUP_DIR/ 2>/dev/null | grep -E "db_|backend_|frontend_" || echo "No backups found"