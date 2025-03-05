"""
Vertex AI utilities for image captioning.

This module provides functions for interacting with Google Cloud's Vertex AI
to generate captions for images.
"""

import os
import time
import base64
from google.cloud import aiplatform
from PIL import Image
import io
import config
import utils

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

def get_image_mime_type(image_path):
    """Detect the MIME type of an image file.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: MIME type of the image (e.g., "image/jpeg", "image/png")
    """
    # Use PIL to open the image and determine its format
    with Image.open(image_path) as img:
        fmt = img.format.lower() if img.format else "jpeg"
        
        # Map common formats to MIME types
        mime_map = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "tiff": "image/tiff"
        }
        
        return mime_map.get(fmt, "image/jpeg")  # Default to JPEG if unknown

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
        
        # Get the model name from the configuration
        model_name = model_config.get("model")
        provider = model_config.get("provider", "").lower()
        use_anthropic_vertex = model_config.get("use_anthropic_vertex", False)
        
        if debug:
            print(f"Processing with Vertex AI model: {model_name}")
            print(f"Provider: {provider}")
            print(f"Use Anthropic Vertex: {use_anthropic_vertex}")
        
        # Handle different model types
        if provider == "vertexai":
            # For Claude models using Anthropic Vertex
            if use_anthropic_vertex:
                try:
                    from anthropic import AnthropicVertex
                    
                    # Initialize AnthropicVertex client
                    client = AnthropicVertex(
                        project_id=config.VERTEX_AI_PROJECT_ID,
                        region=config.VERTEX_AI_REGION,
                    )
                    
                    # Prepare the prompt
                    prompt = model_config["prompt"]
                    if context:
                        prompt = f"Consider this context before analyzing the image: {context}\n\n{prompt}"
                    
                    # Load the image and convert to base64
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                        base64_encoded = base64.b64encode(image_data).decode("utf-8")
                    
                    # Detect the image MIME type
                    mime_type = get_image_mime_type(image_path)
                    
                    if debug:
                        print(f"Detected image MIME type: {mime_type}")
                    
                    # Generate content using AnthropicVertex
                    response = client.messages.create(
                        model=model_name,
                        max_tokens=model_config.get("settings", {}).get("max_tokens", 75),
                        temperature=model_config.get("settings", {}).get("temperature", 0.1),
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": mime_type,
                                            "data": base64_encoded
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                    
                    # Extract the caption
                    raw_caption = response.content[0].text
                    
                    # Clean the caption
                    caption = utils.clean_caption(raw_caption)
                    
                    execution_time = round(time.time() - start_time, 1)
                    
                    if debug:
                        print(f"Generated caption with AnthropicVertex ({execution_time}s):")
                        print(f"  Raw: {raw_caption}")
                        print(f"  Clean: {caption}")
                    
                    return {
                        "caption": caption,
                        "time": execution_time
                    }
                except ImportError:
                    raise ValueError("AnthropicVertex library not installed. Install with: pip install -U 'anthropic[vertex]'")
                except Exception as e:
                    raise ValueError(f"Error using AnthropicVertex: {str(e)}")
            
            # For Gemini models
            elif "gemini" in model_name.lower():
                from vertexai.generative_models import GenerativeModel, Part
                
                # Load the model
                model = GenerativeModel(model_name)
                
                # Prepare the prompt
                prompt = model_config["prompt"]
                if context:
                    prompt = f"Consider this context before analyzing the image: {context}\n\n{prompt}"
                
                # Detect the image MIME type
                mime_type = get_image_mime_type(image_path)
                
                if debug:
                    print(f"Detected image MIME type: {mime_type}")
                
                # Load the image
                with Image.open(image_path) as img:
                    # Convert to RGB if needed (for JPEG format)
                    if mime_type == "image/jpeg" and img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    # Get the format from the MIME type
                    format_str = mime_type.split('/')[1].upper()
                    if format_str == "JPG":
                        format_str = "JPEG"
                    
                    # Convert to bytes, preserving the original format when possible
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=format_str)
                    img_bytes = img_byte_arr.getvalue()
                
                # Generate content
                response = model.generate_content(
                    [prompt, Part.from_data(img_bytes, mime_type)],
                    generation_config={
                        "max_output_tokens": model_config.get("settings", {}).get("max_tokens", 75),
                        "temperature": model_config.get("settings", {}).get("temperature", 0.1),
                        "top_p": model_config.get("settings", {}).get("top_p", 0.7),
                    }
                )
                
                # Extract the caption
                raw_caption = response.text.strip()
                
                # Clean the caption
                caption = utils.clean_caption(raw_caption)
                
                execution_time = round(time.time() - start_time, 1)
                
                if debug:
                    print(f"Generated caption with Vertex AI ({execution_time}s):")
                    print(f"  Raw: {raw_caption}")
                    print(f"  Clean: {caption}")
                
                return {
                    "caption": caption,
                    "time": execution_time
                }
            # Add support for other Vertex AI models here
            # elif "palm" in model_name.lower():
            #     # Implementation for PaLM models
            #     pass
            else:
                raise ValueError(f"Unsupported Vertex AI model: {model_name}")
        else:
            # If the model is not a Vertex AI model, we'll try to use it with Vertex AI anyway
            # This allows users to specify any model in the request
            try:
                from vertexai.generative_models import GenerativeModel, Part
                
                # Default to gemini-pro-vision if the model is not specified
                vertex_model_name = "gemini-pro-vision"
                
                if debug:
                    print(f"Model {model_name} is not a Vertex AI model. Using {vertex_model_name} instead.")
                
                # Load the model
                model = GenerativeModel(vertex_model_name)
                
                # Prepare the prompt
                prompt = model_config["prompt"]
                if context:
                    prompt = f"Consider this context before analyzing the image: {context}\n\n{prompt}"
                
                # Detect the image MIME type
                mime_type = get_image_mime_type(image_path)
                
                if debug:
                    print(f"Detected image MIME type: {mime_type}")
                
                # Load the image
                with Image.open(image_path) as img:
                    # Convert to RGB if needed (for JPEG format)
                    if mime_type == "image/jpeg" and img.mode != "RGB":
                        img = img.convert("RGB")
                    
                    # Get the format from the MIME type
                    format_str = mime_type.split('/')[1].upper()
                    if format_str == "JPG":
                        format_str = "JPEG"
                    
                    # Convert to bytes, preserving the original format when possible
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=format_str)
                    img_bytes = img_byte_arr.getvalue()
                
                # Generate content
                response = model.generate_content(
                    [prompt, Part.from_data(img_bytes, mime_type)],
                    generation_config={
                        "max_output_tokens": model_config.get("settings", {}).get("max_tokens", 75),
                        "temperature": model_config.get("settings", {}).get("temperature", 0.1),
                        "top_p": model_config.get("settings", {}).get("top_p", 0.7),
                    }
                )
                
                # Extract the caption
                raw_caption = response.text.strip()
                
                # Clean the caption
                caption = utils.clean_caption(raw_caption)
                
                execution_time = round(time.time() - start_time, 1)
                
                if debug:
                    print(f"Generated caption with Vertex AI ({execution_time}s):")
                    print(f"  Raw: {raw_caption}")
                    print(f"  Clean: {caption}")
                
                return {
                    "caption": caption,
                    "time": execution_time
                }
            except Exception as e:
                raise ValueError(f"Failed to use model with Vertex AI: {str(e)}")
            
    except Exception as e:
        error_msg = str(e)
        if debug:
            print(f"Error processing image with Vertex AI: {error_msg}")
        return {"caption": error_msg, "error": True}