#!/usr/bin/env python3
"""
Test script using traditional processing to avoid GPT-4 issues
"""

import requests
import time

def test_traditional_processing():
    """Test with traditional processing to avoid GPT-4 issues"""
    
    print("🧪 Testing Traditional Processing")
    print("=" * 40)
    
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
                max_attempts = 60  # 3 minutes max
                attempts = 0
                last_progress = 0
                
                while attempts < max_attempts:
                    time.sleep(3)  # Check every 3 seconds
                    attempts += 1
                    
                    try:
                        status_response = requests.get(f'http://localhost:5001/api/processing/status/{processing_id}')
                        
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

if __name__ == "__main__":
    print("🚀 Starting Traditional Processing Test")
    print("=" * 50)
    
    success = test_traditional_processing()
    
    print("\n" + "=" * 50)
    print("📊 Test Result:")
    print(f"   Traditional Processing: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Traditional processing completed successfully!")
        print("💡 This confirms the web application works correctly without GPT-4 issues.")
    else:
        print("\n⚠️  Traditional processing test failed.") 