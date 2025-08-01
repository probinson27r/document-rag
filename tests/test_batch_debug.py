#!/usr/bin/env python3
"""
Debug batch processing issues
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_batch_debug():
    """Debug batch processing issues"""
    
    print("🧪 Debugging Batch Processing")
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
        
        # Create test chunks
        test_chunks = [
            {'content': 'This is chunk 1 with date 2024-01-15'},
            {'content': 'This is chunk 2 with amount $500'},
            {'content': 'This is chunk 3 with name John Doe'}
        ]
        
        print(f"📝 Testing with {len(test_chunks)} chunks")
        
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
            prefer_private_gpt4=False  # Use OpenAI GPT-4
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
    print("🚀 Starting Batch Processing Debug")
    print("=" * 60)
    
    success = test_batch_debug()
    
    print("\n" + "=" * 60)
    print("📊 Debug Result:")
    print(f"   Batch Debug: {'✅ PASS' if success else '❌ FAIL'}") 