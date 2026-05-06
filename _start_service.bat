@echo off
REM Internal helper invoked by start_services.bat — do not run directly.
REM
REM Args:
REM   %1 = port number              (e.g. 8001)
REM   %2 = service folder name       (e.g. module1-integrity)
REM   %3 = display title             (e.g. "M1 Integrity")

if "%~1"=="" goto :usage
if "%~2"=="" goto :usage

title %~3 :%~1

REM Switch to the service directory (drive + path) — handles spaces correctly.
cd /d "%~dp0services\%~2"
if errorlevel 1 (
    echo [ERROR] Service directory not found: %~dp0services\%~2
    pause
    exit /b 1
)

REM Activate the project venv on D: drive.
if not exist "%~dp0.venv\Scripts\activate.bat" (
    echo [ERROR] Project venv not found at %~dp0.venv
    echo         Run start_services.bat from the project root to bootstrap it.
    pause
    exit /b 1
)
call "%~dp0.venv\Scripts\activate.bat"

set "PYTHONPATH=%~dp0services"
set "OPENBLAS_NUM_THREADS=1"

echo.
echo ============================================
echo  Starting %~3 on port %~1
echo  Working dir: %CD%
echo  Python:      %VIRTUAL_ENV%\Scripts\python.exe
echo ============================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port %~1 --reload

REM If uvicorn exits, hold the window so the user can read the log.
echo.
echo (uvicorn exited — press any key to close this window)
pause >nul
goto :eof

:usage
echo Usage: _start_service.bat ^<port^> ^<service-folder^> ^<title^>
pause
exit /b 1
