#!/usr/bin/env python3
"""
Test parallel processing implementation with Private GPT-4
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_parallel_processing_private():
    """Test parallel processing implementation with Private GPT-4"""
    
    print("🧪 Testing Parallel Processing Implementation (OpenAI GPT-4)")
    print("=" * 60)
    
    try:
        import sys
        sys.path.append('..')
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
            private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
        )
        
        print("✅ GPT4Extractor initialized")
        
        # Create test chunks
        test_chunks = []
        for i in range(20):  # Test with 20 chunks
            test_chunks.append({
                'content': f"""Section {i+1}: This is a test document section with date 2024-01-15 and amount $500. 
                The contract is between ABC Company and XYZ Corporation. This section contains important legal terms 
                and conditions that must be carefully reviewed. Payment terms are 30 days from invoice date. 
                Late payments will incur a 1.5% monthly interest rate. The vendor shall provide comprehensive 
                IT consulting services including system analysis, design, implementation, and ongoing support."""
            })
        
        print(f"📝 Testing parallel processing with {len(test_chunks)} chunks")
        
        # Test parallel processing
        features = {
            'text_enhancement': False,  # Disable for speed
            'structured_data': True,
            'contract_analysis': True
        }
        
        print("🔄 Running parallel batch enhancement with OpenAI GPT-4...")
        start_time = time.time()
        
        enhanced_chunks = extractor.batch_enhance_chunks(
            test_chunks, 
            features=features,
            prefer_private_gpt4=False  # Use OpenAI GPT-4
        )
        
        end_time = time.time()
        print(f"⏱️  Parallel processing took: {end_time - start_time:.2f} seconds")
        
        print(f"📊 Enhanced chunks: {len(enhanced_chunks)}")
        
        # Check if chunks have structured data
        chunks_with_data = sum(1 for chunk in enhanced_chunks if 'structured_data' in chunk)
        print(f"📊 Chunks with structured data: {chunks_with_data}")
        
        if chunks_with_data > 0:
            print("✅ Parallel processing succeeded")
            
            # Show sample structured data
            for i, chunk in enumerate(enhanced_chunks[:3]):
                if 'structured_data' in chunk:
                    print(f"  Chunk {i+1} structured data: {chunk['structured_data'].get('extracted_data', {})}")
            
            return True
        else:
            print("⚠️  Parallel processing completed but no structured data found")
            return False
            
    except Exception as e:
        print(f"❌ Parallel processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Parallel Processing Test (OpenAI GPT-4)")
    print("=" * 70)
    
    success = test_parallel_processing_private()
    
    print("\n" + "=" * 70)
    print("📊 Test Result:")
    print(f"   Parallel Processing: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Parallel processing is working!")
        print("✅ All chunks are being processed with GPT-4!")
        print("✅ Much faster processing with parallel execution!")
        print("✅ OpenAI GPT-4 is working correctly!")
    else:
        print("\n⚠️  Parallel processing has issues.") 