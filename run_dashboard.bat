@echo off
echo X Financial Analyzer - Streamlit Dashboard
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Start Streamlit dashboard
echo Starting Streamlit dashboard...
echo Dashboard will open at: http://localhost:8501
streamlit run dashboard.py

pause