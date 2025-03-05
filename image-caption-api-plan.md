# Implementation Plan: Adding THG Provider Support with LiteLLM API

Based on my analysis of the codebase, I've developed a plan to add support for locally installed models available through the LiteLLM API hosted at https://thgai.io.thehut.local/. This will allow the image captioning system to route requests to this service when the provider is "THG".

## Current System Architecture

The image captioning system currently supports multiple providers:
- Standard models via the `llm` CLI command
- VertexAI models via the Google Cloud API
- Each provider has its own processing function and routing logic

## Implementation Steps

### 1. Add LiteLLM API Configuration to config.py

Add the following configuration variables to config.py:

```python
# LiteLLM API settings
LITELLM_API_BASE_URL = os.environ.get('LITELLM_API_BASE_URL', 'https://thgai.io.thehut.local/')
LITELLM_API_KEY = os.environ.get('LITELLM_API_KEY', '')  # API key for authentication
```

### 2. Create a New Function in utils.py

Create a new function `process_image_url_with_litellm` in utils.py that:
- Downloads the image from the URL
- Converts the image to base64
- Sends a request to the LiteLLM API with the image and prompt
- Processes the response and returns the caption

```python
def process_image_url_with_litellm(image_url, model_name, context=None, prompt=None, debug=False):
    """Process an image from URL with LiteLLM API.
    
    Args:
        image_url (str): URL of the image to process
        model_name (str): Name of the model to use
        context (str, optional): Additional context for caption generation
        prompt (str, optional): Custom prompt to use instead of the one in model_config
        debug (bool, optional): Whether to print debug information
        
    Returns:
        dict: Result containing the generated caption and metadata
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
    
    # Resize large images
    small_image = resize_image(image_path)
    
    try:
        # Convert image to base64
        with open(small_image, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Use provided prompt or fall back to model_config prompt
        prompt_text = prompt or model_config["prompt"]
        if context:
            prompt_text = f"Consider this context before analyzing the image: {context}\n\n{prompt_text}"
        
        if debug and prompt:
            print(f"Using custom prompt instead of model prompt")
        
        # Prepare the request payload for LiteLLM API
        payload = {
            "model": model_config["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": model_config.get("settings", {}).get("max_tokens", 75),
            "temperature": model_config.get("settings", {}).get("temperature", 0.1)
        }
        
        # Add any additional model-specific settings
        for key, value in model_config.get("settings", {}).items():
            if key not in ["max_tokens", "temperature"]:
                payload[key] = value
        
        if debug:
            print("\n" + "="*80)
            print(f"Model: {model_config['model']}")
            print(f"Image: {image_path}")
            print(f"Using LiteLLM API: {config.LITELLM_API_BASE_URL}")
            print("-"*80)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key and service account if provided
        if config.LITELLM_API_KEY:
            headers["Authorization"] = f"Bearer {config.LITELLM_API_KEY}"
        
        # Send request to LiteLLM API
        response = requests.post(
            f"{config.LITELLM_API_BASE_URL.rstrip('/')}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Parse response
        result_json = response.json()
        
        # Extract the caption
        raw_caption = result_json["choices"][0]["message"]["content"]
        caption = clean_caption(raw_caption)
        
        execution_time = round(time.time() - start_time, 1)
        
        if debug:
            print(f"Generated caption with LiteLLM API ({execution_time}s):")
            print(f"  Raw: {raw_caption}")
            print(f"  Clean: {caption}")
            print("="*80)
        
        result = {
            "caption": caption,
            "time": execution_time
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error communicating with LiteLLM API: {str(e)}"
        if debug:
            print(error_msg, file=sys.stderr)
        result = {"caption": error_msg, "error": True}
    except Exception as e:
        error_msg = str(e)
        if debug:
            print(f"Error processing image with LiteLLM API: {error_msg}", file=sys.stderr)
        result = {"caption": error_msg, "error": True}
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if small_image != image_path and os.path.exists(small_image):
                os.remove(small_image)
        except:
            pass
    
    # Add metadata
    total_time = round(time.time() - start_time, 1)
    
    # Get the original provider from the model config
    original_provider = model_config.get("provider", "unknown")
    
    response = {
        "image_url": image_url,
        "model": model_name,
        "provider": "thg",  # Override provider to show it was processed by THG
        "original_provider": original_provider,  # Include the original provider for reference
        "processing_time": total_time
    }
    
    if "error" in result and result["error"]:
        response["error"] = result["caption"]
    else:
        response["alt_text"] = result["caption"]
        response["model_time"] = result["time"]
    
    return response
```

### 3. Update the API Route in api.py

Modify the `generate_alt_text` function in api.py to route requests to the new function when the provider is "thg":

```python
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
```

### 4. Add Example THG Models to models.yaml

Add example THG model configurations to models.yaml:

```yaml
claude-3-sonnet-thg:
  deployment: local
  description: Claude 3 Sonnet (THG)
  model: claude-3-sonnet
  prompt: You are a helpful alt-text generator assisting visually impaired users. Generate a clear and concise caption (10-20 words) that highlights the most important subject and action. Focus only on essential details, avoiding unnecessary background elements. Use simple, everyday language and avoid overly descriptive or poetic words, and avoid website names.
  provider: thg
  settings:
    max_tokens: 75
    temperature: 0.1

llama-3-70b-thg:
  deployment: local
  description: Llama 3 70B (THG)
  model: llama-3-70b
  prompt: You are a helpful alt-text generator assisting visually impaired users. Generate a clear and concise caption (10-20 words) that highlights the most important subject and action. Focus only on essential details, avoiding unnecessary background elements. Use simple, everyday language and avoid overly descriptive or poetic words, and avoid website names.
  provider: thg
  settings:
    max_tokens: 75
    temperature: 0.1
```

### 5. Update mock_utils.py (Optional)

Update the `mock_process_image_url` function in mock_utils.py to handle THG models:

```python
# Mock providers based on model name
providers = {
    "chatgpt-4o-latest": "openai",
    "claude-3-sonnet": "anthropic",
    "llava-13b": "ollama",
    "pixtral-12b": "mistral",
    "gemini-pro-vision": "vertexai",
    "claude-3-sonnet-thg": "thg",
    "llama-3-70b-thg": "thg"
}
```

### 6. Testing Plan

1. Add a THG model to models.yaml
2. Set the LITELLM_API_BASE_URL environment variable
3. Test the API with a request specifying a THG model
4. Verify that the request is routed to the LiteLLM API
5. Verify that the response contains the expected caption

## Questions for Consideration

1. Does the LiteLLM API require authentication? If so, we'll need to add an API key configuration.
2. What is the exact format of the LiteLLM API request and response? We'll need to adapt our implementation accordingly.
3. Are there any specific error handling requirements for the LiteLLM API?
4. Should we add any additional configuration options for the THG provider?

## Implementation Notes

- The LiteLLM API implementation assumes a standard OpenAI-compatible API format. If the API has a different format, the implementation will need to be adjusted.
- Error handling is implemented to catch and report any issues with the LiteLLM API.
- The implementation includes debug logging to help troubleshoot any issues.
- The implementation preserves the original provider in the response metadata.