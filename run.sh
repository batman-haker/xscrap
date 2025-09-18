#!/bin/bash

echo "X Financial Analysis Tool"
echo "========================="

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

# Make main.py executable
chmod +x main.py

# Run the application
echo "Starting X Financial Analyzer..."
python main.py "$@"