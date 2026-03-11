# Chronos Gateway

Windows софтуер за комуникация между терминалите в цеха и бекенда.

## Изисквания

- Windows 10 или по-нов
- Administrator права за инсталация
- Интернет връзка за комуникация с backend

## Инсталация

### Вариант 1: Инсталатор (Препоръчителен)

1. Изтеглете `ChronosGatewaySetup.exe`
2. Стартирайте като Administrator
3. Следвайте инструкциите на екрана

### Вариант 2: Ръчна инсталация

1. Копирайте файловете в `C:\Program Files\Chronos Gateway`
2. Редактирайте `config.yaml`
3. Стартирайте `install.bat` като Administrator

## Конфигурация

### config.yaml

```yaml
backend:
  url: https://dev.chronos.org
  api_key: YOUR_API_KEY_HERE
  ssl_verify_disabled: true

gateway:
  alias: "My Gateway"
  id: "1"

network:
  ip: 0.0.0.0
  terminal_port: 1424
  web_port: 8889
```

### Вземане на API Key

1. Влезте в Chronos админ панела
2. Отидете в **отдел КД** → **Gateways**
3. Копирайте API Key-а

## Портове

| Порт | Описание |
|------|----------|
| 1424 | Terminal Hub (за терминалите) |
| 8889 | Web Dashboard (за мониторинг) |

## Свързване на хардуер

### SR201 Релейна платка

1. Свържете SR201 към USB порт
2. Редактирайте `config.yaml`:

```yaml
access_control:
  hardware:
    devices:
      - device_id: sr201_1
        port: COM3
```

За да намерите COM порта:
```batch
devmgmt.msc
```

### RFID Четци

Повечето RFID четци работят като клавиатура (Wiegand или EM4100).
Просто ги свържете USB и те ще работят автоматично.

## Функции

- Регистрация на терминали
- QR сканиране
- Управление на SR201 релета
- Мониторинг на активността
- Heartbeat към бекенда
- Локална SQLite база данни
- HTTPS комуникация с HMAC сигурност

## Структура на папката

```
C:\Program Files\Chronos Gateway\
├── ChronosGateway.exe       # Главно приложение
├── config.yaml             # Конфигурация
├── nssm.exe              # Service manager
├── logs\                  # Логове
│   └── gateway.log
├── data\                  # SQLite бази
│   ├── config.db
│   └── logs.db
├── install.bat            # Инсталация на service
├── uninstall.bat          # Деинсталация на service
└── uninstall.exe         # Премахва инсталатора
```

## Деинсталация

### През Start Menu
1. Отидете в Start Menu
2. Намерете "Chronos Gateway"
3. Кликнете "Uninstall"

### Ръчно
```batch
cd "C:\Program Files\Chronos Gateway"
uninstall.bat
```

## Развитие

### Инсталиране на зависимости
```bash
pip install -r requirements.txt
```

### Стартиране в development режим
```bash
python gateway/main.py
```

### Билдване с PyInstaller
```bash
pyinstaller chronos-gateway.spec
```

### Билдване на инсталатор
```bash
build.bat
```

## Често срещани проблеми

### Service-ът не стартира
- Проверете дали сте Administrator
- Проверете логовете в `logs\gateway.log`
- Проверете дали портовете са свободни

### Няма връзка с backend
- Проверете интернет връзката
- Проверете `backend.url` в config.yaml
- Проверете дали firewall-ът не блокира

### SR201 не работи
- Проверете COM порта в Device Manager
- Проверете дали портът е посочен в config.yaml
- Опитайте с друг USB порт

## Поддръжка

- GitHub: https://github.com/BgDrDark/chronos

## Лиценз

Copyright © 2026 Chronos. Всички права запазени.
