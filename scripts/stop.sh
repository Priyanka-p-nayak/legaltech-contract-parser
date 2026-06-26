#!/bin/bash
# ============================================================
# STOP ALL SERVICES
# ============================================================

echo "Stopping all LegalTech services..."
docker-compose down
echo "All services stopped."