#!/usr/bin/env python3
"""
Check API Keys Status Script

This script checks the status of all configured API keys and tests connectivity.
"""

import os
from dotenv import load_dotenv

def check_api_keys():
    """Check the status of all API keys"""
    
    print("🔍 Checking API Keys Status")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv('.env.local')
    
    # Check each API key
    api_keys = {
        'OpenAI': {
            'key': os.getenv('OPENAI_API_KEY'),
            'url': 'https://api.openai.com/v1/models',
            'test_function': test_openai
        },
        'Anthropic': {
            'key': os.getenv('ANTHROPIC_API_KEY'),
            'url': 'https://api.anthropic.com/v1/messages',
            'test_function': test_anthropic
        },
        'Private GPT-4': {
            'key': os.getenv('PRIVATE_GPT4_API_KEY'),
            'url': os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'),
            'test_function': test_private_gpt4
        }
    }
    
    results = {}
    
    for provider, config in api_keys.items():
        print(f"\n📋 {provider}:")
        
        if not config['key'] or config['key'] in ['a', 'b', 'your_openai_api_key_here', 'your_anthropic_api_key_here']:
            print(f"   ❌ No valid API key configured")
            print(f"   💡 Get API key from: {get_api_key_url(provider)}")
            results[provider] = False
        else:
            print(f"   ✅ API key found: {config['key'][:10]}...")
            
            # Test connectivity
            try:
                success = config['test_function'](config['key'], config['url'])
                if success:
                    print(f"   ✅ Connection successful")
                    results[provider] = True
                else:
                    print(f"   ❌ Connection failed")
                    results[provider] = False
            except Exception as e:
                print(f"   ❌ Test failed: {str(e)}")
                results[provider] = False
    
    # Summary
    print(f"\n📊 Summary:")
    print("=" * 50)
    
    working_providers = [provider for provider, working in results.items() if working]
    
    if working_providers:
        print(f"✅ Working providers: {', '.join(working_providers)}")
        print(f"🎉 GPT-4 extraction is available!")
    else:
        print(f"❌ No working providers found")
        print(f"⚠️  GPT-4 extraction will use fallback methods")
    
    return results

def get_api_key_url(provider):
    """Get the URL to obtain API key for a provider"""
    urls = {
        'OpenAI': 'https://platform.openai.com/api-keys',
        'Anthropic': 'https://console.anthropic.com/',
        'Private GPT-4': 'Already configured (Azure)'
    }
    return urls.get(provider, 'Unknown')

def test_openai(api_key, url):
    """Test OpenAI API connectivity"""
    try:
        import openai
        openai.api_key = api_key
        # Try to list models (lightweight test)
        models = openai.models.list()
        return len(models.data) > 0
    except Exception as e:
        if "Invalid API key" in str(e):
            return False
        elif "Rate limit" in str(e):
            return True  # Rate limit means key is valid
        else:
            raise e

def test_anthropic(api_key, url):
    """Test Anthropic API connectivity"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Try to create a simple message (lightweight test)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1,
            messages=[{"role": "user", "content": "test"}]
        )
        return True
    except Exception as e:
        if "Invalid API key" in str(e):
            return False
        elif "Rate limit" in str(e):
            return True  # Rate limit means key is valid
        else:
            raise e

def test_private_gpt4(api_key, url):
    """Test Private GPT-4 API connectivity"""
    try:
        import requests
        headers = {
            'Content-Type': 'application/json',
            'api-key': api_key
        }
        data = {
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.status_code in [200, 429]  # 429 = rate limit (valid key)
    except Exception as e:
        return False

if __name__ == "__main__":
    check_api_keys() 