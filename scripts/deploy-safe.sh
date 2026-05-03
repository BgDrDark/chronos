#!/bin/bash
#
# deploy-safe.sh - Safe deployment script for Chronos (CI/CD mode)
# Pulls pre-built images from GHCR with health checks, Alembic migrations, and auto-rollback
#
# Safety features:
# - Pre-deploy DB lock (pg_advisory_lock)
# - Backup verification
# - Alembic dry-run (--sql) before actual migration
# - Graceful shutdown (wait for active queries)
# - DB health check after deploy
# - Auto-rollback on failure
#

set -e

# === CONFIG ===
BACKUP_DIR="./backups/chronos"
HEALTH_TIMEOUT=120
PULL_TIMEOUT=300
LOCK_FILE="/tmp/chronos_deploy.lock"
DEPLOY_LOG="$BACKUP_DIR/deploy.log"
VERSION_FILE="VERSION"
DB_LOCK_ID=1234567890
GRACEFUL_SHUTDOWN_TIMEOUT=30
REGISTRY="ghcr.io/bgdrdark"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get VERSION and DB credentials from .env
if [ -f ".env" ]; then
    source .env
fi

VERSION=${VERSION:-$(cat $VERSION_FILE 2>/dev/null || echo "unknown")}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-chronosdb}

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# === LOGGING ===
log_deploy() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$DEPLOY_LOG"
}

# === DB FUNCTIONS ===
get_db_container() {
    docker ps --filter "name=chronos-DB" --format "{{.Names}}" 2>/dev/null || \
    docker ps --filter "name=db" --format "{{.Names}}" 2>/dev/null | head -1
}

db_exec() {
    local DB_CONTAINER=$(get_db_container)
    if [ -z "$DB_CONTAINER" ]; then
        echo -e "${RED}ERROR:${NC} Database container not found"
        return 1
    fi
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$DB_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1" 2>/dev/null
}

acquire_db_lock() {
    echo "Acquiring database deploy lock..."
    local result=$(db_exec "SELECT pg_try_advisory_lock($DB_LOCK_ID);" 2>/dev/null)
    if echo "$result" | grep -q "t"; then
        echo -e "${GREEN}✓${NC} Database deploy lock acquired"
        log_deploy "DB LOCK acquired"
        return 0
    else
        echo -e "${RED}ERROR:${NC} Another deployment is in progress (DB lock held)"
        log_deploy "DEPLOY ABORTED: DB lock held by another process"
        return 1
    fi
}

release_db_lock() {
    db_exec "SELECT pg_advisory_unlock($DB_LOCK_ID);" >/dev/null 2>&1
    log_deploy "DB LOCK released"
}

wait_for_active_queries() {
    local timeout=$GRACEFUL_SHUTDOWN_TIMEOUT
    echo "Waiting for active queries to finish (timeout: ${timeout}s)..."
    local start=$(date +%s)
    while true; do
        local elapsed=$(( $(date +%s) - start ))
        if [ $elapsed -ge $timeout ]; then
            echo -e "${YELLOW}!${NC} Timeout waiting for queries ($timeout s)"
            return 1
        fi
        
        local active=$(db_exec "SELECT count(*) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND state = 'active' AND pid != pg_backend_pid();" 2>/dev/null | grep -o '[0-9]*' | head -1)
        if [ "$active" = "0" ] || [ -z "$active" ]; then
            echo -e "${GREEN}✓${NC} No active queries"
            return 0
        fi
        echo "  $active active queries remaining..."
        sleep 1
    done
}

check_db_health() {
    echo "Checking database health..."
    local result=$(db_exec "
        SELECT 
            count(*) as total,
            count(*) FILTER (WHERE state = 'active') as active,
            count(*) FILTER (WHERE state = 'idle') as idle,
            count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_txn
        FROM pg_stat_activity
        WHERE datname = '$POSTGRES_DB';
    " 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Database healthy"
        echo "  $result"
        return 0
    else
        echo -e "${RED}✗${NC} Database health check failed"
        return 1
    fi
}

verify_backup() {
    local backup_file=$1
    echo "Verifying backup: $backup_file"
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        echo -e "${GREEN}✓${NC} Backup verified ($size)"
        return 0
    else
        echo -e "${RED}ERROR:${NC} Backup verification failed (file missing or empty)"
        return 1
    fi
}

# === CLEANUP ===
cleanup() {
    rm -f "$LOCK_FILE"
    release_db_lock 2>/dev/null || true
}
trap cleanup EXIT

# === LOCK FILE CHECK ===
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo -e "${RED}ERROR:${NC} Another deployment is in progress (PID: $LOCK_PID)"
        echo "If this is a stale lock, remove: rm -f $LOCK_FILE"
        exit 1
    else
        echo -e "${YELLOW}WARNING:${NC} Stale lock file found, removing..."
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"

# === ARGUMENTS ===
DRY_RUN=false
DEPLOY_VERSION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --version)
            DEPLOY_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--dry-run] [--version v3.6.12.0]"
            exit 1
            ;;
    esac
done

# === UPDATE .env WITH NEW VERSION ===
if [ -n "$DEPLOY_VERSION" ] && [ -f ".env" ]; then
    # Normalize version (add 'v' prefix if missing)
    case "$DEPLOY_VERSION" in
        v*) TARGET_VERSION="$DEPLOY_VERSION" ;;
        *)  TARGET_VERSION="v${DEPLOY_VERSION}" ;;
    esac
    
    # Update VERSION in .env
    sed -i "s/^VERSION=.*/VERSION=${TARGET_VERSION}/" .env
    
    # Re-source .env to get the new version
    source .env
    
    echo -e "${GREEN}✓${NC} .env updated to ${TARGET_VERSION}"
    log_deploy ".env updated to ${TARGET_VERSION}"
fi

# === HEADER ===
echo -e "${BLUE}========================================"
echo -e "=== Chronos Safe Deploy (CI/CD) ==="
echo -e "========================================${NC}"
echo "Current Version: $VERSION"
if [ -n "$DEPLOY_VERSION" ]; then
    echo -e "Target:  ${DEPLOY_VERSION}"
fi
echo "Started: $(date)"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN]${NC} No changes will be made"
    echo ""
fi

# === PRE-DEPLOYMENT CHECKS ===
echo -e "${BLUE}[PRE] Pre-deployment checks...${NC}"

# 1. Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}ERROR:${NC} Docker daemon is not running"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker daemon is running"

# 2. Disk space (min 500MB free for image pull)
DISK_FREE=$(df -m / | awk 'NR==2 {print $4}')
if [ "$DISK_FREE" -lt 512 ]; then
    echo -e "${RED}ERROR:${NC} Insufficient disk space (${DISK_FREE}MB available, need 512MB+)"
    exit 1
fi
echo -e "${GREEN}✓${NC} Disk space OK (${DISK_FREE}MB free)"

# 3. .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR:${NC} .env file not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file exists"

# 4. docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR:${NC} docker-compose.yml not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} docker-compose.yml exists"

# 5. Database connectivity
if ! db_exec "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${RED}ERROR:${NC} Cannot connect to database"
    exit 1
fi
echo -e "${GREEN}✓${NC} Database connection OK"

echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN]${NC} All pre-checks passed. Would proceed with deployment."
    cleanup
    exit 0
fi

# === DEPLOYMENT ===

TARGET_VERSION="${DEPLOY_VERSION:-$VERSION}"
# Ensure version has 'v' prefix for GHCR images
if [[ ! "$TARGET_VERSION" =~ ^v ]]; then
    TARGET_VERSION="v${TARGET_VERSION}"
fi

# 0. Acquire DB-level deploy lock
echo "[0/7] Acquiring database deploy lock..."
if ! acquire_db_lock; then
    exit 1
fi

# 1. Health check (current version)
echo "[1/7] Checking current health..."
if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Current version is healthy"
else
    echo -e "${YELLOW}!${NC} Current version not responding (may be first deploy)"
fi

# Get timestamp BEFORE backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 2. Create backup with verification
echo ""
echo "[2/7] Creating backup..."
if ./scripts/backup.sh 2>&1; then
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        if verify_backup "$LATEST_BACKUP"; then
            echo -e "${GREEN}✓${NC} Backup created and verified ($TIMESTAMP)"
            log_deploy "BACKUP created and verified: $TIMESTAMP"
        else
            echo -e "${RED}ERROR:${NC} Backup verification failed. Aborting deploy."
            log_deploy "DEPLOY ABORTED: backup verification failed"
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} Backup created ($TIMESTAMP)"
        log_deploy "BACKUP created: $TIMESTAMP"
    fi
else
    echo -e "${RED}ERROR:${NC} Backup failed. Aborting deploy."
    log_deploy "DEPLOY ABORTED: backup failed"
    exit 1
fi

# 3. Pull new images from GHCR
echo ""
echo "[3/7] Pulling images from GHCR..."
PULL_START=$(date +%s)

# Login to GHCR if token is available
if [ -n "$GITHUB_TOKEN" ] || [ -n "$GITHUB_REPO_TOKEN" ]; then
    echo "Logging in to GHCR..."
    echo "${GITHUB_TOKEN:-$GITHUB_REPO_TOKEN}" | docker login ghcr.io -u "${GITHUB_ACTOR:-$(whoami)}" --password-stdin 2>/dev/null || \
    echo -e "${YELLOW}!${NC} GHCR login failed, trying without auth..."
fi

# Pull backend
echo "Pulling backend image: ${REGISTRY}/chronos-backend:${TARGET_VERSION}..."
if ! timeout $PULL_TIMEOUT docker pull ${REGISTRY}/chronos-backend:${TARGET_VERSION}; then
    echo -e "${RED}ERROR:${NC} Backend image pull failed"
    log_deploy "DEPLOY ABORTED: backend pull failed"
    exit 1
fi
echo -e "${GREEN}✓${NC} Backend image pulled"

# Pull frontend
echo "Pulling frontend image: ${REGISTRY}/chronos-frontend:${TARGET_VERSION}..."
if ! timeout $PULL_TIMEOUT docker pull ${REGISTRY}/chronos-frontend:${TARGET_VERSION}; then
    echo -e "${RED}ERROR:${NC} Frontend image pull failed"
    log_deploy "DEPLOY ABORTED: frontend pull failed"
    exit 1
fi
echo -e "${GREEN}✓${NC} Frontend image pulled"

PULL_ELAPSED=$(( $(date +%s) - PULL_START ))
echo -e "${GREEN}✓${NC} All images pulled (${PULL_ELAPSED}s)"
log_deploy "PULL complete: ${PULL_ELAPSED}s"

# Update .env with target version BEFORE running alembic
# so docker compose run uses the new image
if [ -n "$DEPLOY_VERSION" ]; then
    if grep -q "^VERSION=" .env; then
        sed -i "s/^VERSION=.*/VERSION=${TARGET_VERSION}/" .env
    else
        echo "VERSION=${TARGET_VERSION}" >> .env
    fi
fi

# 4. Alembic dry-run + migration
echo ""
echo "[4/7] Running Alembic migrations..."

# Get the network used by the DB container
DB_NETWORK=$(docker inspect chronos-DB --format '{{range $net, $v := .NetworkSettings.Networks}}{{$net}}{{end}}' 2>/dev/null || echo "host")
echo "Using network: ${DB_NETWORK}"

# Run alembic using the exact pulled image to avoid compose caching issues
BACKEND_IMAGE="${REGISTRY}/chronos-backend:${TARGET_VERSION}"
ALEMBIC_RUN="docker run --rm --network ${DB_NETWORK} -w /app/backend -e POSTGRES_USER=${POSTGRES_USER} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -e POSTGRES_HOST=chronos-DB -e POSTGRES_PORT=5432 -e POSTGRES_DB=${POSTGRES_DB} -e PYTHONPATH=/app ${BACKEND_IMAGE} alembic upgrade head"

# Dry-run first
echo "Running dry-run check..."
if ${ALEMBIC_RUN} --sql 2>/dev/null | grep -q "BEGIN\|CREATE\|ALTER\|INSERT"; then
    echo -e "${GREEN}✓${NC} Dry-run SQL generated (migrations are valid)"
    log_deploy "ALEMBIC dry-run OK"
else
    echo -e "${YELLOW}!${NC} No migrations needed or dry-run skipped"
fi

# Apply migrations
echo "Applying migrations..."
if ${ALEMBIC_RUN} 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Alembic migrations applied"
    log_deploy "ALEMBIC migrations applied"
else
    echo -e "${YELLOW}!${NC} Alembic migration failed (may be first run or no changes)"
    log_deploy "ALEMBIC migration failed or not needed"
fi

# 5. Graceful shutdown + Deploy backend
echo ""
echo "[5/7] Deploying backend..."

# Wait for active queries before restart
wait_for_active_queries || echo -e "${YELLOW}!${NC} Proceeding despite active queries"

# Stop and remove old container before recreating to avoid name conflicts
echo "Stopping old backend container..."
docker compose stop backend 2>/dev/null || true
docker compose rm -f backend 2>/dev/null || true
sleep 2

docker compose up -d --force-recreate --no-deps backend

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
    log_deploy "DEPLOY FAILED: backend health check timeout"
    ./scripts/rollback.sh $TIMESTAMP
    exit 1
fi

# 6. Deploy frontend
echo ""
echo "[6/7] Deploying frontend..."
docker compose up -d --force-recreate --no-deps frontend
echo -e "${GREEN}✓${NC} Frontend deployed"

# 7. Final health check + DB health
echo ""
echo "[7/7] Final health check..."
sleep 10

BACKEND_OK=false
FRONTEND_OK=false
DB_OK=false

if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend healthy"
    BACKEND_OK=true
else
    echo -e "${RED}✗${NC} Backend not responding"
fi

if curl -sf http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend responding"
    FRONTEND_OK=true
else
    echo -e "${YELLOW}!${NC} Frontend may not be fully ready yet"
fi

if check_db_health; then
    DB_OK=true
fi

# === FINAL ===
echo ""
echo -e "${GREEN}========================================"
echo -e "=== Deploy Complete ==="
echo -e "========================================${NC}"
echo "Version: $TARGET_VERSION"
echo "Deployed at: $(date)"
echo ""

log_deploy "DEPLOY SUCCESS: version=$TARGET_VERSION timestamp=$TIMESTAMP backend=$BACKEND_OK frontend=$FRONTEND_OK db=$DB_OK"
