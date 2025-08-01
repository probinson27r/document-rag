#!/usr/bin/env python3
"""
Comprehensive test to debug GPT-4 processing in the application
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_gpt4_processing_debug():
    """Debug GPT-4 processing issues"""
    
    print("🧪 Debugging GPT-4 Processing")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("🔍 Test 1: Environment Variables")
    print("-" * 30)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    print(f"PRIVATE_GPT4_URL: {'✅ Set' if private_gpt4_url else '❌ Not set'}")
    print(f"PRIVATE_GPT4_API_KEY: {'✅ Set' if private_gpt4_key else '❌ Not set'}")
    
    if private_gpt4_url:
        print(f"URL: {private_gpt4_url[:50]}...")
    if private_gpt4_key:
        print(f"Key: {private_gpt4_key[:10]}...")
    
    print()
    
    # Test 2: Direct GPT-4 test
    print("🔍 Test 2: Direct GPT-4 Test")
    print("-" * 30)
    
    try:
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        print("✅ GPT4Extractor initialized")
        
        # Test the exact same test that the app uses
        test_text = "Test document with date 2024-01-15"
        test_result = extractor.extract_structured_data(test_text, ['dates'])
        
        print(f"✅ Test result success: {test_result.get('success', False)}")
        if test_result.get('success'):
            print(f"📊 Extracted data: {test_result.get('extracted_data', {})}")
        else:
            print(f"❌ Error: {test_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ GPT4Extractor test failed: {e}")
    
    print()
    
    # Test 3: App status
    print("🔍 Test 3: App Status")
    print("-" * 30)
    
    try:
        response = requests.get('http://localhost:5001/api/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ App is running")
            print(f"📊 Current model: {status.get('current_model', 'Unknown')}")
        else:
            print(f"❌ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ App not running: {e}")
        return False
    
    print()
    
    # Test 4: Extraction configuration
    print("🔍 Test 4: Extraction Configuration")
    print("-" * 30)
    
    try:
        response = requests.get('http://localhost:5001/api/extraction/config', timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Extraction method: {config.get('extraction_method', 'Unknown')}")
            print(f"✅ GPT-4 model: {config.get('gpt4_model', 'Unknown')}")
            print(f"✅ Features: {config.get('features', {})}")
        else:
            print(f"❌ Failed to get config: {response.status_code}")
    except Exception as e:
        print(f"❌ Config test failed: {e}")
    
    print()
    
    # Test 5: Set extraction method to gpt4_enhanced
    print("🔍 Test 5: Set Extraction Method to GPT-4 Enhanced")
    print("-" * 30)
    
    try:
        config_data = {
            'extraction_method': 'gpt4_enhanced',
            'gpt4_model': 'gpt-4o',
            'features': {
                'text_enhancement': True,
                'structured_data': True,
                'contract_analysis': True,
                'document_summary': False
            }
        }
        
        response = requests.post('http://localhost:5001/api/extraction/config', 
                               json=config_data, timeout=5)
        if response.status_code == 200:
            print("✅ Extraction method set to gpt4_enhanced")
        else:
            print(f"❌ Failed to set config: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Config set failed: {e}")
    
    print()
    
    # Test 6: Upload with GPT-4 enhanced processing
    print("🔍 Test 6: Upload with GPT-4 Enhanced Processing")
    print("-" * 30)
    
    # Create a test file
    test_content = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation.
    
    Effective Date: January 1, 2024
    Contract Value: $500,000
    
    Section 1: Services
    The vendor shall provide IT consulting services.
    
    Section 2: Payment Terms
    Payment shall be made within 30 days of invoice.
    """
    
    test_file = "test_gpt4_document.txt"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        print(f"📤 Uploading test file: {test_file}")
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:5001/upload', files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload response: {result}")
            
            if 'processing_id' in result:
                processing_id = result['processing_id']
                print(f"🔄 Processing ID: {processing_id}")
                
                # Monitor processing for up to 3 minutes
                max_attempts = 60  # 3 minutes
                attempts = 0
                last_progress = 0
                
                while attempts < max_attempts:
                    time.sleep(3)  # Check every 3 seconds
                    attempts += 1
                    
                    try:
                        status_response = requests.get(f'http://localhost:5001/api/processing/status/{processing_id}', timeout=10)
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            current_progress = status['progress']
                            
                            # Only print if progress changed
                            if current_progress != last_progress:
                                print(f"📊 Progress: {current_progress}% - {status['message']}")
                                last_progress = current_progress
                            
                            if status['status'] == 'completed':
                                print("✅ Processing completed successfully!")
                                print(f"📄 Result: {status['result']}")
                                
                                # Check if it used GPT-4
                                if 'gpt4' in status['result'].get('extraction_method', '').lower():
                                    print("🎉 GPT-4 processing was used successfully!")
                                else:
                                    print("⚠️  Traditional processing was used")
                                
                                return True
                            elif status['status'] == 'error':
                                print(f"❌ Processing failed: {status['error']}")
                                return False
                        else:
                            print(f"❌ Failed to get status: {status_response.status_code}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error checking status: {e}")
                        return False
                
                print("⏰ Processing timeout after 3 minutes")
                return False
            else:
                print("✅ Immediate upload success")
                return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    print("🚀 Starting GPT-4 Processing Debug Test")
    print("=" * 60)
    
    success = test_gpt4_processing_debug()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   GPT-4 Processing Debug: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 GPT-4 processing is working correctly!")
    else:
        print("\n⚠️  GPT-4 processing still has issues.") 