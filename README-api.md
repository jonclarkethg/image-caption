# Image Caption API

A web application that generates alt text for images using various AI models.

## Overview

This API allows you to generate alt text for images by providing an image URL and selecting an AI model. It leverages the existing image captioning functionality and exposes it through a REST API.

## Installation

1. Make sure you have all the prerequisites installed as described in the original README.md:
   - Python 3.x
   - Ollama (for local models)
   - Required LLM plugins and API keys

2. Install the additional dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

### Starting the API Server

```bash
# Activate the virtual environment
source .venv/bin/activate

# Start the server
python app.py
```

The server will start on http://0.0.0.0:5000 by default.

### API Endpoints

#### Generate Alt Text

**Endpoint**: `/api/generate-alt-text`

**Method**: POST

**Request Body**:
```json
{
  "image_url": "https://example.com/image.jpg",
  "model": "chatgpt-4o-latest",
  "context": "Optional context to improve caption accuracy"
}
```

**Response**:
```json
{
  "image_url": "https://example.com/image.jpg",
  "alt_text": "Generated alt text for the image.",
  "model": "chatgpt-4o-latest",
  "processing_time": 2.5
}
```

**Error Response**:
```json
{
  "error": "Error message",
  "status_code": 400
}
```

#### List Available Models

**Endpoint**: `/api/models`

**Method**: GET

**Response**:
```json
{
  "models": [
    {
      "name": "chatgpt-4o-latest",
      "description": "GPT-4 with Vision",
      "provider": "openai",
      "deployment": "cloud",
      "installed": true
    },
    ...
  ]
}
```

#### Health Check

**Endpoint**: `/api/health`

**Method**: GET

**Response**:
```json
{
  "status": "ok"
}
```

## Example Usage

### Using curl

```bash
curl -X POST http://localhost:5000/api/generate-alt-text \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "model": "chatgpt-4o-latest"
  }'
```

### Using Python requests

```python
import requests
import json

url = "http://localhost:5000/api/generate-alt-text"
payload = {
    "image_url": "https://example.com/image.jpg",
    "model": "chatgpt-4o-latest",
    "context": "Photo taken at a conference"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

## Configuration

The API can be configured using environment variables:

- `DEBUG`: Set to 'True' to enable debug mode (default: 'False')
- `PORT`: Port to run the server on (default: 5000)
- `HOST`: Host to bind the server to (default: '0.0.0.0')
- `TEMP_DIR`: Directory to store temporary files (default: './temp')

## Deployment

For production deployment, it's recommended to use Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## License

See the original project license.