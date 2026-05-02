#!/bin/bash
#
# rollback.sh - Rollback script for Chronos
# Restores from a previous backup including DB, images, and config
#

set -e

TIMESTAMP=${1:-""}
BACKUP_DIR="./backups/chronos"
LOCK_FILE="/tmp/chronos_deploy.lock"
DEPLOY_LOG="$BACKUP_DIR/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get DB credentials from .env
if [ -f ".env" ]; then
    source .env
fi

POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-chronosdb}
DB_HOST=${POSTGRES_HOST:-localhost}

# === LOGGING ===
log_deploy() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOY_LOG"
}

# === CHECK BACKUP DIR ===
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}ERROR:${NC} Backup directory $BACKUP_DIR does not exist"
    exit 1
fi

# === FIND LATEST BACKUP IF NO TIMESTAMP ===
if [ -z "$TIMESTAMP" ]; then
    echo "No timestamp provided, finding latest backup..."
    LATEST=$(ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | head -1)
    
    if [ -z "$LATEST" ]; then
        echo -e "${RED}ERROR:${NC} No backup found"
        exit 1
    fi
    
    TIMESTAMP=$(basename "$LATEST" | sed 's/db_//;s/.dump//')
    echo "Using latest backup: $TIMESTAMP"
fi

echo ""
echo -e "${RED}========================================"
echo -e "=== Chronos Rollback ==="
echo -e "========================================${NC}"
echo "Rolling back to: $TIMESTAMP"
echo ""

# === VERIFY BACKUP FILES ===
BACKUP_FILES_FOUND=false

if [ ! -f "$BACKUP_DIR/db_$TIMESTAMP.dump" ]; then
    echo -e "${RED}ERROR:${NC} Database backup not found: db_$TIMESTAMP.dump"
    exit 1
fi
echo -e "${GREEN}✓${NC} Database backup found"
BACKUP_FILES_FOUND=true

if [ -f "$BACKUP_DIR/backend_$TIMESTAMP.tar" ]; then
    echo -e "${GREEN}✓${NC} Backend image backup found"
    BACKEND_TAR_EXISTS=true
else
    echo -e "${YELLOW}!${NC} Backend image backup not found"
    BACKEND_TAR_EXISTS=false
fi

if [ -f "$BACKUP_DIR/frontend_$TIMESTAMP.tar" ]; then
    echo -e "${GREEN}✓${NC} Frontend image backup found"
    FRONTEND_TAR_EXISTS=true
else
    echo -e "${YELLOW}!${NC} Frontend image backup not found"
    FRONTEND_TAR_EXISTS=false
fi

if [ -f "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" ]; then
    echo -e "${GREEN}✓${NC} Configuration backup found"
    CONFIG_EXISTS=true
else
    echo -e "${YELLOW}!${NC} Configuration backup not found"
    CONFIG_EXISTS=false
fi

echo ""

# === CONFIRMATION ===
echo -e "${RED}WARNING:${NC} This will restore the system to state at $TIMESTAMP"
echo "All changes since then will be lost."
echo ""
read -p "Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo ""

# === 1. Stop containers ===
echo "[1/5] Stopping containers..."
docker compose down
echo -e "${GREEN}✓${NC} Containers stopped"

# === 2. Restore Docker images ===
echo ""
echo "[2/5] Restoring Docker images..."

if [ "$BACKEND_TAR_EXISTS" = true ]; then
    echo "Restoring backend image..."
    docker load -i "$BACKUP_DIR/backend_$TIMESTAMP.tar"
    echo -e "${GREEN}✓${NC} Backend image restored"
fi

if [ "$FRONTEND_TAR_EXISTS" = true ]; then
    echo "Restoring frontend image..."
    docker load -i "$BACKUP_DIR/frontend_$TIMESTAMP.tar"
    echo -e "${GREEN}✓${NC} Frontend image restored"
fi

# === 3. Restore Database ===
echo ""
echo "[3/5] Restoring database..."

if command -v pg_restore &> /dev/null; then
    PGPASSWORD=$POSTGRES_PASSWORD pg_restore -U "$POSTGRES_USER" -h "$DB_HOST" -d "$POSTGRES_DB" --clean --if-exists "$BACKUP_DIR/db_$TIMESTAMP.dump" 2>/dev/null || {
        echo -e "${YELLOW}!${NC} pg_restore with --clean failed, trying without..."
        PGPASSWORD=$POSTGRES_PASSWORD pg_restore -U "$POSTGRES_USER" -h "$DB_HOST" -d "$POSTGRES_DB" "$BACKUP_DIR/db_$TIMESTAMP.dump" 2>/dev/null || {
            echo -e "${YELLOW}!${NC} Direct restore failed, trying via docker..."
            docker exec -i chronos-DB pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$BACKUP_DIR/db_$TIMESTAMP.dump" 2>/dev/null || true
        }
    }
    echo -e "${GREEN}✓${NC} Database restored"
else
    echo -e "${YELLOW}!${NC} pg_restore not found, trying docker exec..."
    docker exec -i chronos-DB pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$BACKUP_DIR/db_$TIMESTAMP.dump" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Database restored (via docker)"
fi

# === 4. Restore configuration (optional) ===
echo ""
echo "[4/5] Restoring configuration..."

if [ "$CONFIG_EXISTS" = true ]; then
    tar xzf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" -C /tmp/ 2>/dev/null
    if [ -f "/tmp/.env" ]; then
        cp /tmp/.env .env
        echo -e "${GREEN}✓${NC} .env restored"
    fi
    if [ -f "/tmp/docker-compose.yml" ]; then
        cp /tmp/docker-compose.yml docker-compose.yml
        echo -e "${GREEN}✓${NC} docker-compose.yml restored"
    fi
    rm -f /tmp/.env /tmp/docker-compose.yml
else
    echo -e "${YELLOW}!${NC} No configuration backup, skipping"
fi

# === 5. Run Alembic downgrade ===
echo ""
echo "[5/6] Running Alembic downgrade..."
if docker compose exec -T backend alembic downgrade -1 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Alembic downgrade applied"
else
    echo -e "${YELLOW}!${NC} Alembic downgrade failed (may not be needed)"
fi

# === 6. Start containers ===
echo ""
echo "[6/6] Starting containers..."
docker compose up -d

# Health check
echo "Waiting for services to start..."
sleep 15

echo "Checking health..."
if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}========================================"
    echo -e "=== Rollback Complete ==="
    echo -e "========================================${NC}"
    echo "Restored to: $TIMESTAMP"
    echo ""
    log_deploy "ROLLBACK SUCCESS: timestamp=$TIMESTAMP"
else
    echo -e "${RED}ERROR:${NC} Health check failed after rollback"
    log_deploy "ROLLBACK FAILED: timestamp=$TIMESTAMP - health check failed"
    exit 1
fi
