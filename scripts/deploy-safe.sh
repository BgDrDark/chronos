#!/bin/bash
#
# deploy-safe.sh - Safe deployment script for Chronos
# Deploys with health checks, Alembic migrations, and auto-rollback on failure
#
# Safety features:
# - Pre-deploy DB lock (pg_advisory_lock)
# - Backup verification (pg_restore --list)
# - Alembic dry-run (--sql) before actual migration
# - Graceful shutdown (wait for active queries)
# - DB health check after deploy
# - Deploy lock on DB level (pg_advisory_lock)
#

set -e

# === CONFIG ===
BACKUP_DIR="./backups/chronos"
HEALTH_TIMEOUT=120
BUILD_TIMEOUT=600
LOCK_FILE="/tmp/chronos_deploy.lock"
DEPLOY_LOG="$BACKUP_DIR/deploy.log"
VERSION_FILE="VERSION"
DB_LOCK_ID=1234567890
GRACEFUL_SHUTDOWN_TIMEOUT=30

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

enable_maintenance_mode() {
    echo "Enabling maintenance mode (blocking writes)..."
    db_exec "SET default_transaction_read_only = on;" >/dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Maintenance mode enabled"
    log_deploy "MAINTENANCE MODE enabled"
}

disable_maintenance_mode() {
    echo "Disabling maintenance mode..."
    db_exec "SET default_transaction_read_only = off;" >/dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Maintenance mode disabled"
    log_deploy "MAINTENANCE MODE disabled"
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
    
    if [ ! -f "$backup_file" ] || [ ! -s "$backup_file" ]; then
        echo -e "${RED}ERROR:${NC} Backup file is empty or missing"
        return 1
    fi
    
    # Use pg_restore --list to verify backup is valid
    local DB_CONTAINER=$(get_db_container)
    if docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$DB_CONTAINER" pg_restore --list - < "$backup_file" >/dev/null 2>&1; then
        local size=$(du -h "$backup_file" | cut -f1)
        echo -e "${GREEN}✓${NC} Backup verified ($size, valid format)"
        return 0
    else
        echo -e "${RED}ERROR:${NC} Backup verification failed (invalid format)"
        return 1
    fi
}

# === CLEANUP ===
cleanup() {
    rm -f "$LOCK_FILE"
    release_db_lock 2>/dev/null || true
    disable_maintenance_mode 2>/dev/null || true
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
FORCE_BUILD=false
DRY_RUN=false
DEPLOY_VERSION=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_BUILD=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --version)
            DEPLOY_VERSION="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--force] [--dry-run] [--version v3.6.2.0]"
            exit 1
            ;;
    esac
done

# === HEADER ===
echo -e "${BLUE}========================================"
echo -e "=== Chronos Safe Deploy ==="
echo -e "========================================${NC}"
echo "Version: $VERSION"
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

# 2. Disk space (min 1GB free)
DISK_FREE=$(df -m / | awk 'NR==2 {print $4}')
if [ "$DISK_FREE" -lt 1024 ]; then
    echo -e "${RED}ERROR:${NC} Insufficient disk space (${DISK_FREE}MB available, need 1GB+)"
    exit 1
fi
echo -e "${GREEN}✓${NC} Disk space OK (${DISK_FREE}MB free)"

# 3. Git status (warn on uncommitted changes)
if git status --porcelain 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}!${NC} WARNING: Uncommitted changes detected"
    git status --porcelain | head -5
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would deploy with uncommitted changes"
    fi
else
    echo -e "${GREEN}✓${NC} Git working directory is clean"
fi

# 4. .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR:${NC} .env file not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file exists"

# 5. docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR:${NC} docker-compose.yml not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} docker-compose.yml exists"

# 6. Database connectivity
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

# 0. Acquire DB-level deploy lock
echo "[0/9] Acquiring database deploy lock..."
if ! acquire_db_lock; then
    exit 1
fi

# 1. Health check (current version)
echo "[1/9] Checking current health..."
if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Current version is healthy"
else
    echo -e "${YELLOW}!${NC} Current version not responding (may be first deploy)"
fi

# Get timestamp BEFORE backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 2. Create backup with verification
echo ""
echo "[2/9] Creating backup..."
if ./scripts/backup.sh 2>&1; then
    # Find the backup file and verify it
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

# 3. Git fetch + checkout
echo ""
echo "[3/9] Fetching latest code..."

# Configure git credentials if GITHUB_REPO_TOKEN is set
if [ -n "$GITHUB_REPO_TOKEN" ]; then
    git config --global credential.helper '!f() { echo "username=x-access-token"; echo "password=$GITHUB_REPO_TOKEN"; }; f'
    git config --global url."https://x-access-token:${GITHUB_REPO_TOKEN}@github.com/".insteadOf "https://github.com/"
fi

# Fix dubious ownership (container runs as root, project mounted from host)
git config --global --add safe.directory /project

if [ -n "$DEPLOY_VERSION" ]; then
    # Deploy specific version (tag)
    echo "Fetching tags..."
    if git fetch origin --tags; then
        CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        # Try tag with and without 'v' prefix
        if git rev-parse "$DEPLOY_VERSION" >/dev/null 2>&1; then
            git checkout "$DEPLOY_VERSION"
        elif git rev-parse "v$DEPLOY_VERSION" >/dev/null 2>&1; then
            git checkout "v$DEPLOY_VERSION"
        else
            echo -e "${RED}ERROR:${NC} Version tag '$DEPLOY_VERSION' not found"
            log_deploy "DEPLOY ABORTED: version tag '$DEPLOY_VERSION' not found"
            exit 1
        fi
        NEW_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓${NC} Code updated to $DEPLOY_VERSION: $CURRENT_COMMIT → $NEW_COMMIT"
        log_deploy "GIT updated to $DEPLOY_VERSION: $NEW_COMMIT"
    else
        echo -e "${RED}ERROR:${NC} Git fetch tags failed"
        log_deploy "DEPLOY ABORTED: git fetch tags failed"
        exit 1
    fi
else
    # Deploy latest main
    if git fetch origin main; then
        CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        git reset --hard origin/main
        NEW_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓${NC} Code updated: $CURRENT_COMMIT → $NEW_COMMIT"
        log_deploy "GIT updated: $NEW_COMMIT"
    else
        echo -e "${YELLOW}!${NC} Git fetch failed, using local code"
        log_deploy "GIT fetch failed, using local code"
    fi
fi

# 4. Build images
echo ""
echo "[4/9] Building images..."
BUILD_ARGS=""
if [ "$FORCE_BUILD" = true ]; then
    BUILD_ARGS="--no-cache"
    echo "Building without cache (--force)..."
else
    echo "Using build cache (use --force to rebuild)..."
fi

# Build backend with timeout
echo "Building backend..."
START_TIME=$(date +%s)
docker compose build $BUILD_ARGS backend
BUILD_STATUS=$?
ELAPSED=$(( $(date +%s) - START_TIME ))
if [ $BUILD_STATUS -ne 0 ]; then
    echo -e "${RED}ERROR:${NC} Backend build failed"
    log_deploy "DEPLOY ABORTED: backend build failed"
    exit 1
fi
if [ $ELAPSED -ge $BUILD_TIMEOUT ]; then
    echo -e "${RED}ERROR:${NC} Backend build timeout (${BUILD_TIMEOUT}s)"
    log_deploy "DEPLOY ABORTED: backend build timeout"
    exit 1
fi
echo -e "${GREEN}✓${NC} Backend built (${ELAPSED}s)"

# Build frontend with timeout
echo "Building frontend..."
START_TIME=$(date +%s)
docker compose build $BUILD_ARGS frontend
BUILD_STATUS=$?
ELAPSED=$(( $(date +%s) - START_TIME ))
if [ $BUILD_STATUS -ne 0 ]; then
    echo -e "${RED}ERROR:${NC} Frontend build failed"
    log_deploy "DEPLOY ABORTED: frontend build failed"
    exit 1
fi
if [ $ELAPSED -ge $BUILD_TIMEOUT ]; then
    echo -e "${RED}ERROR:${NC} Frontend build timeout (${BUILD_TIMEOUT}s)"
    log_deploy "DEPLOY ABORTED: frontend build timeout"
    exit 1
fi
echo -e "${GREEN}✓${NC} Frontend built (${ELAPSED}s)"

log_deploy "BUILD complete: backend + frontend"

# 5. Alembic dry-run + migration
echo ""
echo "[5/9] Running Alembic migrations..."

# Dry-run first
echo "Running dry-run check..."
if docker compose exec -T backend alembic upgrade head --sql 2>/dev/null | grep -q "BEGIN\|CREATE\|ALTER\|INSERT"; then
    echo -e "${GREEN}✓${NC} Dry-run SQL generated (migrations are valid)"
    log_deploy "ALEMBIC dry-run OK"
else
    echo -e "${YELLOW}!${NC} No migrations needed or dry-run skipped"
fi

# Apply migrations
echo "Applying migrations..."
if docker compose exec -T backend alembic upgrade head 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Alembic migrations applied"
    log_deploy "ALEMBIC migrations applied"
else
    echo -e "${YELLOW}!${NC} Alembic migration failed (may be first run or no changes)"
    log_deploy "ALEMBIC migration failed or not needed"
fi

# 6. Graceful shutdown + Deploy backend
echo ""
echo "[6/9] Deploying backend..."

# Wait for active queries before restart
wait_for_active_queries || echo -e "${YELLOW}!${NC} Proceeding despite active queries"

docker compose up -d --no-deps backend --force-recreate

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

# 7. Deploy frontend
echo ""
echo "[7/9] Deploying frontend..."
docker compose up -d frontend --force-recreate
echo -e "${GREEN}✓${NC} Frontend deployed"

# 8. Restart dependent services
echo ""
echo "[8/9] Restarting dependent services..."
if docker compose ps gateway 2>/dev/null | grep -q "Up"; then
    docker compose restart gateway
    echo -e "${GREEN}✓${NC} Gateway restarted"
else
    echo -e "${YELLOW}!${NC} Gateway not running, skipping"
fi

# 9. Final health check + DB health
echo ""
echo "[9/9] Final health check..."
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
echo "Version: $VERSION"
echo "Deployed at: $(date)"
echo ""

log_deploy "DEPLOY SUCCESS: version=$VERSION timestamp=$TIMESTAMP backend=$BACKEND_OK frontend=$FRONTEND_OK db=$DB_OK"
