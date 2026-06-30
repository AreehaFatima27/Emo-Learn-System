@echo off
title EmoLearn Quick Start
echo ===================================================
echo   🚀 EmoLearn Quick Start Launcher (Windows)
echo ===================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH. Please install Python 3.10+
    pause
    exit /b
)

:: 2. Check Node.js installation
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js/NPM is not installed or not in PATH. Please install Node.js
    pause
    exit /b
)

:: 3. Setup Backend
echo [1/4] Setting up Python virtual environment and dependencies...
cd backend
if not exist venv (
    echo Creating virtual environment venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/4] Initializing and Seeding Database...
python database/seed.py
if %errorlevel% neq 0 (
    echo WARNING: Database seed failed. Please verify that your PostgreSQL database emolearn is running and credentials in backend/.env are correct.
)

echo.
echo [3/4] Launching FastAPI Backend Server...
start "EmoLearn Backend API" cmd /k "title EmoLearn Backend && call venv\Scripts\activate.bat && uvicorn main:app --host 127.0.0.1 --port 8000"

:: 4. Setup Frontend
echo.
echo [4/4] Setting up Frontend and NPM packages...
cd ../frontend
echo Installing npm packages...
call npm install

echo Launching Frontend Development Server...
start "EmoLearn Frontend App" cmd /k "title EmoLearn Frontend && npm run dev"

echo.
echo ===================================================
echo   🎉 Success! Frontend and Backend are starting...
echo ===================================================
echo.
echo - Backend API: http://localhost:8000
echo - Swagger Docs: http://localhost:8000/docs
echo - Frontend App: http://localhost:5173
echo.
echo Press any key to exit this installer.
pause >nul
