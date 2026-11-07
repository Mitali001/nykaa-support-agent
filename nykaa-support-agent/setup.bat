@echo off
setlocal EnableExtensions
cd /d "%~dp0"

 echo =====================================================
 echo   NYKAA SUPPORT AGENT - PYTHON ENVIRONMENT SETUP
 echo =====================================================
 echo.
 echo Detected Python installations from the Windows launcher:
 py --list
 echo.
 echo Choose the interpreter for this project:
 echo   [1] Python 3.12 - FULL CAPSTONE (recommended, includes CrewAI)
 echo   [2] Python 3.14 - UI + RAG + AutoGen (CrewAI unavailable)
 echo   [3] Exit
 echo.
 set /p CHOICE=Enter choice [1-3]: 

if "%CHOICE%"=="1" goto PY312
if "%CHOICE%"=="2" goto PY314
if "%CHOICE%"=="3" exit /b 0
echo Invalid choice.
exit /b 1

:PY312
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.12 was not found by the py launcher.
  exit /b 1
)
set VENV=.venv312
set REQ=requirements-py312.txt
set EXPECTED=3.12
 goto CREATE

:PY314
py -3.14 --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.14 was not found by the py launcher.
  exit /b 1
)
set VENV=.venv314
set REQ=requirements-py314.txt
set EXPECTED=3.14

:CREATE
echo.
echo Creating environment %VENV% using Python %EXPECTED%...
if exist "%VENV%\Scripts\python.exe" (
  "%VENV%\Scripts\python.exe" -c "import sys; print(sys.version)" | findstr /b "%EXPECTED%." >nul
  if errorlevel 1 (
    echo Existing environment uses a different Python version. Recreating it...
    rmdir /s /q "%VENV%"
  )
)
if not exist "%VENV%\Scripts\python.exe" (
  py -%EXPECTED% -m venv "%VENV%"
  if errorlevel 1 goto FAILED
)

"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto FAILED
"%VENV%\Scripts\python.exe" -m pip install -r "%REQ%"
if errorlevel 1 goto FAILED

echo %EXPECTED%> .python-version-selected
echo.
echo =====================================================
echo Setup completed successfully.
echo Environment: %VENV%
"%VENV%\Scripts\python.exe" --version
echo.
if "%EXPECTED%"=="3.12" (
  echo Full capstone profile selected. CrewAI can be installed and exercised.
) else (
  echo Python 3.14 profile selected. CrewAI is excluded by its current Python version constraint.
  echo The app uses its deterministic CrewAI fallback in this profile.
)
echo Run start_app.bat to launch the dashboard.
echo =====================================================
pause
exit /b 0

:FAILED
echo.
echo Setup failed. Read the pip error above. Check internet access and try again.
pause
exit /b 1
