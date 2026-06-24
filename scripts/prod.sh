#!/bin/bash
# ============================================================
# PRODUCTION STARTUP SCRIPT
# Run this to start the project in production mode
# ============================================================

echo "Starting LegalTech in PRODUCTION mode..."

docker-compose \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    up -d --build "$@"

echo ""
echo "Services started in background."
echo "View logs: docker-compose logs -f"
echo "API URL:   http://localhost/api/v1/health/"