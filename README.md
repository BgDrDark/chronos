# Chronos - ERP система за сладкарско производство

## Overview

Chronos е модулна ERP система, създадена специално за нуждите на сладкарското производство и хранително-вкусовата промишленост в България.

Системата е изградена от самото начало в съответствие с българското законодателство:

- **Трудово законодателство (ТРЗ)** — автоматично изчисляване на работно време, нощен труд, извънреден труд, труд в почивни и празнични дни, годишен отпуск, болни дни (НОИ), трудови договори и приложения
- **Счетоводни стандарти** — ДДС регистри, фактуриране, SAF-T съвместимост, касови операции, банкови транзакции, счетоводни статии
- **НАП и НОИ интеграция** — осигурителни вноски, данъци, декларации, фишове за заплата по българските изисквания
- **Производствено планиране** — рецептури с автоматично калкулиране на себестойност, FEFO складов контрол, производствени станции, партидно проследяване

Обединява управление на производство, склад, рецептури, заплати, доставки, счетоводство и поведенчески анализ в една платформа.

## Бърз Старт

```bash
docker compose up -d
docker compose exec backend alembic -c /app/backend/alembic.ini upgrade head
docker compose exec backend python -m backend.seed_modules
```

## Модули

| Модул | Код | Описание |
|-------|-----|----------|
| Сладкарско производство | `confectionery` | Рецептурник, производствени станции, FEFO склад, ценообразуване |
| Склад и инвентар | `inventory` | Суровини, разходни логове, производствени задачи |
| Графици и смени | `shifts` | Работни графици, присъствие, закъснения, QR терминали |
| Заплати | `salaries` | Payroll, фишове, осигуровки, данъци по българските закони |
| Счетоводство | `accounting` | Фактури, доставчици, разплащания, SAF-T съвместимост |
| Киоск терминал | `kiosk` | Self-service терминали за вход, GPS проверка, QR достъп |
| Доставки | `fleet` | Управление на автомобили, горива, разходи, маршрути |
| Разходи по отдели | `cost_centers` | Проследяване на разходи по департаменти |
| Уведомления | `notifications` | SMTP настройки, автоматични известия, имейл справки |
| Поведенчески анализ | `behavioral_analysis` | 4-слоен анализ на екипите, XAI, bias detection |
| Интеграции | `integrations` | API достъп, външни системи, webhooks |

## Архитектура

- **Backend**: Python/FastAPI + Strawberry GraphQL + PostgreSQL
- **Frontend**: React + TypeScript + Apollo Client + Material UI
- **API Gateway**: Chronos Gateway за reverse proxy
- **Deploy**: Update listener за безопасни ъпдейти без downtime

## Деплоймент

### Production Setup

- Docker + Docker Compose
- Reverse proxy (Nginx/Caddy)
- PostgreSQL 18

### Update Listener Setup

Автоматизиран скрипт за безопасни ъпдейти от вграден UI:

```bash
sudo bash scripts/setup-update-listener.sh
```

Listener-ът работи на host машината, изпълнява `update.sh` извън контейнера с backup, миграции, health checks и auto-rollback.

### Safe Deploy Script

`scripts/update.sh` — безопасен deploy с:
- Pre-deploy DB lock
- Backup verification (DB + images + config)
- Alembic dry-run
- Graceful shutdown
- Auto-rollback при грешка

### Rollback

```bash
./scripts/rollback.sh
```

## Конфигурация

| Variable | Default | Описание |
|----------|---------|----------|
| `POSTGRES_USER` | `postgres` | DB потребител |
| `POSTGRES_PASSWORD` | `postgres` | DB парола |
| `POSTGRES_DB` | `chronosdb` | DB име |
| `DEPLOY_API_KEY` | auto-generated | Deploy auth ключ |
| `DEPLOY_LISTENER_URL` | `http://host.docker.internal:14241` | Update listener URL |
| `VERSION` | `unknown` | Версия на приложението |

## Версии

Формат: `vMAJOR.MINOR.PATCH.BUILD`

```bash
git tag -a v3.6.60.0 -m "Release v3.6.60.0"
git push origin v3.6.60.0
```

## Лиценз

Private - All rights reserved.
