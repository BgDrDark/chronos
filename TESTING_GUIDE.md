# Инструкции за Тестване на Chronos

## Достъп до системата

### Основни URL адреси

| Услуга | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:14240 |
| Kiosk (Clock In/Out) | http://localhost:3000/kiosk |
| Kiosk Terminal (Достъп) | http://localhost:3000/kiosk/terminal |
| Моята карта (QR) | http://localhost:3000/my-card |

### Администраторски акаунт

```
Email: admin@example.com
Password: admin1234
```

---

## Основни функционалности

### 1. Clock In/Out (Супа)
- Отворете: **http://localhost:3000/kiosk**
- Сканирайте QR код или въведете код ръчно
- Потвърдете действието

### 2. Kiosk Terminal (Контрол на достъп)
- Отворете: **http://localhost:3000/kiosk/terminal**
- Използва се за достъп до зони чрез RFID или кодове

### 3. Моята карта
- Отворете: **http://localhost:3000/my-card**
- Показва личен QR код за Clock In/Out

---

## Администраторски функции

### Вход като администратор
1. Отворете: **http://localhost:3000/login**
2. Въведете email и парола (виж по-горе)
3. Ще видите главното меню

### Меню структура

```
├── Табло (Dashboard)
├── Профил
├── Моят график
├── Отпуски
│   ├── Моите заявки
│   ├── Одобрения (admin)
│   └── Всички заявки (admin)
├── Табло присъствие (admin)
│   ├── Присъствие
│   └── Анализи и KPI
├── Графици (admin)
│   ├── Календар
│   ├── Текущ график
│   ├── Управление на смени
│   ├── Шаблони и Ротации
│   └── Масово назначаване
├── Потребители (admin)
│   ├── Списък служители
│   └── Организационна структура
├── Отдел финанси (admin)
├── Счетоводство (admin)
├── Уведомления (admin)
├── Настройки (admin)
├── отдел КД (admin) ⭐
│   ├── Kiosk Терминал
│   ├── Kiosk Достъп
│   ├── Терминали
│   ├── Gateways
│   ├── Зони за достъп
│   ├── Врати
│   ├── Кодове
│   ├── Логове
│   └── Потребители
├── Склад (admin)
├── Рецепти (admin)
├── Поръчки (admin)
├── Контрол (admin)
└── Clock In/Out / Kiosk Terminal
```

---

## Тестване на Контрол на достъп (КД)

### Стъпка 1: Създаване на зона
1. Влезте като admin
2. Отидете в **отдел КД** → **Зони за достъп**
3. Кликнете **+ Нова Зона**
4. Попълнете:
   - Zone ID: `zone_office`
   - Име: `Офис`
   - Ниво: `1`
5. Запазете

### Стъпка 2: Създаване на врата
1. Отидете в **отдел КД** → **Врати**
2. Кликнете **+ Добави врата**
3. Попълнете:
   - Door ID: `door_main`
   - Име: `Главна врата`
   - Зона: `Офис`
   - Gateway: `GATEWAY-001`
   - Device: `sr201_192_168_1_100`
   - Relay: `1`
4. Запазете

### Стъпка 3: Създаване на код за достъп
1. Отидете в **отдел КД** → **Кодове**
2. Кликнете **+ Нов код**
3. Попълнете:
   - Код: `1234`
   - Тип: `Еднократен` или `Многократен`
   - Зони: изберете `Офис`
4. Запазете

### Стъпка 4: Синхронизация с Gateway
1. Отидете в **отдел КД** → **Gateways**
2. Кликнете бутона ↗️ (Upload) до желания gateway
3. Изчакайте потвърждение "Успешно синхронизирано!"
4. Или кликнете ↙️ (Download) за да изтеглите от cloud

---

## Тестване на Gateway Sync

### Push Config (Gateway → Cloud)
```bash
curl -X POST http://localhost:14240/gateways/1/push-config \
  -H "X-Gateway-API-Key: gw_be9697906a6f40963d793164616e6fbaf61246f4682a82ef" \
  -H "Content-Type: application/json" \
  -d '{
    "zones": [{"zone_id": "zone_test", "name": "Тестова зона", "level": 1}],
    "doors": [{"door_id": "door_test", "name": "Тестова врата", "zone_db_id": 1, "device_id": "test", "relay_number": 1}]
  }'
```

### Pull Config (Cloud → Gateway)
```bash
curl -X POST http://localhost:14240/gateways/1/pull-config \
  -H "X-Gateway-API-Key: gw_be9697906a6f40963d793164616e6fbaf61246f4682a82ef"
```

---

## Тестване на Sync Logs

### Синхронизация на логове от Gateway
```bash
curl -X POST http://localhost:14240/gateways/1/access/sync-logs \
  -H "X-Gateway-API-Key: gw_be9697906a6f40963d793164616e6fbaf61246f4682a82ef" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "timestamp": "2026-03-08T10:00:00",
      "user_id": "123",
      "user_name": "Иван Иванов",
      "zone_id": "zone_office",
      "zone_name": "Офис",
      "door_id": "door_main",
      "door_name": "Главна врата",
      "action": "entry",
      "result": "granted",
      "method": "code"
    }
  ]'
```

---

## Модули

Системата поддържа следните модули (активират се от админ):

| Модул | Описание |
|-------|----------|
| kiosk | Контрол на достъп и time tracking |
| shifts | Графици и присъствия |
| salaries | Заплати и плащания |
| accounting | Счетоводство |
| confectionery | Склад, рецепти, поръчки |
| notifications | Email уведомления |
| integrations | Документация и интеграции |

---

## Често срещани грешки

### "Not Found" при API заявки
- Проверете дали backend контейнерът работи: `docker ps | grep chronos-backend`

### "Could not validate credentials"
- Влезте в профила си или използвайте /auth/token вместо /api/auth/login

### Gateway не се свързва
- Проверете IP адреса в config.yaml
- Уверете се, че backend е достъпен от gateway контейнера

---

## Полезни команди

```bash
# Стартиране на всички услуги
docker-compose up -d

# Преглед на логове
docker logs -f chronos-backend
docker logs -f chronos-gateway
docker logs -f chronos-frontend

# Рестартиране на услуга
docker restart chronos-backend

# Списък на контейнерите
docker ps

# Вход в контейнер
docker exec -it chronos-backend sh
docker exec -it chronos-gateway sh
```
