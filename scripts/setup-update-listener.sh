#!/bin/bash
#
# setup-update-listener.sh - Automated setup for Chronos Update Listener
#
# Usage:
#   sudo bash scripts/setup-update-listener.sh [--no-firewall] [--port 14241]
#
# This script:
#   1. Auto-detects user, project dir, Python, API key
#   2. Checks prerequisites (Python3, docker, docker group)
#   3. Creates and enables systemd service
#   4. Configures firewall (optional)
#   5. Updates docker-compose.yml + .env if needed
#   6. Restarts backend container
#   7. Verifies everything works
#

set -e

# === COLORS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# === ARGS ===
NO_FIREWALL=false
LISTENER_PORT=14241
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-firewall)
            NO_FIREWALL=true
            shift
            ;;
        --port)
            LISTENER_PORT="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--no-firewall] [--port 14241]"
            exit 1
            ;;
    esac
done

# === HEADER ===
echo -e "${BLUE}========================================"
echo -e "=== Chronos Deploy Listener Setup ==="
echo -e "========================================${NC}"
echo ""

# === AUTO-DETECT ===
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CURRENT_USER=$(whoami)
PYTHON_BIN=$(which python3 2>/dev/null || echo "")
ENV_FILE="$PROJECT_DIR/.env"
SERVICE_NAME="chronos-update-listener"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_FILE="/var/log/${SERVICE_NAME}.log"

echo -e "${BLUE}[1/8] Auto-detection...${NC}"

# Read DEPLOY_API_KEY from .env
if [ -f "$ENV_FILE" ]; then
    DEPLOY_API_KEY=$(grep "^DEPLOY_API_KEY=" "$ENV_FILE" | head -1 | cut -d= -f2-)
    if [ -n "$DEPLOY_API_KEY" ]; then
        echo -e "${GREEN}✓${NC} DEPLOY_API_KEY found in .env"
    else
        echo -e "${RED}ERROR:${NC} DEPLOY_API_KEY is empty in .env"
        echo "Generate one: python3 -c \"import secrets; print(secrets.token_hex(32))\""
        exit 1
    fi
else
    echo -e "${RED}ERROR:${NC} .env file not found at $ENV_FILE"
    exit 1
fi

echo "  Project dir: $PROJECT_DIR"
echo "  User:        $CURRENT_USER"
echo "  Python3:     $PYTHON_BIN"
echo "  Port:        $LISTENER_PORT"
echo "  Log file:    $LOG_FILE"
echo ""

# === PREREQUISITES ===
echo -e "${BLUE}[2/8] Checking prerequisites...${NC}"

# Python3
if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
    echo -e "${RED}ERROR:${NC} Python3 not found. Install it first."
    exit 1
fi
echo -e "${GREEN}✓${NC} Python3: $($PYTHON_BIN --version 2>&1)"

# Docker
if ! command -v docker &>/dev/null; then
    echo -e "${RED}ERROR:${NC} docker CLI not found. Install Docker first."
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker: $(docker --version)"

# Docker group
if ! groups "$CURRENT_USER" 2>/dev/null | grep -q "docker"; then
    echo -e "${YELLOW}!${NC} User '$CURRENT_USER' is not in the 'docker' group."
    echo "Adding to docker group..."
    sudo usermod -aG docker "$CURRENT_USER"
    echo -e "${GREEN}✓${NC} Added '$CURRENT_USER' to docker group"
    echo -e "${YELLOW}!${NC} You may need to log out and back in for this to take effect"
else
    echo -e "${GREEN}✓${NC} User '$CURRENT_USER' is in docker group"
fi

# .env file
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR:${NC} .env file not found at $ENV_FILE"
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file exists"

# docker-compose.yml
if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    echo -e "${RED}ERROR:${NC} docker-compose.yml not found at $PROJECT_DIR"
    exit 1
fi
echo -e "${GREEN}✓${NC} docker-compose.yml exists"

# update.sh
if [ ! -x "$PROJECT_DIR/scripts/update.sh" ]; then
    echo -e "${YELLOW}!${NC} update.sh not executable, fixing..."
    chmod +x "$PROJECT_DIR/scripts/update.sh"
fi
echo -e "${GREEN}✓${NC} update.sh is executable"

echo ""

# === SYSTEMD SERVICE ===
echo -e "${BLUE}[3/8] Creating systemd service...${NC}"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Chronos Deploy Listener
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
Environment=PROJECT_DIR=$PROJECT_DIR
ExecStart=$PYTHON_BIN $PROJECT_DIR/scripts/update-listener.py \\
    --port $LISTENER_PORT \\
    --project-dir $PROJECT_DIR \\
    --api-key $DEPLOY_API_KEY
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} Service file created at $SERVICE_FILE"
echo ""

# === ENABLE & START ===
echo -e "${BLUE}[4/8] Enabling and starting service...${NC}"

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sleep 2

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓${NC} Service is running"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -15
else
    echo -e "${RED}ERROR:${NC} Service failed to start"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -n 20
    exit 1
fi

echo ""

# === FIREWALL ===
if [ "$NO_FIREWALL" = false ]; then
    echo -e "${BLUE}[5/8] Configuring firewall...${NC}"

    FIREWALL_CONFIGURED=false

    # Try UFW first
    if command -v ufw &>/dev/null; then
        echo "Detected UFW firewall..."
        # Allow from Docker networks and localhost
        sudo ufw allow from 172.17.0.0/16 to any port $LISTENER_PORT proto tcp 2>/dev/null || true
        sudo ufw allow from 127.0.0.1 to any port $LISTENER_PORT proto tcp 2>/dev/null || true
        FIREWALL_CONFIGURED=true
        echo -e "${GREEN}✓${NC} UFW rules added for port $LISTENER_PORT"
    fi

    # Try firewalld
    if command -v firewall-cmd &>/dev/null; then
        echo "Detected firewalld..."
        sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='172.17.0.0/16' port port='$LISTENER_PORT' protocol='tcp' accept" 2>/dev/null || true
        sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='127.0.0.1' port port='$LISTENER_PORT' protocol='tcp' accept" 2>/dev/null || true
        sudo firewall-cmd --reload 2>/dev/null || true
        FIREWALL_CONFIGURED=true
        echo -e "${GREEN}✓${NC} firewalld rules added for port $LISTENER_PORT"
    fi

    # Try iptables (fallback)
    if [ "$FIREWALL_CONFIGURED" = false ]; then
        echo "No firewall manager detected, using iptables..."
        # Only add if rule doesn't already exist
        if ! sudo iptables -C INPUT -p tcp --dport $LISTENER_PORT -s 172.17.0.0/16 -j ACCEPT 2>/dev/null; then
            sudo iptables -A INPUT -p tcp --dport $LISTENER_PORT -s 172.17.0.0/16 -j ACCEPT 2>/dev/null || true
            sudo iptables -A INPUT -p tcp --dport $LISTENER_PORT -s 127.0.0.1 -j ACCEPT 2>/dev/null || true
            echo -e "${GREEN}✓${NC} iptables rules added for port $LISTENER_PORT"
            echo -e "${YELLOW}!${NC} Remember to save iptables rules: sudo iptables-save > /etc/iptables.rules"
        else
            echo -e "${GREEN}✓${NC} iptables rules already exist"
        fi
    fi
else
    echo -e "${YELLOW}[5/8] Firewall configuration skipped (--no-firewall)${NC}"
    echo -e "${YELLOW}!${NC} Make sure port $LISTENER_PORT is accessible from Docker containers"
fi

echo ""

# === UPDATE docker-compose.yml ===
echo -e "${BLUE}[6/8] Checking docker-compose.yml...${NC}"

# Check if DEPLOY_LISTENER_URL env var exists
if ! grep -q "DEPLOY_LISTENER_URL" "$PROJECT_DIR/docker-compose.yml"; then
    echo "Adding DEPLOY_LISTENER_URL env var..."
    sed -i "/DEPLOY_API_KEY=\${DEPLOY_API_KEY}/a\\      - DEPLOY_LISTENER_URL=\${DEPLOY_LISTENER_URL:-http://host.docker.internal:$LISTENER_PORT}" \
        "$PROJECT_DIR/docker-compose.yml"
    echo -e "${GREEN}✓${NC} DEPLOY_LISTENER_URL added to docker-compose.yml"
else
    echo -e "${GREEN}✓${NC} DEPLOY_LISTENER_URL already exists in docker-compose.yml"
fi

# Check if extra_hosts exists for backend service
if ! grep -q "host.docker.internal" "$PROJECT_DIR/docker-compose.yml"; then
    echo "Adding extra_hosts for host.docker.internal..."
    # Find the line with PROJECT_DIR=/project under backend service and add extra_hosts after the ports section
    sed -i "/- PROJECT_DIR=\/project/a\\    extra_hosts:\n      - \"host.docker.internal:host-gateway\"" \
        "$PROJECT_DIR/docker-compose.yml"
    echo -e "${GREEN}✓${NC} extra_hosts added to docker-compose.yml"
else
    echo -e "${GREEN}✓${NC} extra_hosts already exists in docker-compose.yml"
fi

echo ""

# === UPDATE .env ===
echo -e "${BLUE}[7/8] Checking .env...${NC}"

if ! grep -q "^DEPLOY_LISTENER_URL=" "$ENV_FILE"; then
    echo "Adding DEPLOY_LISTENER_URL to .env..."
    echo "DEPLOY_LISTENER_URL=http://host.docker.internal:$LISTENER_PORT" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} DEPLOY_LISTENER_URL added to .env"
else
    echo -e "${GREEN}✓${NC} DEPLOY_LISTENER_URL already exists in .env"
fi

echo ""

# === RESTART BACKEND ===
echo -e "${BLUE}[8/8] Restarting backend container...${NC}"

cd "$PROJECT_DIR"
docker compose up -d --no-deps backend

echo "Waiting for backend to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend healthy after ${i}s"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}!${NC} Backend health check timed out (may still be starting)"
    fi
    sleep 1
done

echo ""

# === VERIFICATION ===
echo -e "${BLUE}=== Verification ===${NC}"

# Listener health
echo -n "  Deploy listener health: "
LISTENER_HEALTH=$(curl -sf http://localhost:$LISTENER_PORT/health 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $LISTENER_HEALTH"
else
    echo -e "${RED}✗${NC} Failed to reach listener"
fi

# Backend health
echo -n "  Backend health: "
BACKEND_HEALTH=$(curl -sf http://localhost:14240/webhook/health 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $BACKEND_HEALTH"
else
    echo -e "${RED}✗${NC} Failed to reach backend"
fi

# Backend can reach listener
echo -n "  Backend → listener connectivity: "
BACKEND_TO_LISTENER=$(docker compose exec -T backend curl -sf http://host.docker.internal:$LISTENER_PORT/health 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $BACKEND_TO_LISTENER"
else
    echo -e "${RED}✗${NC} Backend cannot reach listener"
    echo -e "${YELLOW}!${NC} Check extra_hosts and firewall rules"
fi

echo ""

# === SUMMARY ===
echo -e "${GREEN}========================================"
echo -e "=== Setup Complete ==="
echo -e "========================================${NC}"
echo ""
echo "Service:     sudo systemctl status $SERVICE_NAME"
echo "Logs:        sudo journalctl -u $SERVICE_NAME -f"
echo "Health:      curl http://localhost:$LISTENER_PORT/health"
echo "Status:      curl http://localhost:$LISTENER_PORT/deploy-status"
echo ""
echo "To trigger a deploy:"
echo "  curl -X POST http://localhost:$LISTENER_PORT/deploy \\"
echo "    -H \"Authorization: DeployKey $DEPLOY_API_KEY\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"version\": \"v3.6.58.0\"}'"
echo ""
