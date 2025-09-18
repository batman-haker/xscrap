#!/bin/bash

echo "X Financial Analyzer - Streamlit Dashboard"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start Streamlit dashboard
echo "Starting Streamlit dashboard..."
echo "Dashboard will open at: http://localhost:8501"
streamlit run dashboard.py