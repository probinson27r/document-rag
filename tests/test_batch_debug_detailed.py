#!/usr/bin/env python3
"""
Detailed debug of batch processing issues
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_batch_debug_detailed():
    """Debug batch processing issues in detail"""
    
    print("🧪 Detailed Batch Processing Debug")
    print("=" * 50)
    
    try:
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
            private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
        )
        
        print("✅ GPT4Extractor initialized")
        
        # Create test chunks with realistic content
        test_chunks = [
            {'content': 'This is a test document with date 2024-01-15 and amount $500. The contract is between ABC Company and XYZ Corporation.'},
            {'content': 'Section 1: Services. The vendor shall provide IT consulting services. Payment terms are 30 days from invoice.'},
            {'content': 'Section 2: Payment Terms. Payment shall be made within 30 days of invoice. Late payments incur 1.5% monthly interest.'}
        ]
        
        print(f"📝 Testing with {len(test_chunks)} chunks")
        
        # Test individual extraction first
        print("\n🔍 Test 1: Individual Extraction")
        print("-" * 30)
        
        for i, chunk in enumerate(test_chunks):
            print(f"Testing chunk {i+1}: {chunk['content'][:50]}...")
            
            result = extractor.extract_structured_data(chunk['content'], ['dates', 'amounts'], prefer_private_gpt4=True)
            print(f"  Result: {result.get('success', False)}")
            if result.get('success'):
                print(f"  Data: {result.get('extracted_data', {})}")
            else:
                print(f"  Error: {result.get('error', 'Unknown')}")
        
        # Test batch processing
        print("\n🔍 Test 2: Batch Processing")
        print("-" * 30)
        
        features = {
            'text_enhancement': False,  # Disable to reduce complexity
            'structured_data': True,
            'contract_analysis': False  # Disable to reduce complexity
        }
        
        print("🔄 Running batch enhancement...")
        start_time = time.time()
        
        enhanced_chunks = extractor.batch_enhance_chunks(
            test_chunks, 
            features=features,
            prefer_private_gpt4=True
        )
        
        end_time = time.time()
        print(f"⏱️  Batch processing took: {end_time - start_time:.2f} seconds")
        
        print(f"📊 Enhanced chunks: {len(enhanced_chunks)}")
        
        for i, chunk in enumerate(enhanced_chunks):
            print(f"  Chunk {i+1}: {chunk.get('content', '')[:50]}...")
            if 'structured_data' in chunk:
                print(f"    Structured data: {chunk['structured_data']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Detailed Batch Debug")
    print("=" * 60)
    
    success = test_batch_debug_detailed()
    
    print("\n" + "=" * 60)
    print("📊 Debug Result:")
    print(f"   Detailed Batch Debug: {'✅ PASS' if success else '❌ FAIL'}") 