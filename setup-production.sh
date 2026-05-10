#!/bin/bash
# =============================================================================
# Chronos Production Setup & Deploy Script
# =============================================================================
# Usage:
#   ./setup-production.sh init [version]       # Phase 1: Initial setup (one-time)
#   ./setup-production.sh deploy vX.Y.Z.W      # Phase 2: Deploy new version
#   ./setup-production.sh status               # Check current status
#   ./setup-production.sh rollback TIMESTAMP   # Rollback to backup
#
# Environment:
#   GITHUB_TOKEN - GitHub PAT for GHCR image pulls (required for deploy)
# =============================================================================

set -e

# --- Configuration ---
REPO_URL="https://github.com/BgDrDark/chronos.git"
INSTALL_DIR="/opt/chronos"
PROD_DOMAIN="chronos.oblak24.org"
BACKUP_DIR="./backups/chronos"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}!${NC} $1"; }
log_error()   { echo -e "${RED}ERROR:${NC} $1"; }

# =============================================================================
# PHASE 1: Initial Setup
# =============================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    if [ ! -f /etc/debian_version ]; then
        log_warn "This script is designed for Debian, but continuing anyway..."
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Install it first:"
        echo "  curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_info "Installing git..."
        apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1
    fi
    
    if ! command -v curl &> /dev/null; then
        log_info "Installing curl..."
        apt-get update -qq && apt-get install -y -qq curl > /dev/null 2>&1
    fi
    
    if ! command -v openssl &> /dev/null; then
        log_info "Installing openssl..."
        apt-get update -qq && apt-get install -y -qq openssl > /dev/null 2>&1
    fi
    
    log_success "All prerequisites met"
}

generate_secrets() {
    log_info "Generating secret keys..."
    
    JWT_SECRET=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
    CSRF_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DEPLOY_API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    DB_PASSWORD=$(openssl rand -hex 16)
    
    log_success "Secrets generated"
}

create_env_file() {
    log_info "Creating .env file..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=chronosdb
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Backend Secrets
JWT_SECRET_KEY=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
CSRF_SECRET_KEY=${CSRF_SECRET}

# Deployment
DEPLOY_API_KEY=${DEPLOY_API_KEY}
DEPLOY_LISTENER_URL=http://host.docker.internal:14241
GITHUB_REPO=${REPO_URL}
GITHUB_REPO_TOKEN=${GITHUB_TOKEN:-}
GITHUB_REPO_API=https://api.github.com/repos/BgDrDark/chronos/releases/latest

# Docker Compose
BACKEND_NAME=chronos-backend
FRONTEND_NAME=chronos-frontend
VERSION=${TARGET_VERSION:-latest}

# Frontend API URL (empty for relative URLs in production)
VITE_API_URL=

# CORS Origins
BACKEND_CORS_ORIGINS=https://${PROD_DOMAIN}

# Kiosk
KIOSK_DEVICE_SECRET=$(openssl rand -hex 16)

# Google Calendar Integration (configure manually after setup)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALENDAR_WEBHOOK_SECRET=
GOOGLE_REDIRECT_URI=https://${PROD_DOMAIN}/auth/google/callback
GOOGLE_SYNC_ENABLED=true

# Deployment Settings
PROJECT_DIR=${INSTALL_DIR}
EOF
    
    log_success ".env file created at ${INSTALL_DIR}/.env"
    log_warn "IMPORTANT: Save these credentials securely!"
    echo ""
    echo -e "  ${YELLOW}DB Password:${NC}      ${DB_PASSWORD}"
    echo -e "  ${YELLOW}Deploy API Key:${NC}   ${DEPLOY_API_KEY}"
    echo -e "  ${YELLOW}JWT Secret:${NC}       ${JWT_SECRET}"
    echo -e "  ${YELLOW}Encryption Key:${NC}   ${ENCRYPTION_KEY}"
    echo ""
}

setup_nginx_proxy() {
    log_info "Setting up Nginx Proxy Manager custom proxy config..."
    
    # Wait for NPM container to be ready
    sleep 10
    
    # Find NPM container dynamically
    local NPM_CONTAINER
    NPM_CONTAINER=$(docker ps --filter "name=nginx-proxy-manager" --format "{{.Names}}" 2>/dev/null | head -1)
    
    if [ -z "$NPM_CONTAINER" ]; then
        log_warn "Nginx Proxy Manager container not found, skipping proxy config"
        log_info "Configure proxy manually via NPM web UI (http://<server-ip>:81)"
        return 0
    fi
    
    log_info "Using NPM container: $NPM_CONTAINER"
    
    # Create custom proxy config directory
    docker exec "$NPM_CONTAINER" mkdir -p /data/nginx/custom 2>/dev/null || true
    
    # Write custom proxy config with ALL backend routes
    docker exec -i "$NPM_CONTAINER" sh -c 'cat > /data/nginx/custom/server_proxy.conf' << 'PROXYEOF'
# === Chronos Backend Proxy Routes ===

location /webhook {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}

location /system {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}

location /terminal {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}

location /export {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
    proxy_read_timeout 300s;
}

location /warehouse {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}

location /notifications {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
}

location /documents {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Scheme $scheme;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://backend:14240;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $http_connection;
    proxy_http_version 1.1;
    client_max_body_size 50M;
}
PROXYEOF
    
    # Test and reload NPM
    if docker exec "$NPM_CONTAINER" nginx -t 2>/dev/null; then
        docker exec "$NPM_CONTAINER" nginx -s reload
        log_success "Nginx Proxy Manager configured and reloaded"
    else
        log_warn "Nginx Proxy Manager config test failed (may need manual setup)"
    fi
}

verify_installation() {
    log_info "Verifying installation..."
    
    sleep 15
    
    # Check containers
    local backend_running=false
    local frontend_running=false
    
    if docker ps --format '{{.Names}}' | grep -q chronos-backend; then
        backend_running=true
        log_success "Backend container running"
    fi
    
    if docker ps --format '{{.Names}}' | grep -q chronos-frontend; then
        frontend_running=true
        log_success "Frontend container running"
    fi
    
    if [ "$backend_running" = false ] || [ "$frontend_running" = false ]; then
        log_error "Some containers are not running"
        docker ps -a --filter "name=chronos" --format "table {{.Names}}\t{{.Status}}"
        return 1
    fi
    
    # Check health endpoint
    local health
    health=$(curl -sk https://${PROD_DOMAIN}/webhook/health 2>/dev/null || echo "failed")
    
    if echo "$health" | grep -q '"status":"ok"'; then
        local version
        version=$(echo "$health" | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "unknown")
        log_success "Application healthy (version: ${version})"
    else
        log_warn "Health check not available yet (SSL may not be configured)"
        log_info "Try: curl -s http://localhost:14240/webhook/health"
    fi
    
    log_success "Installation verified"
}

init_production() {
    TARGET_VERSION="${1:-latest}"
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}=== Chronos Production Setup ===${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_prerequisites
    
    # Clone repo
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_warn "Repository already exists at ${INSTALL_DIR}"
        cd "$INSTALL_DIR"
        git pull origin main
    else
        log_info "Cloning repository to ${INSTALL_DIR}..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    # Generate secrets
    generate_secrets
    
    # Create .env
    create_env_file
    
    # Setup update listener BEFORE deploy (required by update.sh)
    log_info "Setting up update listener..."
    if [ -f "$INSTALL_DIR/scripts/setup-update-listener.sh" ]; then
        bash "$INSTALL_DIR/scripts/setup-update-listener.sh" --no-firewall
        log_success "Update listener configured"
    else
        log_warn "setup-update-listener.sh not found, deploy via UI will not work"
    fi
    
    # Ensure docker-compose.yml has extra_hosts for listener connectivity
    log_info "Checking docker-compose.yml configuration..."
    if ! grep -q "host.docker.internal" "$INSTALL_DIR/docker-compose.yml" 2>/dev/null; then
        log_info "Adding extra_hosts to docker-compose.yml..."
        # Find the backend service's volume mount line and add extra_hosts after it
        sed -i '/- PROJECT_DIR=\/project/a\    extra_hosts:\n      - "host.docker.internal:host-gateway"' \
            "$INSTALL_DIR/docker-compose.yml"
        log_success "extra_hosts added for listener connectivity"
    fi
    
    # Ensure DEPLOY_LISTENER_URL is in .env
    if ! grep -q "^DEPLOY_LISTENER_URL=" "$INSTALL_DIR/.env" 2>/dev/null; then
        echo "DEPLOY_LISTENER_URL=http://host.docker.internal:14241" >> "$INSTALL_DIR/.env"
        log_success "DEPLOY_LISTENER_URL added to .env"
    fi
    
    # Initial deploy
    log_info "Running initial deployment (version: ${TARGET_VERSION})..."
    ./scripts/update.sh --version "${TARGET_VERSION}"
    
    # Setup Nginx Proxy
    setup_nginx_proxy
    
    # Verify
    verify_installation
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}=== Production Setup Complete ===${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Nginx Proxy Manager via web UI (http://<server-ip>:81)"
    echo "     - Add proxy host: ${PROD_DOMAIN} -> frontend:3000"
    echo "     - Enable SSL (Let's Encrypt)"
    echo "     - Force SSL redirect"
    echo "  2. Set GitHub token for image pulls:"
    echo "     echo 'GITHUB_REPO_TOKEN=ghp_xxxx' >> ${INSTALL_DIR}/.env"
    echo "  3. Configure Google Calendar credentials:"
    echo "     nano ${INSTALL_DIR}/.env"
    echo "     # Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    echo "     ./setup-production.sh deploy latest"
    echo "  4. Create your admin user via the web interface"
    echo "  5. Test: https://${PROD_DOMAIN}"
    echo ""
    echo "To deploy updates:"
    echo "  cd ${INSTALL_DIR}"
    echo "  ./setup-production.sh deploy v3.6.XX.0"
    echo ""
}

# =============================================================================
# PHASE 2: Deploy New Version
# =============================================================================

deploy_version() {
    local version="$1"
    
    if [ -z "$version" ]; then
        log_error "Usage: $0 deploy vX.Y.Z.W"
        exit 1
    fi
    
    cd "$INSTALL_DIR" 2>/dev/null || { log_error "Chronos not installed at ${INSTALL_DIR}"; exit 1; }
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}=== Deploying ${version} ===${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Check if update listener is running
    if curl -sf http://localhost:14241/health >/dev/null 2>&1; then
        log_success "Update listener is running"
    else
        log_warn "Update listener not running, setting it up..."
        if [ -f "$INSTALL_DIR/scripts/setup-update-listener.sh" ]; then
            bash "$INSTALL_DIR/scripts/setup-update-listener.sh" --no-firewall
        else
            log_error "setup-update-listener.sh not found. Cannot deploy."
            exit 1
        fi
    fi
    
    # Deploy (update.sh now auto-updates .env)
    ./scripts/update.sh --version "${version}"
    
    # Verify
    verify_installation
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}=== Deploy Complete ===${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Version ${version} is now live at https://${PROD_DOMAIN}"
    echo ""
}

# =============================================================================
# Status Check
# =============================================================================

check_status() {
    cd "$INSTALL_DIR" 2>/dev/null || { log_error "Chronos not installed at ${INSTALL_DIR}"; exit 1; }
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}=== Chronos Status ===${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Current version
    if [ -f .env ]; then
        local version
        version=$(grep "^VERSION=" .env | cut -d= -f2)
        echo -e "  Configured version: ${YELLOW}${version}${NC}"
    fi
    
    # Container status
    echo ""
    echo "  Containers:"
    docker ps --filter "name=chronos" --format "    {{.Names}}: {{.Status}}" 2>/dev/null || echo "    (none running)"
    
    # Health check
    echo ""
    echo "  Health check:"
    local health
    health=$(curl -sk https://${PROD_DOMAIN}/webhook/health 2>/dev/null || echo "unavailable")
    if echo "$health" | grep -q '"status"'; then
        echo "    $health" | python3 -m json.tool 2>/dev/null | sed 's/^/    /' || echo "    $health"
    else
        echo "    unavailable"
    fi
    
    # Database
    echo ""
    echo "  Database:"
    local DB_CONTAINER
    DB_CONTAINER=$(docker ps --filter "name=chronos-DB" --filter "name=chronos-db" --format "{{.Names}}" 2>/dev/null | head -1)
    if [ -n "$DB_CONTAINER" ]; then
        docker exec "$DB_CONTAINER" psql -U postgres -d chronosdb -c "SELECT count(*) as user_count FROM users;" 2>/dev/null | grep -v "^$" | sed 's/^/    /' || echo "    (not available)"
    else
        echo "    (container not found)"
    fi
    
    # Backups
    echo ""
    echo "  Recent backups:"
    ls -lh ${BACKUP_DIR}/ 2>/dev/null | grep -E '\.(dump|tar|gz)$' | tail -5 | sed 's/^/    /' || echo "    (no backups found)"
    
    echo ""
}

# =============================================================================
# Rollback
# =============================================================================

rollback_version() {
    local timestamp="$1"
    
    cd "$INSTALL_DIR" 2>/dev/null || { log_error "Chronos not installed at ${INSTALL_DIR}"; exit 1; }
    
    if [ -z "$timestamp" ]; then
        log_error "Usage: $0 rollback TIMESTAMP"
        echo ""
        echo "Available backups:"
        ls -1 ${BACKUP_DIR}/ 2>/dev/null | grep -E '^[0-9]{8}_[0-9]{6}' | sed 's/^/  /' || echo "  (no backups found)"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}=== Rolling back to ${timestamp} ===${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    
    ./scripts/rollback.sh --timestamp "${timestamp}"
    
    echo ""
    echo -e "${GREEN}Rollback complete${NC}"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

case "${1}" in
    init)
        init_production "$2"
        ;;
    deploy)
        deploy_version "$2"
        ;;
    status)
        check_status
        ;;
    rollback)
        rollback_version "$2"
        ;;
    *)
        echo "Usage: $0 {init|deploy|status|rollback} [version/timestamp]"
        echo ""
        echo "Commands:"
        echo "  init [version]        - Initial production setup (one-time)"
        echo "  deploy vX.Y.Z.W       - Deploy new version"
        echo "  status                - Check current status"
        echo "  rollback TIMESTAMP    - Rollback to backup"
        echo ""
        echo "Examples:"
        echo "  sudo $0 init v3.6.60.0        - Setup production with v3.6.60.0"
        echo "  sudo $0 deploy v3.6.60.0      - Deploy v3.6.60.0"
        echo "  sudo $0 status                - Check status"
        echo "  sudo $0 rollback 20260510_192059  - Rollback to backup"
        ;;
esac
