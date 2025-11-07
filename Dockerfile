# Multi-stage Dockerfile for Railway deployment
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install PyTorch CPU first (much smaller than GPU version)
# Using 2.2.0+cpu (available CPU version)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch==2.2.0+cpu

# Copy requirements and install dependencies
COPY requirements-railway.txt .
RUN pip install --no-cache-dir -r requirements-railway.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models logs

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check (disabled - Railway handles this via railway.toml)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:$PORT/health')" || exit 1

# Start the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

