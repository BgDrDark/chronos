# Chronos - Working Time & HR Management System

## Overview

Chronos is a comprehensive HR and time management platform with modules for shifts, payroll, kiosk terminals, accounting, fleet management, confectionery production, and behavioral analysis.

## Quick Start

```bash
# Start all services
docker compose up -d

# Run database migrations
docker compose exec backend alembic -c /app/backend/alembic.ini upgrade head

# Seed initial modules
docker compose exec backend python -m backend.seed_modules
```

## Deployment

### Automated Setup (Production)

The `setup-update-listener.sh` script automates the entire deploy-listener setup on production servers. The listener runs on the **host machine** and receives update requests from the backend container, executing `update.sh` safely outside Docker.

#### One-Command Setup

```bash
# SSH to your production server
cd /path/to/chronos

# Run the setup script (requires sudo)
sudo bash scripts/setup-update-listener.sh

# Or skip firewall configuration
sudo bash scripts/setup-update-listener.sh --no-firewall

# Or use a custom port
sudo bash scripts/setup-update-listener.sh --port 14241
```

#### What the Script Does

| Step | Description |
|------|-------------|
| 1 | Auto-detects user, project directory, Python3 path, and DEPLOY_API_KEY from `.env` |
| 2 | Checks prerequisites: Python3 ≥ 3.8, Docker CLI, docker group membership |
| 3 | Creates systemd service file at `/etc/systemd/system/chronos-update-listener.service` |
| 4 | Enables and starts the service with auto-restart on failure |
| 5 | Configures firewall rules (UFW, firewalld, or iptables) for port 14241 |
| 6 | Updates `docker-compose.yml` with `DEPLOY_LISTENER_URL` and `extra_hosts` |
| 7 | Updates `.env` with `DEPLOY_LISTENER_URL` if missing |
| 8 | Restarts the backend container and verifies health |

#### Prerequisites

- **Python 3.8+** on the host machine
- **Docker** installed and running
- **Docker Compose** v2+
- User must be in the `docker` group (script adds automatically if needed)
- `sudo` access for systemd and firewall configuration

#### After Setup

```bash
# Check service status
sudo systemctl status chronos-update-listener

# View live logs
sudo journalctl -u chronos-update-listener -f

# Health check
curl http://localhost:14241/health

# Check deploy status
curl http://localhost:14241/deploy-status

# Trigger a deployment
curl -X POST http://localhost:14241/deploy \
  -H "Authorization: DeployKey $(grep DEPLOY_API_KEY .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"version": "v3.6.58.0"}'
```

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  HOST Machine                                            │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ chronos-update-listener (systemd, port 14241)       │ │
│  │ - Runs as host user                                 │ │
│  │ - Executes update.sh safely outside container       │ │
│  │ - Auto-restarts on failure                          │ │
│  └──────────────┬──────────────────────────────────────┘ │
│                 │ HTTP (host.docker.internal:14241)      │
│  ┌──────────────▼──────────────────────────────────────┐ │
│  │ Docker Container (backend)                          │ │
│  │ - POST /webhook/deploy → forwards to listener       │ │
│  │ - DEPLOY_LISTENER_URL env var                       │ │
│  │ - extra_hosts: host.docker.internal:host-gateway    │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  Firewall: port 14241 → localhost + Docker networks only │
└─────────────────────────────────────────────────────────┘
```

#### Manual Setup (Alternative)

If you prefer manual setup, follow these steps:

1. **Create systemd service:**
   ```bash
   sudo tee /etc/systemd/system/chronos-update-listener.service << EOF
   [Unit]
   Description=Chronos Update Listener
   After=network.target docker.service
   Wants=docker.service

   [Service]
   Type=simple
   User=$(whoami)
   Group=$(whoami)
   WorkingDirectory=$(pwd)
   Environment=PYTHONUNBUFFERED=1
   Environment=PROJECT_DIR=$(pwd)
   ExecStart=$(which python3) $(pwd)/scripts/update-listener.py \
       --port 14241 \
       --project-dir $(pwd) \
       --api-key $(grep DEPLOY_API_KEY .env | cut -d= -f2)
   Restart=on-failure
   RestartSec=5
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   EOF
   ```

2. **Enable and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable chronos-update-listener
   sudo systemctl start chronos-update-listener
   ```

3. **Configure firewall:**
   ```bash
   # UFW
   sudo ufw allow from 172.17.0.0/16 to any port 14241 proto tcp
   sudo ufw allow from 127.0.0.1 to any port 14241 proto tcp
   ```

4. **Update docker-compose.yml:**
   Add to backend service:
   ```yaml
   environment:
     - DEPLOY_LISTENER_URL=${DEPLOY_LISTENER_URL:-http://host.docker.internal:14241}
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

5. **Restart backend:**
   ```bash
   docker compose up -d --no-deps backend
   ```

### Safe Deploy Script

The `scripts/update.sh` script handles safe deployments with:

- Pre-deploy database lock (`pg_advisory_lock`)
- Backup verification (DB + Docker images + config)
- Alembic dry-run before migration
- Graceful shutdown (waits for active queries)
- Health checks after each step
- Auto-rollback on failure

```bash
# Deploy latest version
./scripts/update.sh

# Deploy specific version
./scripts/update.sh --version v3.6.58.0

# Dry run (no changes)
./scripts/update.sh --dry-run
```

### Rollback

```bash
# Rollback to last backup
./scripts/rollback.sh
```

## Modules

| Module | Code | Description |
|--------|------|-------------|
| Shifts | `shifts` | Work schedules, attendance, late tracking |
| Payroll | `salaries` | Salary calculation, payslips, deductions |
| Kiosk | `kiosk` | Terminal interface, QR access, GPS check |
| Integrations | `integrations` | External system sync, API access |
| Confectionery | `confectionery` | Warehouse (FEFO), recipes, production stations |
| Accounting | `accounting` | Invoices, suppliers, payments, SAF-T |
| Notifications | `notifications` | SMTP settings, email reports, auto-alerts |
| Fleet | `fleet` | Vehicle management, fuel, trips, maintenance |
| Cost Centers | `cost_centers` | Department cost tracking |
| Inventory | `inventory` | Stock management, production tasks |
| Behavioral Analysis | `behavioral_analysis` | 4-layer behavioral analysis with dynamic rules, XAI, bias detection |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `chronosdb` | Database name |
| `JWT_SECRET_KEY` | auto-generated | JWT signing key |
| `ENCRYPTION_KEY` | auto-generated | Fernet encryption key |
| `CSRF_SECRET_KEY` | auto-generated | CSRF protection key |
| `DEPLOY_API_KEY` | auto-generated | Deploy authentication key |
| `DEPLOY_LISTENER_URL` | `http://host.docker.internal:14241` | Update listener URL |
| `VERSION` | `unknown` | Application version |
| `BACKEND_CORS_ORIGINS` | `[]` | Allowed CORS origins |

## Versioning

Releases follow the `vMAJOR.MINOR.PATCH.BUILD` format. Each release is tagged and published on GitHub.

```bash
# Create a new release
git tag -a v3.6.59.0 -m "Release v3.6.59.0 - Description"
git push origin v3.6.59.0
```

## License

Private - All rights reserved.
