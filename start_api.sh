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

# Set Vertex AI environment variables
# Replace these values with your actual Google Cloud project details
export VERTEX_AI_PROJECT_ID="thg-media-vertexai-content"
export VERTEX_AI_REGION="us-central1"
export VERTEX_AI_CREDENTIALS="/Users/clarkej/thg-media-vertexai-content-74926fb82d4a.json"

# Set to True to enable Vertex AI by default
export VERTEX_AI_ENABLED=False

# Start the API server in production mode with Gunicorn
echo "Starting API server in production mode with 4 workers..."
export PORT=5001
export MOCK_MODE=False
cd "${SCRIPT_DIR}" && gunicorn -w 4 -b 0.0.0.0:5001 app:app