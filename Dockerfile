# ============================================================
# DOCKERFILE FOR LEGALTECH DJANGO BACKEND
# ============================================================
FROM python:3.13-slim

LABEL maintainer="LegalTech Team"
LABEL description="LegalTech Contract Parser Django Backend"
LABEL version="1.0.0"

# Prevents Python from writing .pyc files and buffers stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system dependencies for PostgreSQL and PDF processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev gcc libffi-dev curl netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app/

# Create required directories
RUN mkdir -p /app/media/contracts
RUN mkdir -p /app/logs
RUN mkdir -p /app/staticfiles

# Make the startup script executable
RUN chmod +x /app/docker-entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Run the entrypoint script when container starts
ENTRYPOINT ["/app/docker-entrypoint.sh"]