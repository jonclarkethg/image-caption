from flask import Blueprint, request, jsonify
import utils
import mock_utils
import traceback
import os

# Create blueprint
api = Blueprint('api', __name__)

# Determine if we should use mock mode (for testing without API keys)
MOCK_MODE = os.environ.get('MOCK_MODE', 'False').lower() == 'true'

@api.route('/generate-alt-text', methods=['POST'])
def generate_alt_text():
    """Generate alt text for an image URL."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON", "status_code": 400}), 400

        if 'image_url' not in data:
            return jsonify({"error": "Missing required field: image_url", "status_code": 400}), 400
        if 'model' not in data:
            return jsonify({"error": "Missing required field: model", "status_code": 400}), 400

        image_url = data['image_url']
        model = data['model']
        context = data.get('context')
        prompt = data.get('prompt')
        debug = data.get('debug', False)

        if MOCK_MODE:
            print(f"Using mock mode for processing: {image_url}")
            result = mock_utils.mock_process_image_url(image_url, model, context, debug)
        else:
            models = utils.load_models()
            if not models:
                return jsonify({"error": "No models available", "status_code": 500}), 500

            if model not in models:
                return jsonify({"error": f"Model '{model}' not found", "status_code": 400}), 400

            result = utils.process_image_url(image_url, model, context, prompt, debug)

        if 'error' in result:
            return jsonify({"error": result['error'], "status_code": 400}), 400

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({"error": str(e), "status_code": 400}), 400
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "status_code": 500}), 500

@api.route('/models', methods=['GET'])
def list_models():
    """List available models."""
    try:
        if MOCK_MODE:
            model_list = [
                {"name": "gemini-2.0-flash-lite", "description": "Gemini 2.0 Flash Lite", "provider": "google", "installed": True},
                {"name": "gemini-2.0-flash", "description": "Gemini 2.0 Flash", "provider": "google", "installed": True},
            ]
        else:
            models = utils.load_models()
            model_list = []
            for name, model_conf in models.items():
                model_list.append({
                    "name": name,
                    "description": model_conf.get('description', ''),
                    "provider": "google",
                    "installed": model_conf.get('installed', True)
                })

        return jsonify({"models": model_list}), 200

    except Exception as e:
        print(f"Error listing models: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "status_code": 500}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200
