#!/usr/bin/env python3
"""
Debug batch processing errors
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_batch_error_debug():
    """Debug batch processing errors"""
    
    print("🧪 Debugging Batch Processing Errors")
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
        
        # Create a larger test with more realistic content
        test_chunks = []
        for i in range(10):  # Test with 10 chunks
            test_chunks.append({
                'content': f"""Section {i+1}: This is a test document section with date 2024-01-15 and amount $500. 
                The contract is between ABC Company and XYZ Corporation. This section contains important legal terms 
                and conditions that must be carefully reviewed. Payment terms are 30 days from invoice date. 
                Late payments will incur a 1.5% monthly interest rate. The vendor shall provide comprehensive 
                IT consulting services including system analysis, design, implementation, and ongoing support."""
            })
        
        print(f"📝 Testing with {len(test_chunks)} chunks")
        
        # Test batch processing with different features
        print("\n🔍 Test 1: Batch Processing with All Features")
        print("-" * 30)
        
        features = {
            'text_enhancement': True,
            'structured_data': True,
            'contract_analysis': True
        }
        
        print("🔄 Running batch enhancement...")
        start_time = time.time()
        
        try:
            enhanced_chunks = extractor.batch_enhance_chunks(
                test_chunks, 
                features=features,
                prefer_private_gpt4=True
            )
            
            end_time = time.time()
            print(f"⏱️  Batch processing took: {end_time - start_time:.2f} seconds")
            print(f"📊 Enhanced chunks: {len(enhanced_chunks)}")
            
            # Check if any chunks have structured data
            chunks_with_data = sum(1 for chunk in enhanced_chunks if 'structured_data' in chunk)
            print(f"📊 Chunks with structured data: {chunks_with_data}")
            
            if chunks_with_data > 0:
                print("✅ Batch processing succeeded")
                return True
            else:
                print("⚠️  Batch processing completed but no structured data found")
                return False
                
        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Batch Error Debug")
    print("=" * 60)
    
    success = test_batch_error_debug()
    
    print("\n" + "=" * 60)
    print("📊 Debug Result:")
    print(f"   Batch Error Debug: {'✅ PASS' if success else '❌ FAIL'}") 