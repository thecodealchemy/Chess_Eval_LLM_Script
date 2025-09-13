@echo off

REM Development setup script for Windows

echo Setting up Chess Analysis App...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist server\.env (
    echo Creating environment file...
    copy server\.env.example server\.env
    echo Please edit server\.env with your MongoDB connection string and API keys.
)

REM Start services
echo Starting services with Docker Compose...
docker-compose up -d

echo.
echo 🎉 Setup complete!
echo.
echo Services are starting up. This may take a few minutes...
echo.
echo Once ready, you can access:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down
echo.
pause