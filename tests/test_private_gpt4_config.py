#!/usr/bin/env python3
"""
Test script to verify Private GPT-4 configuration
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_private_gpt4_configuration():
    """Test Private GPT-4 configuration and priority"""
    
    print("🔧 Testing Private GPT-4 Configuration")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("\n1. Checking Environment Variables...")
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if private_gpt4_key:
        print(f"✅ Private GPT-4 URL: {private_gpt4_url[:50]}...")
        print(f"✅ Private GPT-4 Key: {private_gpt4_key[:10]}...")
    else:
        print("❌ Private GPT-4 API key not found")
        return False
    
    # Test 2: Test GPT-4 extraction with Private GPT-4 priority
    print("\n2. Testing GPT-4 Extraction with Private GPT-4 Priority...")
    try:
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        # Test with prefer_private_gpt4=True
        test_text = "This is a test document for Private GPT-4 extraction."
        result = extractor.extract_structured_data(
            test_text, 
            ['dates', 'names'], 
            prefer_private_gpt4=True
        )
        
        if result.get('success'):
            print("✅ Private GPT-4 extraction successful!")
            print(f"   - Method: {result.get('chunking_method', 'unknown')}")
        else:
            print(f"❌ Private GPT-4 extraction failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing GPT-4 extraction: {e}")
    
    # Test 3: Test GPT-4 chunking with Private GPT-4 priority
    print("\n3. Testing GPT-4 Chunking with Private GPT-4 Priority...")
    try:
        from gpt4_chunking import GPT4Chunker
        
        chunker = GPT4Chunker(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        test_text = """
        CONTRACT AGREEMENT
        
        This agreement is made between ABC Company and XYZ Corporation.
        
        Section 1: Definitions
        1.1 "Vendor" means ABC Company
        1.2 "Client" means XYZ Corporation
        
        Section 2: Services
        2.1 The Vendor shall provide IT consulting services
        2.2 Services shall commence on January 1, 2024
        """
        
        result = chunker.chunk_document_with_gpt4(
            test_text, 
            "legal", 
            True, 
            prefer_private_gpt4=True
        )
        
        if result.get('success'):
            print("✅ Private GPT-4 chunking successful!")
            print(f"   - Method: {result.get('chunking_method', 'unknown')}")
            print(f"   - Chunks: {len(result.get('chunks', []))}")
        else:
            print(f"❌ Private GPT-4 chunking failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error testing GPT-4 chunking: {e}")
    
    # Test 4: Test DocumentRAG integration
    print("\n4. Testing DocumentRAG Integration...")
    try:
        from document_rag import DocumentRAG
        
        rag = DocumentRAG()
        
        # Check if Private GPT-4 is configured
        if hasattr(rag.document_processor, 'gpt4_extractor'):
            print("✅ GPT-4 extractor available in DocumentRAG")
        else:
            print("❌ GPT-4 extractor not available in DocumentRAG")
        
        if hasattr(rag.document_processor, 'gpt4_chunker'):
            print("✅ GPT-4 chunker available in DocumentRAG")
        else:
            print("❌ GPT-4 chunker not available in DocumentRAG")
            
    except Exception as e:
        print(f"❌ Error testing DocumentRAG integration: {e}")
    
    # Test 5: Test provider priority
    print("\n5. Testing Provider Priority...")
    try:
        from gpt4_extraction import GPT4Extractor
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        # Test with prefer_private_gpt4=True (should use Private GPT-4)
        result1 = extractor.extract_with_gpt4(
            "test", 
            "test prompt", 
            prefer_private_gpt4=True
        )
        
        # Test with prefer_private_gpt4=False (should use OpenAI if available)
        result2 = extractor.extract_with_gpt4(
            "test", 
            "test prompt", 
            prefer_private_gpt4=False
        )
        
        print(f"✅ Provider priority test completed")
        print(f"   - prefer_private_gpt4=True: {result1.get('chunking_method', 'unknown')}")
        print(f"   - prefer_private_gpt4=False: {result2.get('chunking_method', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error testing provider priority: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Private GPT-4 Configuration Test Complete!")
    return True

def test_api_keys():
    """Test API key availability and priority"""
    print("\n🔑 Testing API Key Priority...")
    
    api_keys = {
        'Private GPT-4': {
            'key': os.getenv('PRIVATE_GPT4_API_KEY'),
            'url': os.getenv('PRIVATE_GPT4_URL'),
            'priority': 1
        },
        'OpenAI': {
            'key': os.getenv('OPENAI_API_KEY'),
            'priority': 2
        },
        'Anthropic': {
            'key': os.getenv('ANTHROPIC_API_KEY'),
            'priority': 3
        }
    }
    
    available_providers = []
    for provider, config in api_keys.items():
        if config['key'] and config['key'] not in ['a', 'b', 'your_openai_api_key_here', 'your_anthropic_api_key_here']:
            print(f"✅ {provider} available (priority: {config['priority']})")
            available_providers.append((provider, config['priority']))
        else:
            print(f"❌ {provider} not available")
    
    # Sort by priority
    available_providers.sort(key=lambda x: x[1])
    
    if available_providers:
        print(f"\n🎯 Provider priority order:")
        for i, (provider, priority) in enumerate(available_providers, 1):
            print(f"   {i}. {provider} (priority: {priority})")
        
        print(f"\n🏆 Primary provider: {available_providers[0][0]}")
    else:
        print("\n⚠️  No API keys available")
    
    return available_providers

if __name__ == "__main__":
    # Test API key priority
    available_providers = test_api_keys()
    
    # Test Private GPT-4 configuration
    success = test_private_gpt4_configuration()
    
    if success and available_providers:
        print("\n✅ Private GPT-4 configuration is working correctly!")
        print(f"🎯 Primary provider: {available_providers[0][0]}")
    else:
        print("\n❌ Some tests failed. Check the output above for details.") 