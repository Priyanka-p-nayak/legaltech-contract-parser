@echo off
REM ============================================================
REM run_tests.bat — Member 3
REM Runs all tests inside Docker
REM ============================================================

echo ============================================
echo   LegalTech — Running Full Test Suite
echo ============================================
echo.

echo Running tests inside Docker container...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec backend python manage.py test contracts.tests --verbosity=2

echo.
echo ============================================
echo   Tests Complete!
echo ============================================
pause