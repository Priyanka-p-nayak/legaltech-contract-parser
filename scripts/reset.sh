#!/bin/bash
# ============================================================
# RESET SCRIPT
# WARNING: This deletes ALL data including the database!
# Use only in development when you want a fresh start.
# ============================================================

echo "WARNING: This will delete ALL data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Stopping containers..."
    docker-compose down

    echo "Removing volumes (deletes all data)..."
    docker-compose down -v

    echo "Removing images..."
    docker-compose rm -f

    echo "Done. Run docker-compose up --build to start fresh."
else
    echo "Reset cancelled."
fi