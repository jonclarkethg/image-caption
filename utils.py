import os
import ssl
import requests
import uuid
from pathlib import Path
from PIL import Image
import yaml
import sys
import time
from urllib.parse import urlparse

from google import genai

import config

# Initialize google-genai client
_client = None

def _ssl_verify():
    """Build the TLS verification setting for outbound google-genai (httpx) calls.

    httpx ignores REQUESTS_CA_BUNDLE and SSL_CERT_FILE (unlike requests) and uses
    certifi's bundle, which does not include corporate TLS-interception CAs such as
    Netskope. Honour those variables explicitly, falling back to httpx's default.
    """
    for var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        path = os.environ.get(var)
        if path and os.path.isfile(path):
            return ssl.create_default_context(cafile=path)
    return True

def get_client():
    global _client
    if _client is None:
        verify = _ssl_verify()
        _client = genai.Client(
            api_key=config.GOOGLE_API_KEY,
            http_options=genai.types.HttpOptions(
                client_args={"verify": verify},
                async_client_args={"verify": verify},
            ),
        )
    return _client

def is_valid_url(url):
    """Check if the provided URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_image_url(url):
    """Check if the URL points to a valid image."""
    if not is_valid_url(url):
        return False

    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    extension = os.path.splitext(path)[1][1:] if os.path.splitext(path)[1] else ""
    return extension == "" or extension in config.ALLOWED_EXTENSIONS

def download_image(url):
    """Download image from URL to a temporary file."""
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL format: {url}")

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image: {content_type}")

        if int(response.headers.get('Content-Length', 0)) > config.MAX_IMAGE_SIZE:
            raise ValueError(f"Image is too large (max size: {config.MAX_IMAGE_SIZE} bytes)")

        extension = '.jpg'
        if content_type == 'image/png':
            extension = '.png'
        elif content_type == 'image/gif':
            extension = '.gif'
        elif content_type == 'image/webp':
            extension = '.webp'
        elif content_type in ('image/jpeg', 'image/jpg'):
            extension = '.jpg'

        filename = f"{uuid.uuid4()}{extension}"
        temp_path = os.path.join(config.TEMP_DIR, filename)

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return temp_path

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading image: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing image URL: {str(e)}")

def load_models():
    """Load models from models.yaml."""
    try:
        config_path = Path(__file__).parent / "models.yaml"
        with open(config_path) as f:
            models = yaml.safe_load(f)

        for name, model_conf in models.items():
            model_conf['installed'] = True

        return models

    except FileNotFoundError:
        print("Error: models.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing models.yaml: {e}")
        sys.exit(1)

def validate_model(model_name, models):
    """Validate that the requested model exists."""
    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found")
    return models[model_name]

def resize_image(image_path, max_dimension=1024):
    """Return path to a resized image for LLM processing."""
    path = Path(image_path)
    with Image.open(path) as img:
        if max(img.size) <= max_dimension:
            return image_path

        img.thumbnail((max_dimension, max_dimension))
        temp_path = Path(config.TEMP_DIR) / f"resized-{path.name}"
        img.save(temp_path, optimize=True)
        return str(temp_path)

def clean_caption(caption):
    """Clean caption by extracting first sentence and removing image references."""
    import re

    caption = caption.strip().strip("\"'")
    first_sentence = caption.split(".")[0].strip()

    subjects = r"image|photo|photograph|picture|scene"
    verbs = r"shows|showcases|depicts|displays|features|contains|captures|presents"

    pattern1 = rf"^This is an? ({subjects}) of\s+"
    first_sentence = re.sub(pattern1, "", first_sentence)

    pattern2 = rf"^(?:This|The)\s*(?:{subjects})\s*(?:{verbs})\s+"
    first_sentence = re.sub(pattern2, "", first_sentence)

    first_sentence = first_sentence.strip().strip("\"'")
    if first_sentence:
        first_sentence = first_sentence[0].upper() + first_sentence[1:]

    return first_sentence + "."

def get_image_mime_type(image_path):
    """Detect the MIME type of an image file."""
    with Image.open(image_path) as img:
        fmt = img.format.lower() if img.format else "jpeg"
        mime_map = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        return mime_map.get(fmt, "image/jpeg")

def calculate_cost(usage, pricing):
    """Calculate cost from usage metadata and model pricing.

    Args:
        usage: response.usage_metadata from google-genai
        pricing (dict): Pricing config with input_per_million, output_per_million, cached_input_per_million

    Returns:
        dict: Cost breakdown with input_tokens, output_tokens, thinking_tokens, cached_tokens, total_cost
    """
    input_tokens = usage.prompt_token_count or 0
    output_tokens = usage.candidates_token_count or 0
    thinking_tokens = getattr(usage, 'thoughts_token_count', None) or 0
    cached_tokens = getattr(usage, 'cached_content_token_count', None) or 0

    input_rate = pricing.get("input_per_million", 0)
    output_rate = pricing.get("output_per_million", 0)
    cached_rate = pricing.get("cached_input_per_million", 0)

    non_cached_input = max(input_tokens - cached_tokens, 0)

    input_cost = (non_cached_input / 1_000_000) * input_rate
    cached_cost = (cached_tokens / 1_000_000) * cached_rate
    output_cost = ((output_tokens + thinking_tokens) / 1_000_000) * output_rate
    total_cost = input_cost + cached_cost + output_cost

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "cached_tokens": cached_tokens,
        "total_cost": round(total_cost, 8)
    }

def generate_caption(image_path, model_config, context=None, prompt=None, debug=False):
    """Generate a caption for an image using google-genai.

    Args:
        image_path (str): Path to the image file
        model_config (dict): Model configuration from models.yaml
        context (str, optional): Additional context for caption generation
        prompt (str, optional): Custom prompt override
        debug (bool, optional): Whether to print debug information

    Returns:
        dict: Result with 'caption' and 'time', or 'caption' and 'error'
    """
    start_time = time.time()

    try:
        model_name = model_config["model"]

        prompt_text = prompt or model_config["prompt"]
        if context:
            prompt_text = f"Consider this context before analyzing the image: {context}\n\n{prompt_text}"

        # Read image bytes and detect mime type
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        mime_type = get_image_mime_type(image_path)

        image_part = genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        settings = model_config.get("settings", {})

        if debug:
            print(f"\nModel: {model_name}")
            print(f"Image: {image_path}")
            print(f"MIME type: {mime_type}")

        client = get_client()
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt_text, image_part],
            config={
                "max_output_tokens": settings.get("max_output_tokens", 75),
                "temperature": settings.get("temperature", 0.1),
            }
        )

        raw_caption = response.text.strip()
        caption = clean_caption(raw_caption)

        execution_time = round(time.time() - start_time, 1)

        # Calculate cost from usage metadata
        cost_info = calculate_cost(response.usage_metadata, model_config.get("pricing", {}))

        if debug:
            print(f"Generated caption ({execution_time}s):")
            print(f"  Raw: {raw_caption}")
            print(f"  Clean: {caption}")
            print(f"  Cost: ${cost_info['total_cost']:.6f}")

        return {
            "caption": caption,
            "time": execution_time,
            "cost": cost_info
        }

    except Exception as e:
        error_msg = str(e)
        if debug:
            print(f"Error generating caption: {error_msg}")
        return {"caption": error_msg, "error": True}

def resolve_image(image_source):
    """Resolve an image source to a local file path.

    Supports:
        - file:///path/to/image.jpg — local file path
        - http(s)://... — remote URL (downloaded to temp)

    Returns:
        tuple: (image_path, is_temporary) — is_temporary indicates if the file should be cleaned up
    """
    if image_source.startswith("file://"):
        local_path = image_source[7:]  # strip file://
        if not os.path.isfile(local_path):
            raise ValueError(f"Local file not found: {local_path}")
        return local_path, False
    else:
        return download_image(image_source), True

def process_image_url(image_url, model_name, context=None, prompt=None, debug=False):
    """Process an image from a URL or local file path with the specified model.

    Args:
        image_url (str): URL (http/https) or local path (file://) of the image
        model_name (str): Name of the model to use
        context (str, optional): Additional context for caption generation
        prompt (str, optional): Custom prompt override
        debug (bool, optional): Whether to print debug information

    Returns:
        dict: Result containing the generated caption and metadata
    """
    start_time = time.time()

    models = load_models()
    if not models:
        raise ValueError("No models available")

    model_config = validate_model(model_name, models)

    image_path, is_temporary = resolve_image(image_url)
    small_image = resize_image(image_path)

    result = generate_caption(small_image, model_config, context, prompt, debug)

    total_time = round(time.time() - start_time, 1)

    response = {
        "image_url": image_url,
        "model": model_name,
        "provider": "google",
        "processing_time": total_time
    }

    if "error" in result and result["error"]:
        response["error"] = result["caption"]
    else:
        response["alt_text"] = result["caption"]
        response["model_time"] = result["time"]
        if "cost" in result:
            response["cost"] = result["cost"]

    try:
        if is_temporary and os.path.exists(image_path):
            os.remove(image_path)
        if small_image != image_path and os.path.exists(small_image):
            os.remove(small_image)
    except:
        pass

    return response
