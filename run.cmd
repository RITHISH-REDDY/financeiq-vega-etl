@echo off
setlocal
cd /d "%~dp0"
if not "%~2"=="" goto usage
if "%~1"=="" goto start
if /i "%~1"=="etl" goto start
if /i "%~1"=="verify" goto start
goto usage
:start
if not exist ".venv\Scripts\python.exe" (
  if defined FINANCEIQ_PYTHON (
    "%FINANCEIQ_PYTHON%" -m venv .venv
  ) else (
    py -3 -m venv .venv
  )
  if errorlevel 1 goto python_error
)
if not exist "logs" mkdir logs
if not exist ".venv\financeiq-ready" goto install
fc /b requirements.txt .venv\financeiq-ready >nul 2>&1
if not errorlevel 1 goto pipeline
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
copy /y requirements.txt .venv\financeiq-ready >nul
:pipeline
".venv\Scripts\python.exe" -m src.workflow %1
if errorlevel 1 goto failed
if /i "%~1"=="etl" exit /b 0
if /i "%~1"=="verify" exit /b 0
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
if errorlevel 1 goto failed
exit /b 0
:python_error
echo Python 3.11+ is required. Install Python, reopen CMD, then run run.cmd again.
echo Or set FINANCEIQ_PYTHON to the full path of an installed python.exe.
exit /b 1
:failed
echo FinanceIQ failed. Read the error above and logs\workflow.log.
exit /b 1
:usage
echo Usage: run.cmd [etl^|verify]
exit /b 2

