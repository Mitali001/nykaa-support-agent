@echo off
setlocal
cd /d "%~dp0"
set MOCK_LLM=true
set CREWAI_DISABLE_TELEMETRY=true
set OTEL_SDK_DISABLED=true
set CREWAI_TRACING_ENABLED=false
if not exist ".venv\Scripts\python.exe" echo .venv not found. Activate your PyCharm interpreter or use start_app.bat.& pause & exit /b 1
".venv\Scripts\python.exe" -m uvicorn api.main:app --app-dir "%CD%" --host 127.0.0.1 --port 8000
pause
