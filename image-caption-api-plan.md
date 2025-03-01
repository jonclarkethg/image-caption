# Image Caption Web Application Plan

## 1. Project Overview

The goal is to create a web application that:
- Accepts a REST POST request with an image URL and an LLM model name
- Downloads and processes the image using the specified AI model
- Returns the generated alt text as a response

## 2. Technical Architecture

### 2.1 Web Framework Selection
We'll use Flask as it's lightweight and perfect for creating REST APIs in Python. It will allow us to:
- Define API endpoints
- Handle HTTP requests and responses
- Manage error handling

### 2.2 Component Architecture
The application will have the following components:
1. **API Layer**: Handles HTTP requests/responses and input validation
2. **Image Processing Layer**: Downloads images from URLs
3. **Caption Generation Layer**: Reuses existing code to generate captions
4. **Response Formatting Layer**: Formats the results as JSON responses

## 3. Implementation Plan

### 3.1 Project Setup
1. Create a new virtual environment for the web application
2. Install required dependencies:
   - Flask for the web framework
   - Requests for downloading images from URLs
   - All existing dependencies (llm, pillow, ollama, pyyaml)

### 3.2 Code Modifications

#### 3.2.1 Create Flask Application
Create a new file `app.py` that:
- Initializes a Flask application
- Defines the API endpoints
- Handles request validation and error responses

#### 3.2.2 Modify Image Processing
Extend the existing code to:
- Accept image URLs in addition to local file paths
- Download images from URLs to a temporary location
- Process the downloaded images using the existing caption generation code

#### 3.2.3 API Endpoint Implementation
Create a `/generate-alt-text` endpoint that:
- Accepts POST requests with JSON payload
- Validates the input (image URL and model name)
- Calls the caption generation function
- Returns the result as a JSON response

### 3.3 Error Handling
Implement comprehensive error handling for:
- Invalid input parameters
- Failed image downloads
- Model errors
- Server errors

### 3.4 Testing
1. Unit tests for individual components
2. Integration tests for the API endpoints
3. Manual testing with various image URLs and models

## 4. API Specification

### 4.1 Endpoint: `/generate-alt-text`

**Method**: POST

**Request Body**:
```json
{
  "image_url": "https://example.com/image.jpg",
  "model": "chatgpt-4o-latest"
}
```

**Optional Parameters**:
- `context`: Additional context to help generate more accurate captions

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

## 5. Deployment Considerations

### 5.1 Local Development
- Run with Flask's development server

### 5.2 Production Deployment
- Use Gunicorn or uWSGI as WSGI server
- Consider containerization with Docker
- Set up proper logging and monitoring

## 6. Future Enhancements

1. Add authentication for API access
2. Implement rate limiting
3. Add caching for frequently requested images
4. Support for batch processing multiple images
5. Add a simple web UI for testing the API

## 7. Implementation Timeline

1. **Day 1**: Project setup and initial Flask application
2. **Day 2**: Implement image URL processing and integrate with existing caption code
3. **Day 3**: Complete API endpoint implementation and error handling
4. **Day 4**: Testing and documentation
5. **Day 5**: Deployment setup and final adjustments

## 8. Required Code Changes

### 8.1 New Files
1. `app.py` - Main Flask application
   ```python
   from flask import Flask, request, jsonify
   import utils
   import api
   
   app = Flask(__name__)
   
   # Register API endpoints
   app.register_blueprint(api.blueprint)
   
   if __name__ == "__main__":
       app.run(debug=True)
   ```

2. `utils.py` - Utility functions for image downloading and processing
   ```python
   import requests
   import tempfile
   import os
   from pathlib import Path
   
   def download_image(url):
       """Download image from URL to a temporary file."""
       # Implementation details
       pass
   
   def process_image(image_path, model_name, context=None):
       """Process image using the specified model."""
       # Implementation details
       pass
   ```

3. `api.py` - API endpoint definitions
   ```python
   from flask import Blueprint, request, jsonify
   import utils
   
   blueprint = Blueprint('api', __name__)
   
   @blueprint.route('/generate-alt-text', methods=['POST'])
   def generate_alt_text():
       """Generate alt text for an image URL."""
       # Implementation details
       pass
   ```

4. `config.py` - Configuration settings
   ```python
   import os
   
   # API settings
   DEBUG = os.environ.get('DEBUG', 'False') == 'True'
   PORT = int(os.environ.get('PORT', 5000))
   
   # Image processing settings
   MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
   ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
   ```

### 8.2 Modified Existing Files
Extract reusable functions from `caption.py` to be used by the web application:

1. Refactor `process_image` function to accept both local paths and downloaded images
2. Modify `verify_image_path` to handle URL validation
3. Create a new function to handle model selection and validation

## 9. Integration with Existing Code

The web application will leverage the existing functionality from `caption.py`:

1. Model loading and validation
2. Image processing and resizing
3. Caption generation using the llm CLI
4. Caption cleaning and formatting

This approach ensures we maintain the core functionality while extending it to work as a web service.