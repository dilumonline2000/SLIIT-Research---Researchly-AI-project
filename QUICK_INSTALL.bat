@echo off
REM Quick Install Script for Researchly AI (Windows)
REM Usage: QUICK_INSTALL.bat

setlocal enabledelayedexpansion

echo.
echo ════════════════════════════════════════════════════════════════
echo   RESEARCHLY AI — QUICK INSTALL
echo ════════════════════════════════════════════════════════════════
echo.

REM Check prerequisites
echo [1/7] Checking prerequisites...
where node >nul 2>nul || (
    echo [!] Node.js not found. Install from nodejs.org
    pause
    exit /b 1
)
where python >nul 2>nul || (
    echo [!] Python not found. Install from python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do set NODE_VER=%%i
for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo [+] Node.js: %NODE_VER%
echo [+] Python: %PY_VER%
echo.

REM Frontend
echo [2/7] Installing Frontend (Next.js)...
cd apps\web
call npm install >nul 2>&1 && echo [+] Frontend installed || echo [!] Frontend install failed
cd ..\..
echo.

REM API Gateway
echo [3/7] Installing API Gateway (Express)...
cd apps\api-gateway
call npm install >nul 2>&1 && echo [+] API Gateway installed || echo [!] API Gateway install failed
cd ..\..
echo.

REM Paper-Chat
echo [4/7] Installing Paper-Chat Service...
cd services\paper-chat
python -m venv venv >nul 2>&1
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1 && echo [+] Paper-Chat installed || echo [!] Paper-Chat install failed
deactivate
cd ..\..
echo.

REM Module 1
echo [5/7] Installing Module 1 (Integrity)...
cd services\module1-integrity
python -m venv venv >nul 2>&1
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1 && echo [+] Module 1 installed || echo [!] Module 1 install failed
deactivate
cd ..\..
echo.

REM Module 2
echo [6/7] Installing Module 2 (Collaboration)...
cd services\module2-collaboration
python -m venv venv >nul 2>&1
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1 && echo [+] Module 2 installed || echo [!] Module 2 install failed
deactivate
cd ..\..
echo.

REM Module 3
echo [7/7] Installing Module 3 (Data Management)...
cd services\module3-data
python -m venv venv >nul 2>&1
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1 && echo [+] Module 3 installed || echo [!] Module 3 install failed
deactivate
cd ..\..
echo.

echo ════════════════════════════════════════════════════════════════
echo   INSTALLATION COMPLETE!
echo ════════════════════════════════════════════════════════════════
echo.

echo Next steps:
echo.
echo 1. Set up environment variables:
echo    - Copy apps\web\.env.example to apps\web\.env.local
echo    - Copy services\.env.example to services\.env
echo    - Fill in SUPABASE_URL and API keys
echo.
echo 2. Start 4 services in 4 separate terminals:
echo    Terminal 1: cd apps\web ^&^& npm run dev
echo    Terminal 2: cd apps\api-gateway ^&^& npm run dev
echo    Terminal 3: cd services\paper-chat ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload --port 8005
echo    Terminal 4: cd services\module1-integrity ^&^& venv\Scripts\activate ^&^& python -m uvicorn app.main:app --reload --port 8002
echo.
echo 3. Open browser: http://localhost:3000
echo.
echo For detailed instructions, see: TEAM_SETUP_GUIDE.md
echo.

pause
