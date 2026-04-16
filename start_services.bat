@echo off
title Researchly AI - Start All Services
echo ============================================
echo  Researchly AI - Starting All Services
echo ============================================
echo.

set "ROOT=%~dp0"

REM ---- Check Python ----
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and retry.
    pause & exit /b 1
)

REM ---- Install shared Python deps (skip if already installed) ----
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing Python dependencies...
    echo         First run: downloads ~2-3 GB. Please wait.
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart python-dotenv httpx
    pip install "supabase>=2.10.0"
    pip install sentence-transformers transformers tokenizers huggingface-hub
    pip install numpy scikit-learn pandas scipy tqdm joblib
    pip install PyMuPDF pdfplumber langdetect langchain langchain-text-splitters
    pip install spacy arxiv beautifulsoup4 aiohttp
    python -m spacy download en_core_web_sm
    echo [OK] Dependencies installed.
) else (
    echo [OK] Python dependencies already present.
)

REM ---- Kill any old processes on these ports ----
echo [INFO] Clearing ports 8001-8005...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8001 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8002 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8003 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8004 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8005 " ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
echo [OK] Ports cleared.
echo.
echo [INFO] Starting 5 Python services in separate windows...
echo.

REM /D sets working directory -- handles spaces in path correctly
start "M1 Integrity :8001"   /D "%ROOT%services\module1-integrity"   cmd /k "set PYTHONPATH=%ROOT%services && set OPENBLAS_NUM_THREADS=1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak >nul

start "M2 Collaboration :8002" /D "%ROOT%services\module2-collaboration" cmd /k "set PYTHONPATH=%ROOT%services && set OPENBLAS_NUM_THREADS=1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"
timeout /t 3 /nobreak >nul

start "M3 Data :8003"          /D "%ROOT%services\module3-data"          cmd /k "set PYTHONPATH=%ROOT%services && set OPENBLAS_NUM_THREADS=1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"
timeout /t 3 /nobreak >nul

start "M4 Analytics :8004"     /D "%ROOT%services\module4-analytics"     cmd /k "set PYTHONPATH=%ROOT%services && set OPENBLAS_NUM_THREADS=1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload"
timeout /t 3 /nobreak >nul

start "PaperChat :8005"        /D "%ROOT%services\paper-chat"            cmd /k "set PYTHONPATH=%ROOT%services && set OPENBLAS_NUM_THREADS=1 && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"

echo.
echo [DONE] 5 windows opened. Wait ~30 seconds for all services to start.
echo.
echo  Paste these in browser to confirm each is running:
echo    http://localhost:8001/health   (M1 - Integrity)
echo    http://localhost:8002/health   (M2 - Collaboration)
echo    http://localhost:8003/health   (M3 - Data)
echo    http://localhost:8004/health   (M4 - Analytics)
echo    http://localhost:8005/health   (Paper Chat)
echo.
echo  Once all show status:ok  -- double-click start_web.bat
echo.
pause
