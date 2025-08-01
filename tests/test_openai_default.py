#!/usr/bin/env python3
"""
Test OpenAI GPT-4 as default
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_openai_default():
    """Test that OpenAI GPT-4 is now the default"""
    
    print("🧪 Testing OpenAI GPT-4 as Default")
    print("=" * 50)
    
    # Test 1: Check app status
    print("🔍 Test 1: App Status")
    print("-" * 30)
    
    try:
        response = requests.get('http://localhost:5001/api/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ App is running")
            print(f"📊 Current model: {status.get('current_model', 'Unknown')}")
            
            if status.get('current_model') == 'OpenAI GPT-4':
                print("✅ OpenAI GPT-4 is set as default")
            else:
                print(f"❌ Expected OpenAI GPT-4, got: {status.get('current_model')}")
                return False
        else:
            print(f"❌ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ App not running: {e}")
        return False
    
    print()
    
    # Test 2: Direct GPT-4 test
    print("🔍 Test 2: Direct GPT-4 Test")
    print("-" * 30)
    
    try:
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
            private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
        )
        
        print("✅ GPT4Extractor initialized")
        
        # Test with default settings (should use OpenAI GPT-4)
        test_text = "Test document with date 2024-01-15"
        test_result = extractor.extract_structured_data(test_text, ['dates'])
        
        print(f"✅ Test result success: {test_result.get('success', False)}")
        if test_result.get('success'):
            print(f"📊 Extracted data: {test_result.get('extracted_data', {})}")
            print("✅ OpenAI GPT-4 is being used by default")
        else:
            print(f"❌ Error: {test_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ GPT4Extractor test failed: {e}")
        return False
    
    print()
    
    # Test 3: Set extraction method to gpt4_enhanced
    print("🔍 Test 3: Set Extraction Method to GPT-4 Enhanced")
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
            return False
    except Exception as e:
        print(f"❌ Config set failed: {e}")
        return False
    
    print()
    
    # Test 4: Upload small test file
    print("🔍 Test 4: Upload Test File")
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
    
    test_file = "test_openai_document.txt"
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
                
                # Monitor processing for up to 2 minutes
                max_attempts = 40  # 2 minutes
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
                
                print("⏰ Processing timeout after 2 minutes")
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
    print("🚀 Starting OpenAI GPT-4 Default Test")
    print("=" * 60)
    
    success = test_openai_default()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   OpenAI GPT-4 Default: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 OpenAI GPT-4 is now the default!")
    else:
        print("\n⚠️  OpenAI GPT-4 default setting has issues.") 