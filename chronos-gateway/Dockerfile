FROM python:3.13-slim

WORKDIR /app

# Инсталиране на системни зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копиране на изискванията
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копиране на кода
COPY . .

# Променлива за PYTHONPATH, за да намира модулите
ENV PYTHONPATH=/app

# Стартиране
CMD ["python", "gateway/main.py"]
