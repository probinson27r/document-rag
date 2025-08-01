#!/usr/bin/env python3
"""
Test script for web application async upload processing
"""

import requests
import time
import json

def test_async_upload():
    """Test the async upload functionality"""
    
    print("🧪 Testing Web Application Async Upload")
    print("=" * 50)
    
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
                max_attempts = 60  # 1 minute
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

def test_processing_cleanup():
    """Test the processing cleanup endpoint"""
    
    print("\n🧹 Testing Processing Cleanup")
    print("=" * 30)
    
    try:
        response = requests.post('http://localhost:5001/api/processing/cleanup')
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cleanup result: {result}")
            return True
        else:
            print(f"❌ Cleanup failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Web Application Tests")
    print("=" * 50)
    
    # Test async upload
    upload_success = test_async_upload()
    
    # Test cleanup
    cleanup_success = test_processing_cleanup()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Async Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"   Cleanup: {'✅ PASS' if cleanup_success else '❌ FAIL'}")
    
    if upload_success and cleanup_success:
        print("\n🎉 All tests passed! Web application is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 