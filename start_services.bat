@echo off
title Researchly AI - Start All Services
echo ============================================
echo  Researchly AI - Starting All Services
echo ============================================
echo.

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"

REM ---- Confirm a global Python exists (used only to bootstrap the venv) ----
python --version >nul 2>&1
if errorlevel 1 goto :no_python

REM ---- Create the project venv on D: drive if it doesn't exist ----
if not exist "%VENV_PY%" goto :create_venv
goto :check_fastapi

:create_venv
echo [SETUP] Creating project venv at %VENV%
python -m venv "%VENV%"
if errorlevel 1 goto :venv_failed
"%VENV_PY%" -m pip install --upgrade pip
goto :install_all

:check_fastapi
"%VENV_PY%" -c "import fastapi" >nul 2>&1
if errorlevel 1 goto :install_all
goto :check_topups

:install_all
echo [SETUP] Installing Python dependencies into the venv...
echo         First run: downloads ~2-3 GB. Please wait.
"%VENV_PY%" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
"%VENV_PY%" -m pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart python-dotenv httpx
"%VENV_PY%" -m pip install "supabase>=2.10.0"
"%VENV_PY%" -m pip install sentence-transformers transformers tokenizers huggingface-hub
"%VENV_PY%" -m pip install numpy scikit-learn pandas scipy tqdm joblib
"%VENV_PY%" -m pip install pypdf pdfplumber langdetect langchain langchain-text-splitters
"%VENV_PY%" -m pip install spacy arxiv beautifulsoup4 aiohttp
"%VENV_PY%" -m pip install statsmodels xgboost
"%VENV_PY%" -m spacy download en_core_web_sm
echo [OK] Dependencies installed.
goto :clear_ports

:check_topups
echo [INFO] Verifying optional deps...
"%VENV_PY%" -c "import statsmodels" >nul 2>&1
if errorlevel 1 call :install_pkg statsmodels
"%VENV_PY%" -c "import xgboost" >nul 2>&1
if errorlevel 1 call :install_pkg xgboost
"%VENV_PY%" -c "import pypdf" >nul 2>&1
if errorlevel 1 call :install_pkg pypdf
"%VENV_PY%" -c "import pdfplumber" >nul 2>&1
if errorlevel 1 call :install_pkg pdfplumber
echo [OK] Python deps OK.
goto :clear_ports

:install_pkg
echo [SETUP] Installing missing dep: %1
"%VENV_PY%" -m pip install %1
exit /b

:clear_ports
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

REM Each service launches in a child shell whose working directory is the
REM project root (/D "%ROOT%"). That way the helper .bat can be referenced
REM by its plain filename — no path quoting needed inside cmd /k.
start "M1 Integrity :8001"     /D "%ROOT%" cmd /k _start_service.bat 8001 module1-integrity     "M1 Integrity"
timeout /t 3 /nobreak >nul

start "M2 Collaboration :8002" /D "%ROOT%" cmd /k _start_service.bat 8002 module2-collaboration "M2 Collaboration"
timeout /t 3 /nobreak >nul

start "M3 Data :8003"          /D "%ROOT%" cmd /k _start_service.bat 8003 module3-data          "M3 Data"
timeout /t 3 /nobreak >nul

start "M4 Analytics :8004"     /D "%ROOT%" cmd /k _start_service.bat 8004 module4-analytics     "M4 Analytics"
timeout /t 3 /nobreak >nul

start "PaperChat :8005"        /D "%ROOT%" cmd /k _start_service.bat 8005 paper-chat            "PaperChat"

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
goto :eof

:no_python
echo.
echo [ERROR] Python not found on PATH. Install Python 3.10+ and retry.
echo.
pause
exit /b 1

:venv_failed
echo.
echo [ERROR] Failed to create venv. Check disk space and Python install.
echo.
pause
exit /b 1
