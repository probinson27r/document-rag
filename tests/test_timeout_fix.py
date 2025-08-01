#!/usr/bin/env python3
"""
Test script to verify timeout fix and processing completion
"""

import requests
import time
import signal
import threading

def test_with_timeout():
    """Test with a shorter timeout to see if processing completes"""
    
    print("🧪 Testing Timeout Fix")
    print("=" * 40)
    
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
                
                # Monitor processing progress with shorter timeout
                max_attempts = 40  # 2 minutes max
                attempts = 0
                last_progress = 0
                stuck_count = 0
                
                while attempts < max_attempts:
                    time.sleep(3)  # Check every 3 seconds
                    attempts += 1
                    
                    try:
                        status_response = requests.get(f'http://localhost:5001/api/processing/status/{processing_id}')
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            current_progress = status['progress']
                            
                            # Check if progress is stuck
                            if current_progress == last_progress:
                                stuck_count += 1
                                if stuck_count > 10:  # Stuck for 30 seconds
                                    print(f"⚠️  Progress stuck at {current_progress}% for 30 seconds")
                                    print(f"📊 Current status: {status['message']}")
                                    break
                            else:
                                stuck_count = 0
                            
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
                
                print("⏰ Processing timeout or stuck")
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
    print("🚀 Starting Timeout Fix Test")
    print("=" * 50)
    
    success = test_with_timeout()
    
    print("\n" + "=" * 50)
    print("📊 Test Result:")
    print(f"   Timeout Fix: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Processing completed without getting stuck!")
    else:
        print("\n⚠️  Processing still getting stuck or timing out.") 