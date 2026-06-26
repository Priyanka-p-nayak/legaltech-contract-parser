#!/bin/bash
# ============================================================
# DEVELOPMENT STARTUP SCRIPT
# Run this to start the project in development mode
# ============================================================

echo "Starting LegalTech in DEVELOPMENT mode..."

docker-compose \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up --build "$@"