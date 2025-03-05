#!/usr/bin/env python3

import os
from flask import Flask, jsonify, request, send_from_directory
import config
from api import api
import utils

# Create Flask application
app = Flask(__name__)

# Register blueprints
app.register_blueprint(api, url_prefix='/api')

# Create temp directory if it doesn't exist
os.makedirs(config.TEMP_DIR, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        "name": "Image Caption API",
        "description": "Generate alt text for images using various AI models",
        "endpoints": [
            {
                "path": "/api/generate-alt-text",
                "method": "POST",
                "description": "Generate alt text for an image URL",
                "request_body": {
                    "image_url": "URL of the image to process",
                    "model": "Name of the model to use",
                    "context": "Optional context to improve caption accuracy"
                }
            },
            {
                "path": "/api/models",
                "method": "GET",
                "description": "List available models"
            },
            {
                "path": "/api/health",
                "method": "GET",
                "description": "Health check endpoint"
            }
        ]
    })

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found", "status_code": 404}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed", "status_code": 405}), 405

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error", "status_code": 500}), 500

def main():
    """Run the application."""
    # Load models to verify they're available
    models = utils.load_models()
    if not models:
        print("Warning: No models available. Make sure models.yaml is configured correctly.")
    
    # Print available models
    print("\nAvailable models:")
    for name, model_config in models.items():
        status = "✓" if model_config.get('installed', False) else "✗"
        print(f"  {status} {name} - {model_config.get('description', '')}")
    
    # Run the application
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

if __name__ == "__main__":
    main()