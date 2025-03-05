#!/usr/bin/env python3

import requests
import json
import sys
import argparse

def test_api(image_url, model=None, context=None):
    """Test the image caption API."""
    # API base URL
    base_url = "http://localhost:5001/api"
    
    # Get available models if none specified
    if not model:
        try:
            response = requests.get(f"{base_url}/models")
            models = response.json().get("models", [])
            if not models:
                print("Error: No models available")
                return
            
            # Use the first installed model
            for model_info in models:
                if model_info.get("installed", False):
                    model = model_info["name"]
                    print(f"Using model: {model}")
                    break
            
            if not model:
                print("Error: No installed models found")
                return
        except Exception as e:
            print(f"Error getting models: {str(e)}")
            return
    
    # Prepare request
    url = f"{base_url}/generate-alt-text"
    payload = {
        "image_url": image_url,
        "model": model
    }
    
    if context:
        payload["context"] = context
    
    headers = {"Content-Type": "application/json"}
    
    # Make request
    try:
        print(f"Sending request to {url}...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        print(f"\nStatus code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test the image caption API")
    parser.add_argument("image_url", help="URL of the image to process")
    parser.add_argument("--model", help="Name of the model to use")
    parser.add_argument("--context", help="Additional context for caption generation")
    
    args = parser.parse_args()
    test_api(args.image_url, args.model, args.context)

if __name__ == "__main__":
    main()