import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# API settings
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')

# Image processing settings
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
TEMP_DIR = os.environ.get('TEMP_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp'))

# Vertex AI settings
VERTEX_AI_PROJECT_ID = os.environ.get('VERTEX_AI_PROJECT_ID', '')
VERTEX_AI_REGION = os.environ.get('VERTEX_AI_REGION', 'us-central1')
VERTEX_AI_CREDENTIALS = os.environ.get('VERTEX_AI_CREDENTIALS', '')

# LiteLLM API settings
LITELLM_API_BASE_URL = os.environ.get('LITELLM_API_BASE_URL', 'https://orion.thg.dev/')
LITELLM_API_KEY = os.environ.get('LITELLM_API_KEY', 'sk-2vGUEjQmybNw4yfpx6iheQ')  # API key for authentication

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)