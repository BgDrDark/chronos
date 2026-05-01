# Backend Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-bul \
    poppler-utils \
    fonts-dejavu-core \
    git \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# We copy the entire backend folder content to /app/backend
# so that "from backend..." imports work.
COPY . backend/

# Expose the port the app runs on
EXPOSE 14240

# Entrypoint script to run initialization and start the app
CMD ["bash", "-c", "python -m backend.init_db && uvicorn backend.main:app --host 0.0.0.0 --port 14240"]
