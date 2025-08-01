#!/usr/bin/env python3
"""
Debug Private GPT-4 API issues
"""

import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_private_gpt4_debug():
    """Debug Private GPT-4 API issues"""
    
    print("🧪 Debugging Private GPT-4 API")
    print("=" * 50)
    
    # Get environment variables
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    print(f"URL: {private_gpt4_url}")
    print(f"Key: {private_gpt4_key[:10]}..." if private_gpt4_key else "None")
    
    if not private_gpt4_url or not private_gpt4_key:
        print("❌ Missing Private GPT-4 configuration")
        return False
    
    # Test 1: Simple API call
    print("\n🔍 Test 1: Simple API Call")
    print("-" * 30)
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'api-key': private_gpt4_key,
            'Accept': 'application/json'
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, this is a test."}
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }
        
        print("📤 Sending request...")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {result}")
            return True
        else:
            print(f"❌ Error! Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.text}")
        return False
    
    print("\n🔍 Test 2: Check URL Format")
    print("-" * 30)
    
    # Check if the URL format is correct
    if "api-version" in private_gpt4_url:
        print("✅ URL contains api-version parameter")
    else:
        print("⚠️  URL missing api-version parameter")
    
    if "deployments" in private_gpt4_url:
        print("✅ URL contains deployments path")
    else:
        print("⚠️  URL missing deployments path")
    
    return False

if __name__ == "__main__":
    print("🚀 Starting Private GPT-4 Debug")
    print("=" * 60)
    
    success = test_private_gpt4_debug()
    
    print("\n" + "=" * 60)
    print("📊 Debug Result:")
    print(f"   Private GPT-4 Debug: {'✅ PASS' if success else '❌ FAIL'}") 