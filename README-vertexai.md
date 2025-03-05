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
```

## Usage

### Starting the API

Run the start_api.sh script to start the API server:

```bash
./start_api.sh
```

### Making Requests

To use Vertex AI for image captioning, simply specify a model with "vertexai" as the provider in your API request:

```bash
curl -X POST "http://localhost:5001/api/generate-alt-text" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "model": "gemini-pro-vision",
    "context": "Optional context to improve caption accuracy"
  }'
```

The system automatically detects that "gemini-pro-vision" has a provider of "vertexai" in the models.yaml configuration and processes the image using Vertex AI.

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

### Available Models

The API includes the Gemini Pro Vision model from Vertex AI. You can see all available models by making a GET request to the `/api/models` endpoint:

```bash
curl "http://localhost:5001/api/models"
```

The response will include information about all available models and their providers.

## Adding New Vertex AI Models

To add a new Vertex AI model, update the `models.yaml` file with a new entry that has "vertexai" as the provider:

```yaml
new-vertexai-model:
  deployment: cloud
  description: New Vertex AI Model
  model: new-model-name
  prompt: Your prompt here...
  provider: vertexai
  settings:
    max_tokens: 75
    temperature: 0.1
```

The system will automatically use Vertex AI to process images when this model is specified.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

1. Verify that the `credentials.json` file is in the correct location
2. Check that the service account has the necessary permissions
3. Ensure the Vertex AI API is enabled for your project

### Model Availability

If the Vertex AI models are not available:

1. Check that the `VERTEX_AI_PROJECT_ID` and `VERTEX_AI_REGION` are set correctly
2. Verify that the Vertex AI API is enabled for your project
3. Ensure you have access to the models in your region

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