@echo off
cd /d "%~dp0"
echo Windows Python Launcher inventory:
py --list
echo.
echo Project environments:
if exist .venv312\Scripts\python.exe .venv312\Scripts\python.exe --version
if exist .venv314\Scripts\python.exe .venv314\Scripts\python.exe --version
echo.
echo Python 3.8 and 3.9 are not supported for this capstone's current framework stack.
pause
