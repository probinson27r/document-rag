#!/usr/bin/env python3
"""
Test large document processing with improved batch processing
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_large_document():
    """Test processing a large document with improved batch processing"""
    
    print("🧪 Testing Large Document Processing")
    print("=" * 50)
    
    # Test 1: Set extraction method to gpt4_enhanced
    print("🔍 Test 1: Set Extraction Method to GPT-4 Enhanced")
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
    
    # Test 2: Upload PDF file
    print("🔍 Test 2: Upload Large PDF File")
    print("-" * 30)
    
    pdf_file = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return False
    
    try:
        print(f"📤 Uploading PDF file: {pdf_file}")
        start_time = time.time()
        
        with open(pdf_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:5001/upload', files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload response: {result}")
            
            if 'processing_id' in result:
                processing_id = result['processing_id']
                print(f"🔄 Processing ID: {processing_id}")
                
                # Monitor processing for up to 10 minutes
                max_attempts = 200  # 10 minutes
                attempts = 0
                last_progress = 0
                gpt4_start_time = None
                
                while attempts < max_attempts:
                    time.sleep(3)  # Check every 3 seconds
                    attempts += 1
                    
                    try:
                        status_response = requests.get(f'http://localhost:5001/api/processing/status/{processing_id}', timeout=10)
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            current_progress = status['progress']
                            message = status['message']
                            
                            # Track when GPT-4 processing starts
                            if 'batch processing' in message.lower() and gpt4_start_time is None:
                                gpt4_start_time = time.time()
                                print(f"⏱️  GPT-4 batch processing started at {gpt4_start_time - start_time:.1f}s")
                            
                            # Only print if progress changed
                            if current_progress != last_progress:
                                elapsed = time.time() - start_time
                                print(f"📊 Progress: {current_progress}% - {message} (elapsed: {elapsed:.1f}s)")
                                last_progress = current_progress
                            
                            if status['status'] == 'completed':
                                total_time = time.time() - start_time
                                print(f"✅ Processing completed successfully in {total_time:.1f} seconds!")
                                print(f"📄 Result: {status['result']}")
                                
                                # Check if it used GPT-4
                                extraction_method = status['result'].get('extraction_method', '')
                                if 'gpt4' in extraction_method.lower():
                                    print("🎉 GPT-4 batch processing was used successfully!")
                                    print(f"📊 Extraction method: {extraction_method}")
                                    
                                    if gpt4_start_time:
                                        gpt4_time = time.time() - gpt4_start_time
                                        print(f"⚡ GPT-4 processing took: {gpt4_time:.1f} seconds")
                                    
                                    return True
                                else:
                                    print("⚠️  Traditional processing was used")
                                    return False
                            elif status['status'] == 'error':
                                print(f"❌ Processing failed: {status['error']}")
                                return False
                        else:
                            print(f"❌ Failed to get status: {status_response.status_code}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error checking status: {e}")
                        return False
                
                print("⏰ Processing timeout after 10 minutes")
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
    print("🚀 Starting Large Document Test")
    print("=" * 60)
    
    success = test_large_document()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   Large Document Processing: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Large document processing is working with improved batch processing!")
    else:
        print("\n⚠️  Large document processing still has issues.") 