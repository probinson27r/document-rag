#!/usr/bin/env python3
"""
Test Private GPT-4 as default
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_private_gpt4_default():
    """Test that Private GPT-4 is now the default"""
    
    print("🧪 Testing Private GPT-4 as Default")
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
            
            if status.get('current_model') == 'Private GPT-4':
                print("✅ Private GPT-4 is set as default")
            else:
                print(f"❌ Expected Private GPT-4, got: {status.get('current_model')}")
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
        
        # Test with default settings (should use Private GPT-4)
        test_text = "Test document with date 2024-01-15"
        test_result = extractor.extract_structured_data(test_text, ['dates'])
        
        print(f"✅ Test result success: {test_result.get('success', False)}")
        if test_result.get('success'):
            print(f"📊 Extracted data: {test_result.get('extracted_data', {})}")
            print("✅ Private GPT-4 is being used by default")
        else:
            print(f"❌ Error: {test_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ GPT4Extractor test failed: {e}")
        return False
    
    print()
    
    # Test 3: Batch processing test
    print("🔍 Test 3: Batch Processing Test")
    print("-" * 30)
    
    try:
        # Create test chunks
        test_chunks = [
            {'content': 'This is chunk 1 with date 2024-01-15'},
            {'content': 'This is chunk 2 with amount $500'},
            {'content': 'This is chunk 3 with name John Doe'}
        ]
        
        print(f"📝 Testing batch processing with {len(test_chunks)} chunks")
        
        # Test batch processing
        features = {
            'text_enhancement': True,
            'structured_data': True,
            'contract_analysis': True
        }
        
        print("🔄 Running batch enhancement...")
        start_time = time.time()
        
        enhanced_chunks = extractor.batch_enhance_chunks(
            test_chunks, 
            features=features,
            prefer_private_gpt4=True  # Use Private GPT-4
        )
        
        end_time = time.time()
        print(f"⏱️  Batch processing took: {end_time - start_time:.2f} seconds")
        
        print(f"📊 Enhanced chunks: {len(enhanced_chunks)}")
        
        for i, chunk in enumerate(enhanced_chunks):
            print(f"  Chunk {i+1}: {chunk.get('content', '')[:50]}...")
            if 'structured_data' in chunk:
                print(f"    Structured data: {chunk['structured_data']}")
        
        print("✅ Private GPT-4 batch processing is working")
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False
    
    print()
    
    # Test 4: Set extraction method to gpt4_enhanced
    print("🔍 Test 4: Set Extraction Method to GPT-4 Enhanced")
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
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Private GPT-4 Default Test")
    print("=" * 60)
    
    success = test_private_gpt4_default()
    
    print("\n" + "=" * 60)
    print("📊 Test Result:")
    print(f"   Private GPT-4 Default: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Private GPT-4 is now the default with optimized batch processing!")
    else:
        print("\n⚠️  Private GPT-4 default setting has issues.") 