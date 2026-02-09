@echo off
setlocal enabledelayedexpansion
title Welding System - Smart Restart

color 0A
echo.
echo ========================================
echo   Welding System - Smart Restart
echo ========================================
echo.
echo This script will:
echo   1. Kill all existing services
echo   2. Clean up ports
echo   3. Start Backend API (Port 8000)
echo   4. Start User Portal (Port 3000)
echo   5. Start Admin Portal (Port 3001)
echo.
echo Press any key to continue...
pause >nul
cls

REM ========================================
REM STEP 1: Kill all processes
REM ========================================
echo.
echo [1/5] Killing existing processes...
echo ----------------------------------------

echo   - Killing Python processes...
taskkill /F /IM python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] Python processes killed
) else (
    echo     [INFO] No Python processes found
)

echo   - Killing Node.js processes...
taskkill /F /IM node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] Node.js processes killed
) else (
    echo     [INFO] No Node.js processes found
)

echo   - Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    echo     [OK] Port 3000 cleaned
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    echo     [OK] Port 3001 cleaned
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
    echo     [OK] Port 8000 cleaned
)

echo.
echo [OK] All processes killed
timeout /t 2 /nobreak >nul

REM ========================================
REM STEP 2: Verify ports are free
REM ========================================
echo.
echo [2/5] Verifying ports are free...
echo ----------------------------------------

set PORT_CHECK_FAILED=0

netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [ERROR] Port 8000 still in use!
    set PORT_CHECK_FAILED=1
) else (
    echo     [OK] Port 8000 is free
)

netstat -ano | findstr ":3000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [ERROR] Port 3000 still in use!
    set PORT_CHECK_FAILED=1
) else (
    echo     [OK] Port 3000 is free
)

netstat -ano | findstr ":3001.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [ERROR] Port 3001 still in use!
    set PORT_CHECK_FAILED=1
) else (
    echo     [OK] Port 3001 is free
)

if !PORT_CHECK_FAILED! equ 1 (
    echo.
    echo [ERROR] Some ports are still in use!
    echo Please close all applications using these ports and try again.
    pause
    exit /b 1
)

echo.
echo [OK] All ports are free
timeout /t 1 /nobreak >nul

REM ========================================
REM STEP 3: Check directories exist
REM ========================================
echo.
echo [3/5] Checking directories...
echo ----------------------------------------

if not exist "%~dp0backend" (
    echo     [ERROR] Backend directory not found!
    pause
    exit /b 1
)
echo     [OK] Backend directory found

if not exist "%~dp0frontend" (
    echo     [ERROR] Frontend directory not found!
    pause
    exit /b 1
)
echo     [OK] Frontend directory found

if not exist "%~dp0admin-portal" (
    echo     [WARNING] Admin portal directory not found
    echo     [INFO] Will skip admin portal
    set SKIP_ADMIN=1
) else (
    echo     [OK] Admin portal directory found
    set SKIP_ADMIN=0
)

echo.
echo [OK] Directory check complete
timeout /t 1 /nobreak >nul

REM ========================================
REM STEP 4: Start Backend
REM ========================================
echo.
echo [4/5] Starting Backend API...
echo ----------------------------------------

cd /d "%~dp0backend"
echo     Starting on port 8000...
start "Backend API - Port 8000 [FIXED]" cmd /k "echo Starting Backend API with latest fixes... && python -m uvicorn app.main:app --host localhost --port 8000 --reload"

echo     Waiting for backend to start (10 seconds)...
timeout /t 10 /nobreak >nul

REM Check if backend started
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [OK] Backend API started successfully
) else (
    echo     [WARNING] Backend may not have started yet
    echo     [INFO] Check the Backend API window for errors
)

REM ========================================
REM STEP 5: Start Frontend Services
REM ========================================
echo.
echo [5/5] Starting Frontend services...
echo ----------------------------------------

REM Start User Portal
echo     Starting User Portal on port 3000...
cd /d "%~dp0frontend"
start "User Portal - Port 3000" cmd /k "echo Starting User Portal... && npm run dev"
timeout /t 4 /nobreak >nul
echo     [OK] User Portal starting...

REM Start Admin Portal (if exists)
if !SKIP_ADMIN! equ 0 (
    echo     Starting Admin Portal on port 3001...
    cd /d "%~dp0admin-portal"
    start "Admin Portal - Port 3001" cmd /k "echo Starting Admin Portal... && npm run dev"
    timeout /t 2 /nobreak >nul
    echo     [OK] Admin Portal starting...
)

REM ========================================
REM COMPLETION
REM ========================================
echo.
echo ========================================
echo   All Services Started Successfully!
echo ========================================
echo.
echo Access URLs:
echo   User Portal:   http://localhost:3000
echo   Admin Portal:  http://localhost:3001
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo.
echo IMPORTANT NOTES:
echo   - Backend has latest fixes applied
echo   - Wait 15-20 seconds for all services to fully start
echo   - Check each window for any errors
echo   - If you see errors, check the individual windows
echo.
echo Next Steps:
echo   1. Wait 15-20 seconds
echo   2. Open browser to http://localhost:3000
echo   3. Login with your test account
echo   4. Go to Membership Center
echo   5. Should work without 400 error!
echo.
echo ========================================
echo.
pause

