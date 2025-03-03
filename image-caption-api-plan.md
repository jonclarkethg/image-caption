# Plan for Adding Vertex AI Support to Image Caption API

## Current Application Overview

The image captioning application is a Flask-based API that generates alt text for images using various AI models. The application currently supports models from OpenAI, Anthropic, Ollama, and Mistral, with both cloud-based and local deployment options.

Key components:
- `api.py`: API endpoints for generating alt text, listing models, and health check
- `app.py`: Main Flask application
- `utils.py`: Utility functions for image processing and model interaction
- `caption.py`: CLI tool for generating captions
- `config.py`: Application configuration
- `models.yaml`: Model configurations

The application uses the `llm` CLI tool to interact with models, which provides a consistent interface across different model providers.

## Requirements for Vertex AI Integration

1. Add support for Google Cloud's Vertex AI using the Python SDK
2. Enable Vertex AI when "vertexai=true" is added as a query string parameter
3. Use the provided project ID, region, and credentials file for authentication

## Implementation Plan

### 1. Install Required Dependencies

Add the Vertex AI Python SDK to the project:
```
google-cloud-aiplatform
```

### 2. Update Configuration

1. Add Vertex AI configuration to `config.py`:
   - Project ID
   - Region
   - Credentials file path
   - Default model (e.g., Gemini Pro Vision)

2. Add Vertex AI model configuration to `models.yaml`:
   - Add a new model entry for Gemini Pro Vision
   - Include provider, description, and settings

### 3. Implement Vertex AI Integration

1. Create a new module `vertex_utils.py` for Vertex AI specific functionality:
   - Authentication with Google Cloud
   - Image processing for Vertex AI
   - Caption generation using Vertex AI models

2. Update `api.py` to check for the "vertexai=true" query parameter:
   - Extract the parameter from the request
   - Route the request to Vertex AI processing if the parameter is present

3. Update `utils.py` to integrate with Vertex AI:
   - Add a new function to process images with Vertex AI
   - Ensure compatibility with the existing processing flow

### 4. Update Model Listing

1. Update the `/api/models` endpoint to include Vertex AI models:
   - Add Vertex AI models to the response
   - Include provider information

### 5. Testing

1. Test the integration with sample images
2. Verify that the "vertexai=true" parameter correctly routes to Vertex AI
3. Compare results between existing models and Vertex AI models

### 6. Documentation

1. Update API documentation to include Vertex AI support
2. Document the "vertexai=true" query parameter
3. Add information about Vertex AI models to the model listing

## Detailed Implementation Steps

### Step 1: Install Dependencies

Add the Vertex AI SDK to `requirements.txt`:
```
google-cloud-aiplatform>=1.36.0
```

### Step 2: Update Configuration

Add Vertex AI configuration to `config.py`:
```python
# Vertex AI settings
VERTEX_AI_ENABLED = os.environ.get('VERTEX_AI_ENABLED', 'False').lower() == 'true'
VERTEX_AI_PROJECT_ID = os.environ.get('VERTEX_AI_PROJECT_ID', '')
VERTEX_AI_REGION = os.environ.get('VERTEX_AI_REGION', 'us-central1')
VERTEX_AI_CREDENTIALS = os.environ.get('VERTEX_AI_CREDENTIALS', '')
```

Add Vertex AI model to `models.yaml`:
```yaml
gemini-pro-vision:
  deployment: cloud
  description: Gemini Pro Vision
  model: gemini-pro-vision
  prompt: You are a helpful alt-text generator assisting visually impaired users. Generate a clear and concise caption (10-20 words) that highlights the most important subject and action. Focus only on essential details, avoiding unnecessary background elements. Use simple, everyday language and avoid overly descriptive or poetic words.
  provider: vertexai
  settings:
    max_tokens: 75
    temperature: 0.1
```

### Step 3: Create Vertex AI Utilities

Create a new file `vertex_utils.py`:
```python
import os
import time
import base64
from google.cloud import aiplatform
from PIL import Image
import io
import config

def initialize_vertexai():
    """Initialize Vertex AI with project and location."""
    # Set credentials if provided
    if config.VERTEX_AI_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.VERTEX_AI_CREDENTIALS
    
    # Initialize Vertex AI
    aiplatform.init(
        project=config.VERTEX_AI_PROJECT_ID,
        location=config.VERTEX_AI_REGION,
    )

def image_to_base64(image_path):
    """Convert image to base64 for Vertex AI."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def process_image_with_vertexai(image_path, model_config, context=None, debug=False):
    """Process an image using Vertex AI.
    
    Args:
        image_path (str): Path to the image file
        model_config (dict): Model configuration
        context (str, optional): Additional context for caption generation
        debug (bool, optional): Whether to print debug information
        
    Returns:
        dict: Result containing the generated caption and metadata
    """
    start_time = time.time()
    
    try:
        # Initialize Vertex AI
        initialize_vertexai()
        
        # Get the model
        model_name = model_config.get("model", "gemini-pro-vision")
        
        # For Gemini models
        if "gemini" in model_name:
            from vertexai.generative_models import GenerativeModel, Part
            
            # Load the model
            model = GenerativeModel(model_name)
            
            # Prepare the prompt
            prompt = model_config["prompt"]
            if context:
                prompt = f"Consider this context before analyzing the image: {context}\n\n{prompt}"
            
            # Load the image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
            
            # Generate content
            response = model.generate_content(
                [prompt, Part.from_data(img_bytes, "image/jpeg")],
                generation_config={
                    "max_output_tokens": model_config.get("settings", {}).get("max_tokens", 75),
                    "temperature": model_config.get("settings", {}).get("temperature", 0.1),
                    "top_p": model_config.get("settings", {}).get("top_p", 0.7),
                }
            )
            
            # Extract the caption
            raw_caption = response.text.strip()
            
            # Clean the caption
            from utils import clean_caption
            caption = clean_caption(raw_caption)
            
            execution_time = round(time.time() - start_time, 1)
            
            if debug:
                print(f"Generated caption with Vertex AI ({execution_time}s):")
                print(f"  Raw: {raw_caption}")
                print(f"  Clean: {caption}")
            
            return {
                "caption": caption,
                "time": execution_time
            }
        else:
            raise ValueError(f"Unsupported Vertex AI model: {model_name}")
            
    except Exception as e:
        error_msg = str(e)
        if debug:
            print(f"Error processing image with Vertex AI: {error_msg}")
        return {"caption": error_msg, "error": True}
```

### Step 4: Update API to Support Vertex AI

Update `api.py` to check for the "vertexai=true" query parameter:
```python
@api.route('/generate-alt-text', methods=['POST'])
def generate_alt_text():
    """Generate alt text for an image URL."""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON", "status_code": 400}), 400
        
        # Validate required fields
        if 'image_url' not in data:
            return jsonify({"error": "Missing required field: image_url", "status_code": 400}), 400
        if 'model' not in data:
            return jsonify({"error": "Missing required field: model", "status_code": 400}), 400
        
        # Extract fields
        image_url = data['image_url']
        model = data['model']
        context = data.get('context')
        debug = data.get('debug', False)
        
        # Check if Vertex AI should be used
        use_vertexai = request.args.get('vertexai', '').lower() == 'true'
        
        # Process image
        if MOCK_MODE:
            print(f"Using mock mode for processing: {image_url}")
            result = mock_utils.mock_process_image_url(image_url, model, context, debug)
        elif use_vertexai:
            # Import here to avoid circular imports
            import vertex_utils
            result = utils.process_image_url_with_vertexai(image_url, model, context, debug)
        else:
            result = utils.process_image_url(image_url, model, context, debug)
        
        # Check for errors
        if 'error' in result:
            return jsonify({"error": result['error'], "status_code": 400}), 400
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": str(e), "status_code": 400}), 400
    except Exception as e:
        # Log the full error
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "status_code": 500}), 500
```

### Step 5: Update Utils to Support Vertex AI

Add a new function to `utils.py` for processing images with Vertex AI:
```python
def process_image_url_with_vertexai(image_url, model_name, context=None, debug=False):
    """Process an image from URL with Vertex AI.
    
    Args:
        image_url (str): URL of the image to process
        model_name (str): Name of the model to use
        context (str, optional): Additional context for caption generation
        debug (bool, optional): Whether to print debug information
        
    Returns:
        dict: Result containing the generated caption and metadata
    """
    start_time = time.time()
    
    # Import Vertex AI utilities
    import vertex_utils
    
    # Load models
    models = load_models()
    if not models:
        raise ValueError("No models available")
    
    # Validate model
    model_config = validate_model(model_name, models)
    
    # Download image
    image_path = download_image(image_url)
    
    # Resize large images
    small_image = resize_image(image_path)
    
    # Process image with Vertex AI
    result = vertex_utils.process_image_with_vertexai(small_image, model_config, context, debug)
    
    # Add metadata
    total_time = round(time.time() - start_time, 1)
    
    response = {
        "image_url": image_url,
        "model": model_name,
        "processing_time": total_time
    }
    
    if "error" in result and result["error"]:
        response["error"] = result["caption"]
    else:
        response["alt_text"] = result["caption"]
        response["model_time"] = result["time"]
    
    # Clean up temporary files
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
        if small_image != image_path and os.path.exists(small_image):
            os.remove(small_image)
    except:
        pass
    
    return response
```

## Testing and Verification

After implementing the changes, we should test the integration with:

1. A request without the "vertexai=true" parameter (should use the existing flow)
2. A request with the "vertexai=true" parameter (should use Vertex AI)
3. Different models to ensure compatibility

## Conclusion

This plan outlines the steps needed to add Vertex AI support to the image captioning application. The implementation will maintain compatibility with the existing codebase while adding the new functionality as requested.

The key aspects of this integration are:
1. Using the Vertex AI Python SDK for model interaction
2. Supporting the "vertexai=true" query parameter
3. Maintaining the same response format for consistency