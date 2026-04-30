# Safe Update План

## Общ Преглед

Тази система осигурява сигурен и автоматичен deployment с rollback защита за Chronos приложението.

```
┌─────────────────────────────────────────────────────┐
│            Safe Update Архитектура                    │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┬───────────────┐
         │               │               │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Backup  │    │  Deploy │    │ Rollback│
    │ .sh    │    │-safe.sh │    │  .sh   │
    └─────────┘    └─────────┘    └─────────┘
         │               │               │
         ▼               ▼               ▼
   /backups/       Health         /backups/
   chronos/      Check         chronos/
```

## Компоненти

### 1. scripts/backup.sh

```bash
#!/bin/bash
set -e
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/chronos"

mkdir -p $BACKUP_DIR

# Пази последните 3 backup-а
ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | tail -n +4 | xargs -r rm
ls -t $BACKUP_DIR/backend_*.tar 2>/dev/null | tail -n +4 | xargs -r rm
ls -t $BACKUP_DIR/frontend_*.tar 2>/dev/null | tail -n +4 | xargs -r rm

# DB Backup (compressed)
echo "Creating DB backup..."
pg_dump -U postgres -Fc chronosdb -f $BACKUP_DIR/db_$TIMESTAMP.dump

# Docker Images Backup
echo "Creating image backups..."
BACKEND_IMAGE=$(docker compose images -q backend 2>/dev/null || echo "chronos-backend")
FRONTEND_IMAGE=$(docker compose images -q frontend 2>/dev/null || echo "chronos-frontend")

if [ -n "$BACKEND_IMAGE" ]; then
    docker save $BACKEND_IMAGE -o $BACKUP_DIR/backend_$TIMESTAMP.tar
fi

if [ -n "$FRONTEND_IMAGE" ]; then
    docker save $FRONTEND_IMAGE -o $BACKUP_DIR/frontend_$TIMESTAMP.tar
fi

echo "Backup complete: $TIMESTAMP"
echo "  DB: $BACKUP_DIR/db_$TIMESTAMP.dump"
echo "  Backend: $BACKUP_DIR/backend_$TIMESTAMP.tar"
echo "  Frontend: $BACKUP_DIR/frontend_$TIMESTAMP.tar"
```

### 2. scripts/deploy-safe.sh

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/chronos"
VERSION=$(grep VERSION .env | cut -d= -f2 || echo "unknown")
HEALTH_TIMEOUT=60

echo "=== Chronos Safe Deploy v$VERSION ==="
echo "Started: $(date)"

# 1. Health check (current version)
echo "[1/6] Checking current health..."
if ! curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo "ERROR: Current version is not healthy. Aborting deploy."
    exit 1
fi
echo "✓ Current version is healthy"

# 2. Create backup
echo "[2/6] Creating backup..."
./scripts/backup.sh >/dev/null 2>&1
echo "✓ Backup created"

# 3. Git pull
echo "[3/6] Fetching latest code..."
git fetch origin main
git reset --hard origin/main
echo "✓ Code updated"

# 4. Build images
echo "[4/6] Building images..."
docker compose build --no-cache backend
docker compose build --no-cache frontend
echo "✓ Images built"

# 5. Deploy backend + health check
echo "[5/6] Deploying backend..."
docker compose up -d backend

echo "Waiting for backend health..."
for i in $(seq 1 $HEALTH_TIMEOUT); do
    if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
        echo "✓ Backend healthy after ${i}s"
        break
    fi
    if [ $i -eq $HEALTH_TIMEOUT ]; then
        echo "ERROR: Backend health check timeout. Rolling back..."
        ./scripts/rollback.sh $TIMESTAMP
        exit 1
    fi
    sleep 1
done

# 6. Deploy frontend
echo "[6/6] Deploying frontend..."
docker compose up -d frontend

# Final check
sleep 5
if curl -sf http://localhost:3000 >/dev/null 2>&1; then
    echo "=== Deploy complete ==="
    echo "Version: $VERSION"
    echo "Timestamp: $(date)"
else
    echo "WARNING: Frontend may not be fully ready"
fi
```

### 3. scripts/rollback.sh

```bash
#!/bin/bash
set -e

TIMESTAMP=${1:-""}
BACKUP_DIR="/backups/chronos"

if [ -z "$TIMESTAMP" ]; then
    # Намери най-новия backup
    TIMESTAMP=$(ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | head -1 | xargs basename | sed 's/db_//;s/.dump//')
fi

if [ -z "$TIMESTAMP" ]; then
    echo "ERROR: No backup found"
    exit 1
fi

echo "=== Rolling back to $TIMESTAMP ==="

# Restore Docker images
if [ -f "$BACKUP_DIR/backend_$TIMESTAMP.tar" ]; then
    echo "Restoring backend..."
    docker load -i $BACKUP_DIR/backend_$TIMESTAMP.tar
fi

if [ -f "$BACKUP_DIR/frontend_$TIMESTAMP.tar" ]; then
    echo "Restoring frontend..."
    docker load -i $BACKUP_DIR/frontend_$TIMESTAMP.tar
fi

# Restart containers
echo "Restarting containers..."
docker compose down
docker compose up -d

# Health check
sleep 10
if curl -sf http://localhost:14240/webhook/health >/dev/null 2>&1; then
    echo "=== Rollback complete ==="
else
    echo "ERROR: Rollback failed - health check failed"
    exit 1
fi
```

## Конфигурация

### .env

```bash
# Deployment
VERSION=3.6.1.0
GITHUB_REPO=https://github.com/BgDrDark/chronos

# Backup
BACKUP_DIR=/backups/chronos
MAX_BACKUPS=3
```

### frontend/.env

```bash
VITE_API_URL=/
VITE_GITHUB_REPO=BgDrDark/chronos
```

## Frontend Компоненти

### SettingsPage.tsx - DeploymentSection

```
┌────────────────────────────────────────┐
│  ⚙️ Системни Настройки                 │
│                                        │
│  GitHub repository: BgDrDark/chronos    │
│                                        │
│  Текуща версия: 3.6.1.0    [Провери]  │
│                                        │
│  ┌──────────────────────────────┐      │
│  │    [Обнови Продукцията]      │      │
│  └──────────────────────────────┘      │
│                                        │
│  Последен update: 30.04.2026 10:00     │
└────────────────────────────────────────┘
```

### Check for Update логика

```typescript
const checkForUpdate = async () => {
  const REPO = import.meta.env.VITE_GITHUB_REPO;
  
  // GitHub API - latest release
  const response = await fetch(
    `https://api.github.com/repos/${REPO}/releases/latest`,
    {
      headers: {
        'Accept': 'application/vnd.github.v3+json'
      }
    }
  );
  
  const data = await response.json();
  const latestVersion = data.tag_name?.replace('v', '') || 'unknown';
  
  const hasUpdate = latestVersion !== currentVersion;
  
  return { hasUpdate, latestVersion };
};
```

## Времева таблица

| Операц��я | ��реме |
|-----------|-------|
| Health check (current) | 5 sec |
| DB Backup | 30-60 sec |
| Images Backup | 1-2 min |
| Git fetch | 10-30 sec |
| Docker build | 2-5 min |
| Deploy backend | 15-30 sec |
| Health check (new) | 15-60 sec |
| Deploy frontend | 10-20 sec |
| **Total** | **5-10 min** |
| **Rollback** | **30-60 sec** |

## Защити

| Защита | Описание |
|--------|----------|
| Health check преди deploy | Проверява че текущата версия работи |
| DB Backup (pg_dump) | Преди всяка промяна |
| Images Backup (docker save) | За rollback |
| Auto-rollback при fail | Ако health check не мине |
| Max 3 backups | Изтрива старите автоматично |
| Health check след deploy | Проверява новата версия |

## GitHub Интеграция

### Къде да проверява за нова версия

- **URL:** `https://api.github.com/repos/BgDrDark/chronos/releases/latest`
- **Метод:** GET request
- **Response:** `{ tag_name: "v3.6.2.0", body: "...", published_at: "..." }`

### Какво показва

| Сценарий | Показва |
|----------|---------|
| Има нова версия | "Налична версия: 3.6.2.0" |
| Няма нова версия | "Използвате най-новата версия" |
| Грешка | "Не може да се провери" |

## Rollback Процедура

### Автоматичен (при fail)

```
deploy-safe.sh:
  1. Health check timeout
  2. ./scripts/rollback.sh $TIMESTAMP
  3. docker compose up -d
```

### Ръчен

```bash
# Спри container-ите
docker compose down

# Върни старите images
docker load -i /backups/chronos/backend_20260430_020000.tar
docker load -i /backups/chronos/frontend_20260430_020000.tar

# Стартирай
docker compose up -d
```

## Инструкции за употреба

### 1. Първата инсталация

```bash
# Създай backup директория
mkdir -p /backups/chronos

# Направи скриптовете изпълними
chmod +x scripts/backup.sh
chmod +x scripts/deploy-safe.sh
chmod +x scripts/rollback.sh

# Тествай backup
./scripts/backup.sh
```

### 2. Ръчен Deploy

```bash
./scripts/deploy-safe.sh
```

### 3. Ръчен Rollback

```bash
# Листни наличните backups
ls -la /backups/chronos/

# Върни конкретен backup
./scripts/rollback.sh 20260430_020000
```

### 4. Check for Update (Frontend)

```
 Отиди в Settings
 Натисни "Провери"
 Виж дали има нова версия
```

## Troubleshooting

| Проблем | Решение |
|---------|--------|
| Backup fail | Провери PostgreSQL credentials |
| Build fail | Провери Docker |
| Health check fail | Веми логове: `docker compose logs` |
| Rollback fail | Ръчно: `docker load -i ...` |

---

## Версии

| Версия | Дата | Описание |
|--------|-----|----------|
| 1.0 | 30.04.2026 | Първоначална версия |