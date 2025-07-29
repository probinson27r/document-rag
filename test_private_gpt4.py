#!/usr/bin/env python3
"""
Test script for Private GPT-4 integration
"""

import os
import requests
import json

def test_private_gpt4_connection():
    """Test the private GPT-4 API connection"""
    
    # Get API key from environment
    api_key = os.getenv('PRIVATE_GPT4_API_KEY')
    if not api_key:
        print("❌ PRIVATE_GPT4_API_KEY not found in environment variables")
        return False
    
    # Private GPT-4 configuration
    base_url = 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    
    payload = {
        'model': 'gpt-4o',
        'messages': [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please respond with 'Private GPT-4 is working correctly!'"}
        ],
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    try:
        print("🔗 Testing Private GPT-4 connection...")
        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"✅ Private GPT-4 connection successful!")
            print(f"📝 Response: {answer}")
            return True
        else:
            print(f"❌ Private GPT-4 API error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Private GPT-4: {e}")
        return False

def test_app_integration():
    """Test if the app can initialize with Private GPT-4"""
    try:
        print("\n🔧 Testing app integration...")
        
        # Import app components
        from app import initialize_rag_system, private_gpt4_client
        
        # Initialize the system
        success = initialize_rag_system()
        
        if success and private_gpt4_client:
            print("✅ App integration successful - Private GPT-4 client initialized")
            return True
        elif success:
            print("⚠️  App initialized but Private GPT-4 client not available (check API key)")
            return False
        else:
            print("❌ App initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing app integration: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 PRIVATE GPT-4 INTEGRATION TEST")
    print("=" * 50)
    
    # Test 1: Direct API connection
    api_test = test_private_gpt4_connection()
    
    # Test 2: App integration
    app_test = test_app_integration()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"API Connection: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"App Integration: {'✅ PASS' if app_test else '❌ FAIL'}")
    
    if api_test and app_test:
        print("\n🎉 All tests passed! Private GPT-4 integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
    
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Set your API key: export PRIVATE_GPT4_API_KEY='your-key-here'")
    print("2. Restart the Flask app: python app.py")
    print("3. The 'Private GPT-4' model should appear in the model selection dropdown")

if __name__ == "__main__":
    main() 