@echo off
title Researchly AI - Web + Gateway
echo ============================================
echo  Researchly AI - Web + API Gateway
echo ============================================
echo.

set "ROOT=%~dp0"

REM ---- Kill old processes on 3000/3001 ----
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3001 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3000 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

REM ---- Install Node deps if needed ----
if not exist "%ROOT%node_modules\.modules.yaml" (
    echo [SETUP] Installing pnpm dependencies...
    cd /d "%ROOT%"
    pnpm install
)

echo [INFO] Starting API Gateway on port 3001...
start "API Gateway :3001" /D "%ROOT%apps\api-gateway" cmd /k "pnpm dev"

timeout /t 5 /nobreak >nul

echo [INFO] Starting Next.js web on port 3000...
start "Web App :3000" /D "%ROOT%apps\web" cmd /k "pnpm dev"

echo.
echo [OK] Opening browser in 12 seconds...
timeout /t 12 /nobreak >nul
start http://localhost:3000

echo.
echo  All services running:
echo    Web App : http://localhost:3000
echo    Gateway : http://localhost:3001/api/v1/health
echo.
pause
