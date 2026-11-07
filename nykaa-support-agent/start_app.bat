@echo off
setlocal
cd /d "%~dp0"
set MOCK_LLM=true
set CREWAI_DISABLE_TELEMETRY=true
set OTEL_SDK_DISABLED=true
set CREWAI_TRACING_ENABLED=false

echo =====================================================
echo          NYKAA SUPPORT AGENT - DASHBOARD
echo =====================================================
echo Project folder: %CD%
echo.
echo Select the environment you installed:
echo [1] Python 3.12 environment (.venv312)
echo [2] Python 3.14 environment (.venv314)
echo [3] Existing .venv environment
echo [4] Exit
set /p CHOICE=Choose [1-4]:
if "%CHOICE%"=="1" set "VENV=.venv312"
if "%CHOICE%"=="2" set "VENV=.venv314"
if "%CHOICE%"=="3" set "VENV=.venv"
if "%CHOICE%"=="4" exit /b 0
if not defined VENV echo Invalid choice.& pause & exit /b 1
if not exist "%VENV%\Scripts\python.exe" echo Environment %VENV% not found. Run setup.bat or create it in PyCharm first.& pause & exit /b 1

echo.
echo Checking dashboard files...
"%VENV%\Scripts\python.exe" -c "from pathlib import Path; import api.main as m; print('Loaded:',m.__file__); print('Dashboard:',m.INDEX_FILE); print('Dashboard exists:',m.INDEX_FILE.is_file()); print('Root route:',any(getattr(r,'path',None)=='/' for r in m.app.routes))"
if errorlevel 1 pause & exit /b 1

echo.
echo Starting at http://127.0.0.1:8000/
echo Swagger remains available at http://127.0.0.1:8000/docs
echo Press CTRL+C to stop.
echo.
"%VENV%\Scripts\python.exe" -m uvicorn api.main:app --app-dir "%CD%" --host 127.0.0.1 --port 8000
pause
