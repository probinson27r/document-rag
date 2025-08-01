#!/usr/bin/env python3
"""
Test script to directly test GPT-4 extraction and identify why it's timing out
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from gpt4_extraction import GPT4Extractor

def test_gpt4_extraction():
    """Test GPT-4 extraction directly"""
    
    print("🧪 Testing GPT-4 Extraction Directly")
    print("=" * 50)
    
    # Initialize the extractor
    extractor = GPT4Extractor(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        private_gpt4_url=os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'),
        private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
    )
    
    # Test text
    test_text = """
    This is a test document for GPT-4 extraction.
    It contains some sample text to test the extraction capabilities.
    The document includes dates like 2024-01-15 and amounts like $1,000.
    """
    
    print("📝 Test text:")
    print(test_text.strip())
    print()
    
    # Test 1: Simple text enhancement
    print("🔍 Test 1: Text Enhancement")
    print("-" * 30)
    start_time = time.time()
    
    try:
        result = extractor.enhance_text_extraction(test_text, '.txt', prefer_private_gpt4=True)
        end_time = time.time()
        
        print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("📄 Enhanced text:")
            print(result['extracted_data'].get('enhanced_text', 'No enhanced text'))
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        end_time = time.time()
        print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        print(f"❌ Exception: {e}")
    
    print()
    
    # Test 2: Structured data extraction
    print("🔍 Test 2: Structured Data Extraction")
    print("-" * 30)
    start_time = time.time()
    
    try:
        result = extractor.extract_structured_data(test_text, ['dates', 'amounts'], prefer_private_gpt4=True)
        end_time = time.time()
        
        print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('success'):
            print("📊 Extracted data:")
            print(result['extracted_data'])
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        end_time = time.time()
        print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
        print(f"❌ Exception: {e}")
    
    print()
    
    # Test 3: Direct API call with timeout
    print("🔍 Test 3: Direct API Call with Timeout")
    print("-" * 30)
    
    if extractor.private_gpt4_url and extractor.private_gpt4_key:
        headers = {
            'Content-Type': 'application/json',
            'api-key': extractor.private_gpt4_key
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, this is a test' and nothing else."}
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(extractor.private_gpt4_url, headers=headers, json=data, timeout=30)
            end_time = time.time()
            
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            print(f"📡 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ Response: {content}")
            else:
                print(f"❌ Error response: {response.text}")
                
        except requests.exceptions.Timeout:
            end_time = time.time()
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            print("❌ Request timed out after 30 seconds")
        except Exception as e:
            end_time = time.time()
            print(f"⏱️  Time taken: {end_time - start_time:.2f} seconds")
            print(f"❌ Exception: {e}")
    else:
        print("❌ Private GPT-4 not configured")

if __name__ == "__main__":
    print("🚀 Starting GPT-4 Extraction Test")
    print("=" * 60)
    
    test_gpt4_extraction()
    
    print("\n" + "=" * 60)
    print("📊 Test Complete")
    print("💡 This will help identify why GPT-4 is timing out during processing.") 