@echo off
title Researchly AI - Start All Services
echo ============================================
echo  Researchly AI - Starting All Services
echo ============================================
echo.

set ROOT=%~dp0

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
    pip install "supabase==2.8.1"
    pip install sentence-transformers transformers tokenizers huggingface-hub
    pip install numpy scikit-learn pandas scipy tqdm joblib
    pip install PyMuPDF pdfplumber langdetect langchain langchain-text-splitters
    echo [OK] Dependencies installed.
) else (
    echo [OK] Python dependencies already present.
)

echo.
echo [INFO] Starting 5 Python services in separate windows...
echo.

REM Module 1 - Integrity (port 8001)
start "M1 Integrity :8001" cmd /k "title M1-Integrity && cd /d "%ROOT%services\module1-integrity" && set PYTHONPATH=%ROOT%services && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload 2>&1"

REM Module 2 - Collaboration (port 8002)
start "M2 Collaboration :8002" cmd /k "title M2-Collaboration && cd /d "%ROOT%services\module2-collaboration" && set PYTHONPATH=%ROOT%services && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload 2>&1"

REM Module 3 - Data Management (port 8003)
start "M3 Data :8003" cmd /k "title M3-Data && cd /d "%ROOT%services\module3-data" && set PYTHONPATH=%ROOT%services && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload 2>&1"

REM Module 4 - Analytics (port 8004)
start "M4 Analytics :8004" cmd /k "title M4-Analytics && cd /d "%ROOT%services\module4-analytics" && set PYTHONPATH=%ROOT%services && python -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload 2>&1"

REM Paper Chat - RAG + Training (port 8005)
start "Paper-Chat :8005" cmd /k "title PaperChat && cd /d "%ROOT%services\paper-chat" && set PYTHONPATH=%ROOT%services && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload 2>&1"

echo.
echo [DONE] 5 windows opened. Wait ~30 seconds for services to start.
echo.
echo  Health check URLs (paste in browser):
echo    http://localhost:8001/health
echo    http://localhost:8002/health
echo    http://localhost:8003/health
echo    http://localhost:8004/health
echo    http://localhost:8005/health
echo.
echo  Then run: start_web.bat
echo.
pause
