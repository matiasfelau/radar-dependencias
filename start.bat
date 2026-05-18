@echo off
REM Dependency Radar - Quick Start Script for Windows
REM Usage: start.bat [prod|dev]

setlocal enabledelayedexpansion

set MODE=%1
if "%MODE%"=="" set MODE=prod

echo 🚀 Dependency Radar - Starting in %MODE% mode...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop.
    exit /b 1
)

REM Check if docker-compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ docker-compose is not available. Please install Docker Compose.
        exit /b 1
    )
)

if "%MODE%"=="prod" (
    echo 📦 Building production images...
    docker-compose build
    echo 🔄 Starting services ^(production mode^)...
    docker-compose up -d
    echo.
    echo ✅ Services started!
    echo.
    echo 📍 Frontend: http://localhost:5173
    echo 📍 Backend:  http://localhost:8000
    echo 📍 API Docs: http://localhost:8000/docs
    echo.
    echo To view logs: docker-compose logs -f
    echo To stop:      docker-compose down
) else if "%MODE%"=="dev" (
    echo 📦 Starting development environment...
    docker-compose -f docker-compose.dev.yml up -d
    echo.
    echo ✅ Development services started!
    echo.
    echo 📍 Frontend: http://localhost:5173 ^(with hot-reload^)
    echo 📍 Backend:  http://localhost:8000 ^(with auto-reload^)
    echo 📍 pgAdmin:  http://localhost:5050 ^(admin@radar.local / admin^)
    echo 📍 API Docs: http://localhost:8000/docs
    echo.
    echo To view logs: docker-compose -f docker-compose.dev.yml logs -f
    echo To stop:      docker-compose -f docker-compose.dev.yml down
) else (
    echo ❌ Unknown mode: %MODE%
    echo Usage: %0 [prod^|dev]
    exit /b 1
)

echo.
echo 💡 First time? Register a project:
echo    curl -X POST "http://localhost:8000/api/v1/projects/register" ^
echo      -H "X-API-Key: default-api-key" ^
echo      -F "project_name=my-app" ^
echo      -F "environment=Dev" ^
echo      -F "dependency_file=@requirements.txt"
echo.
