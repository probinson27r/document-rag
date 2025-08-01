#!/usr/bin/env python3
"""
Test GPT-4 processing with PDF files
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_pdf_gpt4_processing():
    """Test GPT-4 processing with PDF files"""
    
    print("🧪 Testing GPT-4 Processing with PDF")
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
    print("🔍 Test 2: Upload PDF File")
    print("-" * 30)
    
    pdf_file = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        return False
    
    try:
        print(f"📤 Uploading PDF file: {pdf_file}")
        
        with open(pdf_file, 'rb') as f:
            files = {'file': f}
            response = requests.post('http://localhost:5001/upload', files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload response: {result}")
            
            if 'processing_id' in result:
                processing_id = result['processing_id']
                print(f"🔄 Processing ID: {processing_id}")
                
                # Monitor processing for up to 5 minutes
                max_attempts = 100  # 5 minutes
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
                                extraction_method = status['result'].get('extraction_method', '')
                                if 'gpt4' in extraction_method.lower():
                                    print("🎉 GPT-4 processing was used successfully!")
                                    print(f"📊 Extraction method: {extraction_method}")
                                    return True
                                else:
                                    print("⚠️  Traditional processing was used")
                                    print(f"📊 Extraction method: {extraction_method}")
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
                
                print("⏰ Processing timeout after 5 minutes")
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
    print("🚀 Starting PDF GPT-4 Processing Test")
    print("=" * 60)
    
    success = test_pdf_gpt4_processing()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   PDF GPT-4 Processing: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 GPT-4 processing is working correctly with PDF files!")
    else:
        print("\n⚠️  GPT-4 processing still has issues with PDF files.") 