@echo off
title Researchly AI - Web + Gateway
echo ============================================
echo  Researchly AI - Web + API Gateway
echo ============================================
echo.

set ROOT=%~dp0

REM ---- Install Node deps if needed ----
if not exist "%ROOT%node_modules\.modules.yaml" (
    echo [SETUP] Installing pnpm dependencies...
    pnpm install
)

echo Starting API Gateway on port 3001...
start "API Gateway :3001" cmd /k "cd /d %ROOT%apps\api-gateway && pnpm dev"

timeout /t 3 /nobreak >nul

echo Starting Next.js web on port 3000...
start "Web App :3000" cmd /k "cd /d %ROOT%apps\web && pnpm dev"

echo.
echo [OK] Opening browser in 10 seconds...
timeout /t 10 /nobreak >nul
start http://localhost:3000

echo.
echo Services running:
echo   Web:     http://localhost:3000
echo   Gateway: http://localhost:3001/api/v1/health
echo.
pause
