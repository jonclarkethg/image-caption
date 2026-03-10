# Image Caption API

Generate alt text for images using Google Gemini models via the `google-genai` library.

## Prerequisites

- Python 3.x
- A Google AI API key ([get one here](https://aistudio.google.com/apikey))

## Installation

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .
   source bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your API key (or add a default in `config.py`):
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   ```

## Quick start

```bash
./start_api.sh
```

The server starts on http://localhost:5001 with 4 Gunicorn workers.

## Available models

Configured in `models.yaml`:

| Model | Description |
|-------|-------------|
| `gemini-2.5-flash-lite` | Fastest, cheapest (~$0.03 per 1K images) |
| `gemini-2.5-flash` | Better quality (~$0.06 per 1K images) |
| `gemini-3.1-flash-lite-preview` | Latest generation (~$0.10 per 1K images) |

## API endpoints

### Generate alt text

```bash
curl -X POST http://localhost:5001/api/generate-alt-text \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "model": "gemini-2.5-flash-lite"
  }'
```

Response:
```json
{
  "image_url": "https://example.com/image.jpg",
  "alt_text": "A golden retriever running through a grassy field.",
  "model": "gemini-2.5-flash-lite",
  "provider": "google",
  "processing_time": 2.3,
  "model_time": 1.9,
  "cost": {
    "input_tokens": 324,
    "output_tokens": 21,
    "thinking_tokens": 0,
    "cached_tokens": 0,
    "total_cost": 3.06e-05
  }
}
```

Optional fields in the request body:
- `context` — additional context to improve caption accuracy
- `prompt` — custom prompt to override the default
- `debug` — set to `true` for debug logging

### List models

```bash
curl http://localhost:5001/api/models
```

### Health check

```bash
curl http://localhost:5001/api/health
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (from config.py) | Google AI API key |
| `PORT` | `5000` | Server port |
| `HOST` | `0.0.0.0` | Server bind address |
| `DEBUG` | `False` | Enable Flask debug mode |
| `MOCK_MODE` | `False` | Use mock responses (no API calls) |
| `TEMP_DIR` | `./temp` | Temporary file directory |

## Testing

```bash
python test_api.py "https://example.com/image.jpg" --model gemini-2.5-flash-lite
```
