# Vertex AI Integration for Image Caption API

This document explains how to set up and use the Vertex AI integration for the Image Caption API.

## Setup

### 1. Google Cloud Project

You need a Google Cloud project with the Vertex AI API enabled. If you don't have one:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Vertex AI API for your project

### 2. Service Account Credentials

Create a service account and download the credentials:

1. In the Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Give it a name and description
4. Grant the "Vertex AI User" role
5. Click "Create and Continue"
6. Click "Done"
7. Find your new service account in the list, click the three dots menu, and select "Manage keys"
8. Click "Add Key" > "Create new key"
9. Choose JSON format and click "Create"
10. Save the downloaded JSON file to your project directory as `credentials.json`

### 3. Configure the API

Edit the `start_api.sh` script to set your Google Cloud project details:

```bash
# Set Vertex AI environment variables
export VERTEX_AI_PROJECT_ID="your-project-id"  # Replace with your actual project ID
export VERTEX_AI_REGION="us-central1"          # Replace with your preferred region
export VERTEX_AI_CREDENTIALS="${SCRIPT_DIR}/credentials.json"
export VERTEX_AI_ENABLED=True                  # Set to True to enable Vertex AI by default
```

## Usage

### Starting the API

Run the start_api.sh script to start the API server:

```bash
./start_api.sh
```

### Making Requests

To use Vertex AI for image captioning, add the `vertexai=true` query parameter to your API requests:

```bash
curl -X POST "http://localhost:5001/api/generate-alt-text?vertexai=true" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "model": "gemini-pro-vision",
    "context": "Optional context to improve caption accuracy"
  }'
```

The `model` parameter in your request will be used with Vertex AI. You can specify any model that's configured in your models.yaml file. If the model is a Vertex AI model (provider: "vertexai"), it will be used directly. If it's not a Vertex AI model, the system will fall back to using "gemini-pro-vision" but will still use the prompt and settings from the specified model.

### Response Format

The API response includes information about which provider was used to process the image:

```json
{
  "image_url": "https://example.com/image.jpg",
  "alt_text": "Generated caption for the image",
  "model": "gemini-pro-vision",
  "provider": "vertexai",
  "processing_time": 2.5,
  "model_time": 1.8
}
```

When using Vertex AI with a non-Vertex AI model, the response will include both the provider ("vertexai") and the original provider:

```json
{
  "image_url": "https://example.com/image.jpg",
  "alt_text": "Generated caption for the image",
  "model": "claude-3-sonnet",
  "provider": "vertexai",
  "original_provider": "anthropic",
  "processing_time": 2.5,
  "model_time": 1.8
}
```

### Available Models

The API includes the Gemini Pro Vision model from Vertex AI. You can see all available models by making a GET request to the `/api/models` endpoint:

```bash
curl "http://localhost:5001/api/models"
```

The response will include information about whether Vertex AI is enabled and which models are available.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

1. Verify that the `credentials.json` file is in the correct location
2. Check that the service account has the necessary permissions
3. Ensure the Vertex AI API is enabled for your project

### Model Availability

If the Gemini Pro Vision model is not available:

1. Check that the `VERTEX_AI_PROJECT_ID` and `VERTEX_AI_REGION` are set correctly
2. Verify that the Vertex AI API is enabled for your project
3. Ensure you have access to the Gemini Pro Vision model in your region

### Debug Mode

To enable debug mode, add `"debug": true` to your request body:

```json
{
  "image_url": "https://example.com/image.jpg",
  "model": "gemini-pro-vision",
  "debug": true
}
```

This will provide more detailed information about the processing steps and any errors that occur.