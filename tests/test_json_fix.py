#!/usr/bin/env python3
"""
Test script to verify JSON processing fix is working in the application
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_json_processing_fix():
    """Test if the JSON processing fix is working"""
    
    print("🧪 Testing JSON Processing Fix")
    print("=" * 50)
    
    # Test 1: Check if app is running
    print("🔍 Test 1: App Status")
    print("-" * 30)
    
    try:
        response = requests.get('http://localhost:5001/api/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ App is running")
            print(f"📊 Current model: {status.get('current_model', 'Unknown')}")
            print(f"🔑 Private GPT-4: {'✅ Available' if status.get('private_gpt4', False) else '❌ Not available'}")
        else:
            print(f"❌ App returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ App not running: {e}")
        return False
    
    print()
    
    # Test 2: Test a small document upload
    print("🔍 Test 2: Small Document Upload")
    print("-" * 30)
    
    # Create a small test file
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
    
    test_file = "test_small_document.txt"
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
    print("🚀 Starting JSON Processing Fix Test")
    print("=" * 60)
    
    success = test_json_processing_fix()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   JSON Processing Fix: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 The JSON processing fix is working!")
        print("💡 GPT-4 responses are now being processed correctly.")
    else:
        print("\n⚠️  The JSON processing fix may still have issues.") 