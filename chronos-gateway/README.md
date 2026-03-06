# Chronos Gateway

Windows service за комуникация между терминалите в цеха и бекенда.

## Инсталация

1. Инсталирайте `ChronosGateway-Setup.exe`
2. Конфигурирайте `config.yaml` с вашия бекенд URL
3. Регистрирайте gateway-а в бекенда

## Конфигурация

```yaml
backend:
  url: "https://chronos.obka24.org"
  api_key: "your-api-key"
```

## Портове

- **1424** - Terminal Hub (за терминалите)
- **8889** - Web Dashboard (за мониторинг)

## Функции

- Регистрация на терминали
- QR сканиране
- Управление на принтери
- Мониторинг на активността
- Heartbeat към бекенда

## Развитие

```bash
# Инсталиране на зависимости
pip install -r requirements.txt

# Стартиране в development режим
python gateway/main.py

# Билдване с PyInstaller
pyinstaller gateway.spec
```
