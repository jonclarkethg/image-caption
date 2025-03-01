"""Mock utilities for testing the API without actual LLM calls."""

import time
import random
import uuid
import os
from pathlib import Path
import config

def mock_download_image(url):
    """Mock function to simulate downloading an image."""
    print(f"Mock: Downloading image from {url}")
    time.sleep(0.5)  # Simulate network delay
    
    # Create a unique filename with a fake extension
    filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join(config.TEMP_DIR, filename)
    
    # Create an empty file
    Path(temp_path).touch()
    
    return temp_path

def mock_process_image_url(image_url, model_name, context=None, debug=False):
    """Mock function to simulate processing an image URL."""
    start_time = time.time()
    
    # Simulate processing delay
    processing_time = random.uniform(1.5, 3.0)
    time.sleep(processing_time)
    
    # Generate a mock caption based on the model
    captions = {
        "chatgpt-4o-latest": "A fluffy orange cat with bright green eyes looking directly at the camera.",
        "claude-3-sonnet": "Orange tabby cat with green eyes in close-up portrait.",
        "llava-13b": "Cat with orange fur staring at viewer.",
        "pixtral-12b": "Close-up of an orange tabby cat with striking green eyes."
    }
    
    # Use the caption for the specified model, or a default one
    alt_text = captions.get(model_name, "A close-up photograph of an orange cat.")
    
    # Add context influence if provided
    if context and "dog" in context.lower():
        alt_text = alt_text.replace("cat", "dog").replace("tabby", "golden")
    
    # Calculate total time
    total_time = round(time.time() - start_time, 1)
    
    return {
        "image_url": image_url,
        "alt_text": alt_text,
        "model": model_name,
        "processing_time": total_time,
        "model_time": processing_time
    }