@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".tmp" mkdir ".tmp"
if not exist ".pip-cache" mkdir ".pip-cache"
set "TEMP=%CD%\.tmp"
set "TMP=%CD%\.tmp"
set "PIP_CACHE_DIR=%CD%\.pip-cache"
set "PYTHONPYCACHEPREFIX=%CD%\.pycache"

set "LF_PYTHON="
if defined PYTHON_EXE if exist "%PYTHON_EXE%" set "LF_PYTHON=%PYTHON_EXE%"

if not defined LF_PYTHON (
  where python >nul 2>nul
  if not errorlevel 1 (
    python -c "import sys; assert sys.version_info >= (3, 11)" >nul 2>nul
    if not errorlevel 1 set "LF_PYTHON=python"
  )
)

if not defined LF_PYTHON (
  if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    set "LF_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  )
)

if not defined LF_PYTHON (
  echo Python 3.11 or newer was not found.
  echo Install Python from https://www.python.org/ or set PYTHON_EXE.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  "%LF_PYTHON%" -m venv .venv || exit /b 1
)

call .venv\Scripts\activate.bat || exit /b 1
python -m pip install --disable-pip-version-check -e ".[dev]" || exit /b 1
python -m lidar_forensics.synthetic || exit /b 1

echo.
echo LiDAR Forensics is starting at http://127.0.0.1:8765
echo Press Ctrl+C to stop the server.
python -m uvicorn lidar_forensics.app:app --host 127.0.0.1 --port 8765
