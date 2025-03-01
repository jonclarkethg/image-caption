#!/bin/bash

# Activate virtual environment
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source "${SCRIPT_DIR}/.venv/bin/activate"

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r "${SCRIPT_DIR}/requirements.txt"

# Create temp directory if it doesn't exist
mkdir -p "${SCRIPT_DIR}/temp"

# Kill any existing processes on port 5000 and 5001
echo "Checking for existing processes on ports 5000 and 5001..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Start the API server in mock mode
echo "Starting API server in mock mode..."
export PORT=5001
export MOCK_MODE=True
python "${SCRIPT_DIR}/app.py"