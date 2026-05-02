# Backend Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies + Docker CLI + Docker Compose plugin
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-bul \
    poppler-utils \
    fonts-dejavu-core \
    git \
    curl \
    gnupg \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --pre -r requirements.txt

# Copy the rest of the application code
# We copy the entire backend folder content to /app/backend
# so that "from backend..." imports work.
COPY . backend/

# Expose the port the app runs on
EXPOSE 14240

# Entrypoint script to run initialization and start the app
CMD ["bash", "-c", "python -m backend.init_db && uvicorn backend.main:app --host 0.0.0.0 --port 14240"]
