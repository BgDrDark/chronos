#!/bin/bash
#
# rollback.sh - Rollback script for Chronos
# Restores from a previous backup
#

TIMESTAMP=${1:-""}
BACKUP_DIR="/backups/chronos"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Chronos Rollback ==="

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}ERROR:${NC} Backup directory $BACKUP_DIR does not exist"
    exit 1
fi

# Find latest backup if no timestamp provided
if [ -z "$TIMESTAMP" ]; then
    echo "No timestamp provided, finding latest backup..."
    LATEST=$(ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | head -1)
    
    if [ -z "$LATEST" ]; then
        echo -e "${RED}ERROR:${NC} No backup found"
        exit 1
    fi
    
    TIMESTAMP=$(basename "$LATEST" | sed 's/db_//;s/.dump//')
fi

echo "Rolling back to: $TIMESTAMP"
echo ""

# Check if backup files exist
if [ ! -f "$BACKUP_DIR/db_$TIMESTAMP.dump" ]; then
    echo -e "${RED}ERROR:${NC} Backup file not found: db_$TIMESTAMP.dump"
    exit 1
fi

# Stop containers
echo "Stopping containers..."
docker compose down

# Restore Database (optional - usually not needed for rollback, just images)
# echo "Restoring database..."
# PGPASSWORD=postgres pg_restore -U postgres -d chronosdb $BACKUP_DIR/db_$TIMESTAMP.dump 2>/dev/null || true

# Restore Docker images
if [ -f "$BACKUP_DIR/backend_$TIMESTAMP.tar" ]; then
    echo "Restoring backend image..."
    docker load -i $BACKUP_DIR/backend_$TIMESTAMP.tar
    echo -e "${GREEN}✓${NC} Backend restored"
else
    echo -e "${YELLOW}!${NC} Backend backup not found, skipping"
fi

if [ -f "$BACKUP_DIR/frontend_$TIMESTAMP.tar" ]; then
    echo "Restoring frontend image..."
    docker load -i $BACKUP_DIR/frontend_$TIMESTAMP.tar
    echo -e "${GREEN}✓${NC} Frontend restored"
else
    echo -e "${YELLOW}!${NC} Frontend backup not found, skipping"
fi

# Start containers
echo "Starting containers..."
docker compose up -d

# Health check
sleep 15
echo "Checking health..."
if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}=== Rollback Complete ==="
else
    echo -e "${RED}ERROR: Health check failed after rollback"
    exit 1
fi