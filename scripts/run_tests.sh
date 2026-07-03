#!/bin/bash
# ============================================================
# run_tests.sh — Member 3
# Runs all tests with coverage report
# ============================================================

echo "============================================"
echo "  LegalTech — Running Full Test Suite"
echo "============================================"
echo ""

# Activate virtual environment if not active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run all tests with verbosity
echo "Running tests..."
python manage.py test contracts.tests \
    --verbosity=2 \
    --timing

echo ""
echo "============================================"
echo "  Tests Complete!"
echo "============================================"