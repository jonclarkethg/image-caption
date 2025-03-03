import os
import requests
import tempfile
import uuid
from pathlib import Path
from PIL import Image
import yaml
import subprocess
import sys
import time
from urllib.parse import urlparse

import config

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
    
    # Check file extension
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    # Some URLs might not have a file extension (e.g., dynamic content)
    # In this case, we'll validate the content type after downloading
    extension = os.path.splitext(path)[1][1:] if os.path.splitext(path)[1] else ""
    
    # If no extension or unknown extension, we'll check the content type later
    return extension == "" or extension in config.ALLOWED_EXTENSIONS

def download_image(url):
    """Download image from URL to a temporary file.
    
    Args:
        url (str): URL of the image to download
        
    Returns:
        str: Path to the downloaded image
        
    Raises:
        ValueError: If the URL is invalid or the image cannot be downloaded
    """
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL format: {url}")
    
    try:
        # Download the image
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image: {content_type}")
        
        # Check file size
        if int(response.headers.get('Content-Length', 0)) > config.MAX_IMAGE_SIZE:
            raise ValueError(f"Image is too large (max size: {config.MAX_IMAGE_SIZE} bytes)")
        
        # Determine file extension from content type
        extension = '.jpg'  # Default extension
        if content_type == 'image/png':
            extension = '.png'
        elif content_type == 'image/gif':
            extension = '.gif'
        elif content_type == 'image/webp':
            extension = '.webp'
        elif content_type == 'image/jpeg' or content_type == 'image/jpg':
            extension = '.jpg'
        
        # Create a unique filename
        filename = f"{uuid.uuid4()}{extension}"
        temp_path = os.path.join(config.TEMP_DIR, filename)
        
        # Save the image
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return temp_path
    
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading image: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing image URL: {str(e)}")

def load_models():
    """Load models from models.yaml and check their status."""
    try:
        # Load config
        config_path = Path(__file__).parent / "models.yaml"
        with open(config_path) as f:
            models = yaml.safe_load(f)
            
        # Get installed models from CLI
        result = subprocess.run(["llm", "models"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running 'llm models': {result.stderr}")
            raise Exception("Failed to get model list")
            
        # Parse output to get installed models
        installed_models = set()
        for line in result.stdout.split('\n'):
            if ':' in line:
                _, model_part = line.split(':', 1)
                # Take the first part before any aliases
                model_id = model_part.split('(')[0].strip().lower()
                if model_id:
                    installed_models.add(model_id)
        
        # Check each model's status
        for name, config in models.items():
            model_id = config['model'].lower()
            config['installed'] = model_id in installed_models
            config['configured'] = True  # If llm models works, assume configured
            
        return models
        
    except FileNotFoundError:
        print("Error: models.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing models.yaml: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking model status: {e}")
        return {}

def validate_model(model_name, models):
    """Validate that the requested model exists and is installed."""
    if model_name not in models:
        raise ValueError(f"Model '{model_name}' not found")
    
    model_config = models[model_name]
    #if not model_config.get('installed', False):
        #raise ValueError(f"Model '{model_name}' is not installed")
    
    return model_config

def resize_image(image_path, max_dimension=1024):
    """Return path to a resized image for LLM processing."""
    path = Path(image_path)
    with Image.open(path) as img:
        # Return original path if image is small enough
        if max(img.size) <= max_dimension:
            return image_path
            
        # Resize while preserving aspect ratio
        img.thumbnail((max_dimension, max_dimension))
        
        # Create temp file path with original extension
        temp_path = Path(config.TEMP_DIR) / f"resized-{path.name}"
        
        # Save resized image to temp location
        img.save(temp_path, optimize=True)
        return str(temp_path)

def clean_caption(caption):
    """Clean caption by extracting first sentence and removing image references."""
    # Implementation from caption.py
    import re
    
    # First remove any surrounding whitespace and quotes
    caption = caption.strip().strip("\"'")

    # Extract the first sentence
    first_sentence = caption.split(".")[0].strip()

    # Define patterns for image-related subjects and verbs
    subjects = r"image|photo|photograph|picture|scene"
    verbs = r"shows|showcases|depicts|displays|features|contains|captures|presents"

    # Match "This is an image of..." at the start
    pattern1 = rf"^This is an? ({subjects}) of\s+"
    first_sentence = re.sub(pattern1, "", first_sentence)

    # Match "This image shows..." or similar at the start
    pattern2 = rf"^(?:This|The)\s*(?:{subjects})\s*(?:{verbs})\s+"
    first_sentence = re.sub(pattern2, "", first_sentence)

    # Final cleanup and capitalize
    first_sentence = first_sentence.strip().strip("\"'")
    if first_sentence:
        first_sentence = first_sentence[0].upper() + first_sentence[1:]

    return first_sentence + "."

def run_llm_command(image_path, model_config, context=None, debug=False):
    """Run llm command for a specific model and return the result."""
    start_time = time.time()
    
    try:
        # Base command
        cmd = ["llm", "-m", model_config["model"]]
        
        # Add attachment for image
        cmd.extend(["-a", str(image_path)])
        
        # Build prompt with context if provided
        prompt = model_config["prompt"]
        if context:
            prompt = f"Consider this context before analyzing the image: {context}\n\n{prompt}"
        
        # Add prompt to command
        cmd.append(prompt)
        
        # Add any model-specific settings
        if "settings" in model_config:
            for key, value in model_config["settings"].items():
                cmd.extend(["-o", key, str(value)])
        
        if debug:
            print("\n" + "="*80)
            print(f"Model: {model_config['model']}")
            print(f"Image: {image_path}")
            print("-"*80)
            
            # Build and show the exact command with settings
            settings_str = ""
            if "settings" in model_config:
                settings_str = " " + " ".join(f"-o {k} {v}" for k, v in model_config["settings"].items())
            print(f"Command:")
            print(f"  llm -m {model_config['model']} -a {image_path}{settings_str}")
            print("-"*80)
            
            print("Prompt details:")
            if context:
                print("  Context provided:")
                print(f"    {context}")
            if "settings" in model_config:
                print("  Settings:")
                for key, value in model_config["settings"].items():
                    print(f"    {key}: {value}")
            print("-"*80)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        execution_time = round(time.time() - start_time, 1)
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        
        raw_caption = result.stdout.strip()
        caption = clean_caption(raw_caption)
        
        if debug:
            print(f"Generated caption ({execution_time}s):")
            print(f"  Raw: {raw_caption}")
            print(f"  Clean: {caption}")
            print("="*80)
        
        return {
            "caption": caption,
            "time": execution_time
        }
        
    except subprocess.CalledProcessError as e:
        if debug:
            print(e.stderr, file=sys.stderr)
        return {"caption": e.stderr.strip(), "error": True}
    except Exception as e:
        error_msg = str(e)
        if debug:
            print(error_msg, file=sys.stderr)
        return {"caption": error_msg, "error": True}

def process_image_url(image_url, model_name, context=None, debug=False):
    """Process an image from URL with the specified model.
    
    Args:
        image_url (str): URL of the image to process
        model_name (str): Name of the model to use
        context (str, optional): Additional context for caption generation
        debug (bool, optional): Whether to print debug information
        
    Returns:
        dict: Result containing the generated caption and metadata
        
    Raises:
        ValueError: If the image URL is invalid or the model is not available
    """
    start_time = time.time()
    
    # Load models
    models = load_models()
    if not models:
        raise ValueError("No models available")
    
    # Validate model
    model_config = validate_model(model_name, models)
    
    # Download image
    image_path = download_image(image_url)
    
    # Resize large images to reduce upload bandwidth to cloud LLMs
    small_image = resize_image(image_path)
    
    # Process image
    result = run_llm_command(small_image, model_config, context, debug)
    
    # Add metadata
    total_time = round(time.time() - start_time, 1)
    
    response = {
        "image_url": image_url,
        "model": model_name,
        "provider": model_config.get("provider", "unknown"),
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
    
    # Get the original provider from the model config
    original_provider = model_config.get("provider", "unknown")
    
    response = {
        "image_url": image_url,
        "model": model_name,
        "provider": "vertexai",  # Override provider to show it was processed by Vertex AI
        "original_provider": original_provider,  # Include the original provider for reference
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