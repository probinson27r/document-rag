#!/usr/bin/env python3
"""
Simple test script for web application - uses traditional processing
"""

import requests
import time
import json

def test_simple_upload():
    """Test upload with traditional processing"""
    
    print("🧪 Testing Web Application - Simple Upload")
    print("=" * 50)
    
    # First, set extraction method to traditional
    print("📝 Setting extraction method to traditional...")
    try:
        config_response = requests.post('http://localhost:5001/api/extraction/config', 
                                      json={
                                          'extraction_method': 'traditional',
                                          'gpt4_model': 'gpt-4o'
                                      })
        if config_response.status_code == 200:
            print("✅ Extraction method set to traditional")
        else:
            print(f"❌ Failed to set extraction method: {config_response.status_code}")
            error_data = config_response.json()
            print(f"Error details: {error_data}")
            return False
    except Exception as e:
        print(f"❌ Error setting extraction method: {e}")
        return False
    
    # Test file upload
    test_file = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    try:
        print(f"📤 Uploading file: {test_file}")
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:5001/upload', files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload response: {result}")
            
            if 'processing_id' in result:
                processing_id = result['processing_id']
                print(f"🔄 Processing ID: {processing_id}")
                
                # Monitor processing progress
                max_attempts = 30  # 1 minute
                attempts = 0
                
                while attempts < max_attempts:
                    time.sleep(2)  # Check every 2 seconds
                    attempts += 1
                    
                    try:
                        status_response = requests.get(f'http://localhost:5001/api/processing/status/{processing_id}')
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            print(f"📊 Status: {status['status']} - {status['message']} ({status['progress']}%)")
                            
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
                
                print("⏰ Processing timeout")
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

def test_api_endpoints():
    """Test basic API endpoints"""
    
    print("\n🔍 Testing API Endpoints")
    print("=" * 30)
    
    endpoints = [
        ('/api/status', 'GET'),
        ('/api/models', 'GET'),
        ('/api/extraction/config', 'GET'),
        ('/api/extraction/status', 'GET'),
        ('/api/documents', 'GET')
    ]
    
    all_passed = True
    
    for endpoint, method in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f'http://localhost:5001{endpoint}')
            else:
                response = requests.post(f'http://localhost:5001{endpoint}')
            
            if response.status_code == 200:
                print(f"✅ {method} {endpoint}")
            else:
                print(f"❌ {method} {endpoint} - {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Starting Simple Web Application Tests")
    print("=" * 50)
    
    # Test API endpoints first
    api_success = test_api_endpoints()
    
    # Test simple upload
    upload_success = test_simple_upload()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Simple Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    
    if api_success and upload_success:
        print("\n🎉 All tests passed! Web application is working correctly.")
        print("💡 The Private GPT-4 connection issues are separate from the web app functionality.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 