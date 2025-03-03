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
        "context": "Optional context to improve caption accuracy"
    }
    
    Query parameters:
    vertexai=true - Use Vertex AI for processing instead of the default model provider
    
    Returns:
    {
        "image_url": "https://example.com/image.jpg",
        "alt_text": "Generated alt text for the image.",
        "model": "chatgpt-4o-latest",
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
        debug = data.get('debug', False)
        
        # Check if Vertex AI should be used
        use_vertexai = request.args.get('vertexai', '').lower() == 'true'
        
        # Process image (use mock in test mode)
        if MOCK_MODE:
            print(f"Using mock mode for processing: {image_url}")
            result = mock_utils.mock_process_image_url(image_url, model, context, debug)
        elif use_vertexai:
            print(f"Using Vertex AI for processing: {image_url}")
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
        ],
        "vertex_ai_enabled": true/false
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
        
        # Add Vertex AI enabled flag
        response = {
            "models": model_list,
            "vertex_ai_enabled": config.VERTEX_AI_PROJECT_ID != '' and config.VERTEX_AI_REGION != ''
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