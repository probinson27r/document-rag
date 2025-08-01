#!/usr/bin/env python3
"""
Debug script for Private GPT-4 timeout/hanging issues
"""

import os
import time
import signal
import threading
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function timed out")

def test_private_gpt4_with_timeout(timeout_seconds=30):
    """Test Private GPT-4 with specific timeout"""
    
    print(f"🔍 Testing Private GPT-4 with {timeout_seconds}s timeout")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if not private_gpt4_key:
        print("❌ Private GPT-4 API key not found")
        return False
    
    print(f"✅ Using Private GPT-4 URL: {private_gpt4_url[:50]}...")
    print(f"✅ Using Private GPT-4 Key: {private_gpt4_key[:10]}...")
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    # Test with simple content first
    simple_data = {
        "messages": [
            {"role": "user", "content": "Say 'Hello, Private GPT-4 is working!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    print(f"\n1. Testing Simple Request ({timeout_seconds}s timeout)...")
    start_time = time.time()
    
    try:
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        response = requests.post(private_gpt4_url, headers=headers, json=simple_data, timeout=timeout_seconds)
        signal.alarm(0)  # Cancel the alarm
        
        api_time = time.time() - start_time
        print(f"⏱️  API call completed in {api_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except TimeoutError:
        print(f"❌ Request timed out after {timeout_seconds} seconds")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Requests timeout after {timeout_seconds} seconds")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_private_gpt4_with_large_content():
    """Test Private GPT-4 with larger content (simulating PDF processing)"""
    
    print(f"\n🔍 Testing Private GPT-4 with Large Content")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    # Create a larger prompt to simulate PDF processing
    large_prompt = """
    Analyze this contract document and extract key information:
    
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation on January 15, 2024.
    
    Section 1: Definitions
    1.1 "Vendor" means ABC Company, a corporation organized under the laws of Delaware
    1.2 "Client" means XYZ Corporation, a corporation organized under the laws of California
    1.3 "Services" means the IT consulting services described in Section 2
    
    Section 2: Services
    2.1 The Vendor shall provide IT consulting services to the Client
    2.2 Services shall commence on January 1, 2024 and continue for 12 months
    2.3 The total contract value is $500,000 USD
    
    Please extract the following information:
    - Contract parties
    - Contract value
    - Service duration
    - Key terms
    """
    
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert contract analyzer. Extract key information from contracts accurately."},
            {"role": "user", "content": large_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    print(f"📝 Prompt length: {len(large_prompt)} characters")
    print(f"📊 Request size: {len(str(data))} characters")
    
    # Test with different timeouts
    timeouts = [30, 60, 120]
    
    for timeout in timeouts:
        print(f"\n2. Testing Large Content Request ({timeout}s timeout)...")
        start_time = time.time()
        
        try:
            # Set up timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=timeout)
            signal.alarm(0)  # Cancel the alarm
            
            api_time = time.time() - start_time
            print(f"⏱️  API call completed in {api_time:.2f} seconds")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ Response: {content[:200]}...")
                return True
            else:
                print(f"❌ Error: {response.text}")
                
        except TimeoutError:
            print(f"❌ Request timed out after {timeout} seconds")
        except requests.exceptions.Timeout:
            print(f"❌ Requests timeout after {timeout} seconds")
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    return False

def test_gpt4_extractor_timeout():
    """Test the actual GPT4Extractor with timeout monitoring"""
    
    print(f"\n🔍 Testing GPT4Extractor with Timeout Monitoring")
    print("=" * 60)
    
    try:
        from gpt4_extraction import GPT4Extractor
        
        print("1. Initializing GPT4Extractor...")
        start_time = time.time()
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'),
            private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
        )
        
        init_time = time.time() - start_time
        print(f"✅ Extractor initialized in {init_time:.2f} seconds")
        
        # Test simple extraction
        print("\n2. Testing Simple Extraction...")
        test_text = "This is a simple test document. It contains basic information."
        
        start_time = time.time()
        
        # Set up timeout monitoring
        def extraction_with_timeout():
            try:
                return extractor.extract_structured_data(test_text, ['dates', 'names'], prefer_private_gpt4=True)
            except Exception as e:
                return {"error": str(e)}
        
        # Run with timeout
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(extraction_with_timeout)
            try:
                result = future.result(timeout=60)  # 60 second timeout
                extraction_time = time.time() - start_time
                
                print(f"⏱️  Extraction completed in {extraction_time:.2f} seconds")
                print(f"📊 Result: {result.get('success', False)}")
                
                if result.get('error'):
                    print(f"❌ Error: {result.get('error')}")
                else:
                    print("✅ Extraction successful!")
                    return True
                    
            except concurrent.futures.TimeoutError:
                print("❌ Extraction timed out after 60 seconds")
                return False
        
    except Exception as e:
        print(f"❌ Error during extractor test: {e}")
        return False

def test_connection_stability():
    """Test connection stability with multiple requests"""
    
    print(f"\n🔍 Testing Connection Stability")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "Say 'Test message'"}
        ],
        "max_tokens": 20,
        "temperature": 0.1
    }
    
    print("Testing multiple consecutive requests...")
    
    for i in range(5):
        print(f"\nRequest {i+1}/5...")
        start_time = time.time()
        
        try:
            response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
            api_time = time.time() - start_time
            
            print(f"⏱️  Request {i+1} completed in {api_time:.2f} seconds")
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ Response: {content}")
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request {i+1} failed: {e}")
        
        # Small delay between requests
        time.sleep(1)

if __name__ == "__main__":
    print("🚀 Starting Private GPT-4 Timeout Debug Tests")
    print("=" * 60)
    
    # Test simple requests with different timeouts
    simple_success = test_private_gpt4_with_timeout(30)
    
    # Test large content requests
    large_success = test_private_gpt4_with_large_content()
    
    # Test GPT4Extractor
    extractor_success = test_gpt4_extractor_timeout()
    
    # Test connection stability
    test_connection_stability()
    
    print("\n" + "=" * 60)
    print("📊 Timeout Debug Test Summary:")
    print(f"   Simple Requests: {'✅ PASS' if simple_success else '❌ FAIL'}")
    print(f"   Large Content: {'✅ PASS' if large_success else '❌ FAIL'}")
    print(f"   GPT4Extractor: {'✅ PASS' if extractor_success else '❌ FAIL'}")
    
    if simple_success and large_success and extractor_success:
        print("\n🎉 All tests passed! Private GPT-4 should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for timeout issues.") 