from flask import Blueprint, request, jsonify
import utils
import mock_utils
import config
import traceback
import os

# Create blueprint
api = Blueprint('api', __name__)

# Determine if we should use mock mode (for testing without API keys)
MOCK_MODE = os.environ.get('MOCK_MODE', 'False').lower() == 'true'

@api.route('/generate-alt-text', methods=['POST'])
def generate_alt_text():
    """Generate alt text for an image URL.
    
    Request body:
    {
        "image_url": "https://example.com/image.jpg",
        "model": "chatgpt-4o-latest",
        "context": "Optional context to improve caption accuracy",
        "prompt": "Optional custom prompt to use instead of the default prompt"
    }
    
    Returns:
    {
        "image_url": "https://example.com/image.jpg",
        "alt_text": "Generated alt text for the image.",
        "model": "chatgpt-4o-latest",
        "provider": "openai",
        "processing_time": 2.5
    }
    
    Error response:
    {
        "error": "Error message",
        "status_code": 400
    }
    """
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
        prompt = data.get('prompt')
        debug = data.get('debug', False)
        
        # Process image (use mock in test mode)
        if MOCK_MODE:
            print(f"Using mock mode for processing: {image_url}")
            result = mock_utils.mock_process_image_url(image_url, model, context, debug)
        else:
            # Load models to check the provider
            models = utils.load_models()
            if not models:
                return jsonify({"error": "No models available", "status_code": 500}), 500
            
            # Check if the model exists
            if model not in models:
                return jsonify({"error": f"Model '{model}' not found", "status_code": 400}), 400
            
            # Get the provider from the model config
            provider = models[model].get("provider", "").lower()
            
            # Use Vertex AI if the provider is "vertexai"
            if provider == "vertexai":
                print(f"Using Vertex AI for processing: {image_url} (provider: {provider})")
                result = utils.process_image_url_with_vertexai(image_url, model, context, prompt, debug)
            # Use LiteLLM API if the provider is "thg"
            elif provider == "thg":
                print(f"Using LiteLLM API for processing: {image_url} (provider: {provider})")
                result = utils.process_image_url_with_litellm(image_url, model, context, prompt, debug)
            else:
                result = utils.process_image_url(image_url, model, context, prompt, debug)
        
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

@api.route('/models', methods=['GET'])
def list_models():
    """List available models.
    
    Returns:
    {
        "models": [
            {
                "name": "chatgpt-4o-latest",
                "description": "GPT-4 with Vision",
                "provider": "openai",
                "installed": true
            },
            ...
        ]
    }
    """
    try:
        if MOCK_MODE:
            # Return mock model data
            model_list = [
                {
                    "name": "chatgpt-4o-latest",
                    "description": "GPT-4 with Vision",
                    "provider": "openai",
                    "deployment": "cloud",
                    "installed": True
                },
                {
                    "name": "claude-3-sonnet",
                    "description": "Claude 3 Sonnet",
                    "provider": "anthropic",
                    "deployment": "cloud",
                    "installed": True
                },
                {
                    "name": "llava-13b",
                    "description": "LLaVA (13B)",
                    "provider": "ollama",
                    "deployment": "local",
                    "installed": True
                },
                {
                    "name": "pixtral-12b",
                    "description": "Pixtral 12B",
                    "provider": "mistral",
                    "deployment": "cloud",
                    "installed": True
                },
                {
                    "name": "gemini-pro-vision",
                    "description": "Gemini Pro Vision",
                    "provider": "vertexai",
                    "deployment": "cloud",
                    "installed": config.VERTEX_AI_PROJECT_ID != ''
                }
            ]
        else:
            # Load real models
            models = utils.load_models()
            
            # Format response
            model_list = []
            for name, config in models.items():
                # For Vertex AI models, check if project ID is set
                installed = config.get('installed', False)
                if config.get('provider') == 'vertexai':
                    installed = installed and config.VERTEX_AI_PROJECT_ID != ''
                
                model_list.append({
                    "name": name,
                    "description": config.get('description', ''),
                    "provider": config.get('provider', 'unknown'),
                    "deployment": config.get('deployment', 'unknown'),
                    "installed": installed
                })
        
        # Create response
        response = {
            "models": model_list
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        # Log the full error
        print(f"Error listing models: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "status_code": 500}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    
    Returns:
    {
        "status": "ok"
    }
    """
    return jsonify({"status": "ok"}), 200