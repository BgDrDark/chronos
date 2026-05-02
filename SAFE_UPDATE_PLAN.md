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
MAX_BACKUPS=5

# Get PostgreSQL credentials from .env
if [ -f ".env" ]; then
    source .env
fi

POSTGRES_DB=${POSTGRES_DB:-chronosdb}

# Clean old backups (keep only MAX_BACKUPS)
ls -t $BACKUP_DIR/db_*.dump 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

# [1/3] Database Backup
pg_dump -U "$POSTGRES_USER" -h "$DB_HOST" -Fc "$POSTGRES_DB" -f "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Verify backup
if [ -f "$DB_BACKUP_FILE" ] && [ -s "$DB_BACKUP_FILE" ]; then
    echo "✓ Backup verified"
fi

# [2/3] Docker Images Backup
docker save $BACKEND_IMAGE -o "$BACKUP_DIR/backend_$TIMESTAMP.tar"
docker save $FRONTEND_IMAGE -o "$BACKUP_DIR/frontend_$TIMESTAMP.tar"

# [3/3] Configuration Backup
tar czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" .env docker-compose.yml
```

**Нови функции:**
- ✅ Backup verification (проверка че файлът е валиден)
- ✅ Configuration backup (.env + docker-compose.yml)
- ✅ Fallback към `docker exec` ако `pg_dump` не е в PATH
- ✅ MAX_BACKUPS увеличен на 5

### 2. scripts/deploy-safe.sh

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/chronos"
HEALTH_TIMEOUT=120
BUILD_TIMEOUT=600
LOCK_FILE="/tmp/chronos_deploy.lock"
DEPLOY_LOG="$BACKUP_DIR/deploy.log"

# Lock file - предотвратява concurrent deploys
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Another deployment is in progress"
    exit 1
fi
echo $$ > "$LOCK_FILE"

# Pre-deployment checks
# 1. Docker daemon
# 2. Disk space (min 1GB)
# 3. Git status
# 4. .env file existence
# 5. docker-compose.yml existence

# Deployment steps:
# [1/9] Health check (current)
# [2/9] Backup (DB + images + config)
# [3/9] Git fetch + reset
# [4/9] Build images (with cache, --force за no-cache)
# [5/9] Alembic migrations
# [6/9] Deploy backend + health check
# [7/9] Deploy frontend
# [8/9] Restart dependent services (gateway)
# [9/9] Final health check
```

**Нови функции:**
- ✅ **Lock file** - предотвратява concurrent deploys
- ✅ **Pre-deployment checks** - Docker, disk space, git, .env
- ✅ **Alembic migrations** - `alembic upgrade head` преди deploy
- ✅ **Deploy log** - всички действия се записват в `deploy.log`
- ✅ **Gateway restart** - рестартира gateway след deploy
- ✅ **Build timeout** - 600s лимит за build
- ✅ **--force флаг** - `--no-cache` build
- ✅ **--dry-run флаг** - показва какво ще направи без промени
- ✅ **Force recreate** - `--force-recreate` за env var промени

### 3. scripts/rollback.sh

```bash
#!/bin/bash
set -e

TIMESTAMP=${1:-""}
BACKUP_DIR="/backups/chronos"

# Find latest backup if no timestamp
if [ -z "$TIMESTAMP" ]; then
    TIMESTAMP=$(ls -t $BACKUP_DIR/db_*.dump | head -1 | xargs basename | sed 's/db_//;s/.dump//')
fi

# Verify all backup files exist
# [1/5] Stop containers
# [2/5] Restore Docker images
# [3/5] Restore Database (pg_restore --clean --if-exists)
# [4/5] Restore configuration (.env + docker-compose.yml)
# [5/5] Start containers + health check
```

**Нови функции:**
- ✅ **DB restore** - `pg_restore --clean --if-exists` (вече не е коментиран)
- ✅ **Config restore** - възстановява .env и docker-compose.yml
- ✅ **Confirmation prompt** - изисква "yes" за потвърждение
- ✅ **Backup verification** - проверява че всички файлове съществуват
- ✅ **Deploy log** - записва rollback в `deploy.log`

## Конфигурация

### .env

```bash
# Deployment
VERSION=3.6.1.0
GITHUB_REPO=https://github.com/BgDrDark/chronos

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=chronosdb
POSTGRES_HOST=localhost

# Backup
BACKUP_DIR=/backups/chronos
MAX_BACKUPS=5
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
│  Последен deploy: deploy.log           │
└────────────────────────────────────────┘
```

## Времева таблица

| Операция | Време |
|----------|-------|
| Pre-deployment checks | 5 sec |
| Health check (current) | 5 sec |
| DB Backup | 30-60 sec |
| Images Backup | 1-2 min |
| Git fetch | 10-30 sec |
| Docker build (cached) | 1-3 min |
| Docker build (no-cache) | 3-8 min |
| Alembic migrations | 5-30 sec |
| Deploy backend | 15-30 sec |
| Health check (new) | 15-60 sec |
| Deploy frontend | 10-20 sec |
| Gateway restart | 5 sec |
| **Total (cached)** | **4-8 min** |
| **Total (no-cache)** | **7-15 min** |
| **Rollback** | **30-60 sec** |

## Защити

| Защита | Описание |
|--------|----------|
| Lock file | Предотвратява concurrent deploys |
| Pre-deployment checks | Docker, disk space, git, .env |
| Health check преди deploy | Проверява че текущата версия работи |
| DB Backup (pg_dump) | Преди всяка промяна |
| Images Backup (docker save) | За rollback |
| Config Backup (.env + compose) | За rollback на конфигурация |
| Backup verification | Проверява че backup файловете са валидни |
| Alembic migrations | Автоматично прилага миграции |
| Auto-rollback при fail | Ако health check не мине |
| Max 5 backups | Изтрива старите автоматично |
| Health check след deploy | Проверява новата версия |
| Force recreate | Прилага промени в .env |
| Build timeout | 600s лимит за build |

## Флагове

| Флаг | Описание |
|------|----------|
| `--force` | Build без cache (`--no-cache`) |
| `--dry-run` | Показва какво ще направи без промени |

### Примери

```bash
# Нормален deploy (с cache)
./scripts/deploy-safe.sh

# Deploy без cache
./scripts/deploy-safe.sh --force

# Dry run - проверка без промени
./scripts/deploy-safe.sh --dry-run

# Rollback към последния backup
./scripts/rollback.sh

# Rollback към конкретен backup
./scripts/rollback.sh 20260502_143000
```

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
  1. Backend health check timeout
  2. ./scripts/rollback.sh $TIMESTAMP
  3. docker compose up -d
```

### Ръчен

```bash
# Спри container-ите
docker compose down

# Върни старите images
docker load -i /backups/chronos/backend_20260502_143000.tar
docker load -i /backups/chronos/frontend_20260502_143000.tar

# Върни базата данни
pg_restore -U postgres -d chronosdb --clean --if-exists /backups/chronos/db_20260502_143000.dump

# Върни конфигурацията
tar xzf /backups/chronos/config_20260502_143000.tar.gz -C /tmp/
cp /tmp/.env .env

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

# Тествай dry run
./scripts/deploy-safe.sh --dry-run
```

### 2. Ръчен Deploy

```bash
# Нормален deploy
./scripts/deploy-safe.sh

# С rebuild без cache
./scripts/deploy-safe.sh --force
```

### 3. Ръчен Rollback

```bash
# Листни наличните backups
ls -la /backups/chronos/

# Върни последния backup
./scripts/rollback.sh

# Върни конкретен backup
./scripts/rollback.sh 20260502_143000
```

### 4. Check for Update (Frontend)

```
1. Отиди в Settings
2. Натисни "Провери"
3. Виж дали има нова версия
```

## Deploy Log

Всички действия се записват в `/backups/chronos/deploy.log`:

```
[2026-05-02 14:30:00] BACKUP created: 20260502_143000
[2026-05-02 14:30:15] GIT updated: abc123def
[2026-05-02 14:32:00] BUILD complete: backend + frontend
[2026-05-02 14:32:10] ALEMBIC migrations applied
[2026-05-02 14:33:00] DEPLOY SUCCESS: version=3.6.1.0 timestamp=20260502_143000 backend=true frontend=true
```

### Преглед на логове

```bash
# Последните 10 deploy-а
tail -20 /backups/chronos/deploy.log

# Само успешни deploys
grep "DEPLOY SUCCESS" /backups/chronos/deploy.log

# Само failed deploys
grep "DEPLOY FAILED\|ROLLBACK" /backups/chronos/deploy.log
```

## Troubleshooting

| Проблем | Решение |
|---------|--------|
| Backup fail | Провери PostgreSQL credentials в .env |
| Build fail | Провери Docker: `docker compose build` |
| Health check fail | Виж логове: `docker compose logs backend` |
| Rollback fail | Ръчно: `docker load -i ...` + `pg_restore` |
| Lock file error | `rm -f /tmp/chronos_deploy.lock` |
| Disk space error | Изчисти стари backups: `ls -t /backups/chronos/ \| tail -n +6 \| xargs rm` |
| Alembic fail | Ръчно: `docker compose exec backend alembic upgrade head` |

---

## Версии

| Версия | Дата | Описание |
|--------|-----|----------|
| 1.0 | 30.04.2026 | Първоначална версия |
| 2.0 | 02.05.2026 | Alembic migrations, lock file, pre-checks, deploy log, config backup, DB restore, gateway restart |
