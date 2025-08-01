#!/usr/bin/env python3
"""
Test script for GPT-4 chunking functionality
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_gpt4_chunking():
    """Test GPT-4 chunking functionality"""
    
    print("🧪 Testing GPT-4 Chunking Functionality")
    print("=" * 50)
    
    # Test 1: Import and initialize GPT-4 chunker
    print("\n1. Testing GPT-4 Chunker Import...")
    try:
        from gpt4_chunking import GPT4Chunker
        print("✅ GPT-4 chunker imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import GPT-4 chunker: {e}")
        return False
    
    # Test 2: Initialize chunker
    print("\n2. Testing GPT-4 Chunker Initialization...")
    try:
        chunker = GPT4Chunker(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
            private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
        )
        print("✅ GPT-4 chunker initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GPT-4 chunker: {e}")
        return False
    
    # Test 3: Test with sample legal document
    print("\n3. Testing GPT-4 Chunking with Legal Document...")
    
    sample_legal_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation.
    
    Section 1: Definitions
    1.1 "Vendor" means ABC Company, a corporation organized under the laws of Delaware.
    1.2 "Client" means XYZ Corporation, a corporation organized under the laws of California.
    1.3 "Services" means the consulting services described in Section 2 below.
    1.4 "Effective Date" means January 1, 2024.
    
    Section 2: Services
    2.1 The Vendor shall provide IT consulting services as specified in Schedule A attached hereto.
    2.2 Services shall commence on the Effective Date and continue for a period of twelve (12) months.
    2.3 The Vendor shall deliver all deliverables in accordance with the timeline set forth in Schedule A.
    
    Section 3: Payment Terms
    3.1 The Client shall pay the Vendor a total fee of $500,000 for the Services.
    3.2 Payment shall be made in monthly installments of $41,667, due on the first day of each month.
    3.3 All payments are due within 30 days of invoice date.
    3.4 Late payments shall incur interest at the rate of 1.5% per month.
    
    Section 4: Term and Termination
    4.1 This Agreement shall commence on the Effective Date and continue for one (1) year.
    4.2 Either party may terminate this Agreement with 30 days written notice.
    4.3 Upon termination, the Client shall pay for all Services rendered up to the termination date.
    """
    
    try:
        result = chunker.chunk_document_with_gpt4(sample_legal_text, "legal", True)
        
        if result.get('success'):
            print(f"✅ GPT-4 chunking successful!")
            print(f"   - Generated {len(result['chunks'])} chunks")
            print(f"   - Chunking method: {result.get('chunking_method', 'unknown')}")
            
            # Display chunk details
            for i, chunk in enumerate(result['chunks'][:3]):  # Show first 3 chunks
                print(f"\n   Chunk {i+1}:")
                print(f"   - Type: {chunk.get('chunk_type', 'unknown')}")
                print(f"   - Section: {chunk.get('section_number', 'N/A')} - {chunk.get('section_title', 'N/A')}")
                print(f"   - Theme: {chunk.get('semantic_theme', 'N/A')}")
                print(f"   - Quality: {chunk.get('quality_score', 0):.2f}")
                print(f"   - Length: {len(chunk.get('content', ''))} characters")
                print(f"   - Content preview: {chunk.get('content', '')[:100]}...")
            
            # Test optimization
            print("\n4. Testing Chunk Optimization...")
            optimized_chunks = chunker.optimize_chunks_for_rag(result['chunks'])
            print(f"✅ Optimized {len(optimized_chunks)} chunks for RAG")
            
        else:
            print(f"❌ GPT-4 chunking failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during GPT-4 chunking test: {e}")
        return False
    
    # Test 4: Test fallback chunking
    print("\n5. Testing Fallback Chunking...")
    try:
        fallback_result = chunker._fallback_chunking(sample_legal_text, "legal")
        if fallback_result.get('success'):
            print(f"✅ Fallback chunking successful: {len(fallback_result['chunks'])} chunks")
        else:
            print(f"❌ Fallback chunking failed: {fallback_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error during fallback chunking test: {e}")
    
    # Test 5: Test integration with DocumentRAG
    print("\n6. Testing Integration with DocumentRAG...")
    try:
        from document_rag import DocumentRAG
        
        rag = DocumentRAG()
        print("✅ DocumentRAG initialized successfully")
        
        # Check if GPT-4 chunking is available in DocumentRAG
        if hasattr(rag.document_processor, 'use_gpt4_chunking'):
            print(f"✅ GPT-4 chunking available in DocumentRAG: {rag.document_processor.use_gpt4_chunking}")
        else:
            print("❌ GPT-4 chunking not available in DocumentRAG")
            
    except Exception as e:
        print(f"❌ Error testing DocumentRAG integration: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 GPT-4 Chunking Test Complete!")
    return True

def test_api_keys():
    """Test API key availability"""
    print("\n🔑 Testing API Key Availability...")
    
    api_keys = {
        'OpenAI': os.getenv('OPENAI_API_KEY'),
        'Anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'Private GPT-4': os.getenv('PRIVATE_GPT4_API_KEY')
    }
    
    available_keys = []
    for provider, key in api_keys.items():
        if key and key not in ['a', 'b', 'your_openai_api_key_here', 'your_anthropic_api_key_here']:
            print(f"✅ {provider} API key available")
            available_keys.append(provider)
        else:
            print(f"❌ {provider} API key not available")
    
    if available_keys:
        print(f"\n🎯 Available providers for GPT-4 chunking: {', '.join(available_keys)}")
    else:
        print("\n⚠️  No API keys available - GPT-4 chunking will use fallback methods")
    
    return available_keys

if __name__ == "__main__":
    # Test API keys first
    available_keys = test_api_keys()
    
    # Test GPT-4 chunking
    success = test_gpt4_chunking()
    
    if success:
        print("\n✅ All tests passed! GPT-4 chunking is ready to use.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.") 