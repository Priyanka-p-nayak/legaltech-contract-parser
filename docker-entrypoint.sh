#!/bin/bash

# ============================================================
# DOCKER ENTRYPOINT SCRIPT — IMPROVED VERSION
# ============================================================

# Exit immediately if any command fails
set -e

# ── Color Output ───────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC}    $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $1"; }

# ── Banner ─────────────────────────────────────────────────
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  LegalTech Contract Parser Backend${NC}"
echo -e "${BLUE}  Starting Up...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ── Step 1: Wait for PostgreSQL ────────────────────────────
log_info "Step 1/4: Waiting for PostgreSQL..."

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
MAX_RETRIES=30
RETRY_COUNT=0

until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))

    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        log_error "PostgreSQL not available after $MAX_RETRIES retries!"
        log_error "Host: $DB_HOST | Port: $DB_PORT"
        log_error "Check your DB_HOST and DB_PORT environment variables."
        exit 1
    fi

    log_warning "PostgreSQL not ready. Retry $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

log_success "PostgreSQL is ready! (Host: $DB_HOST:$DB_PORT)"

# ── Step 2: Run Migrations ─────────────────────────────────
log_info "Step 2/4: Running database migrations..."

python manage.py migrate --noinput 2>&1

if [ $? -eq 0 ]; then
    log_success "Migrations complete!"
else
    log_error "Migrations failed!"
    exit 1
fi

# ── Step 3: Collect Static Files ──────────────────────────
log_info "Step 3/4: Collecting static files..."

python manage.py collectstatic --noinput --clear 2>/dev/null

log_success "Static files collected!"

# ── Step 4: Start Server ───────────────────────────────────
log_info "Step 4/4: Starting server..."

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Server is running!${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "  Health Check : http://0.0.0.0:8000/api/v1/health/"
echo -e "  Admin Panel  : http://0.0.0.0:8000/admin/"
echo -e "  API Base     : http://0.0.0.0:8000/api/v1/"
echo -e "${GREEN}============================================${NC}"
echo ""

# Start gunicorn with production settings
exec gunicorn legaltech_project.wsgi:application \
    --bind        0.0.0.0:8000 \
    --workers     2 \
    --worker-class sync \
    --timeout     120 \
    --graceful-timeout 30 \
    --keep-alive  5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile  - \
    --log-level     info \
    --capture-output