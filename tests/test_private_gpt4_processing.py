#!/usr/bin/env python3
"""
Test script to debug Private GPT-4 processing issues
"""

import os
import json
import time
import logging
from dotenv import load_dotenv

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.local')

def test_private_gpt4_extraction_timeout():
    """Test Private GPT-4 extraction with timeout monitoring"""
    
    print("🔍 Testing Private GPT-4 Processing with Timeout Monitoring")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if not private_gpt4_key:
        print("❌ Private GPT-4 API key not found")
        return False
    
    print(f"✅ Using Private GPT-4 URL: {private_gpt4_url[:50]}...")
    print(f"✅ Using Private GPT-4 Key: {private_gpt4_key[:10]}...")
    
    try:
        from gpt4_extraction import GPT4Extractor
        
        print("\n1. Initializing GPT-4 Extractor...")
        start_time = time.time()
        
        extractor = GPT4Extractor(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        init_time = time.time() - start_time
        print(f"✅ Extractor initialized in {init_time:.2f} seconds")
        
        # Test 1: Simple text extraction
        print("\n2. Testing Simple Text Extraction...")
        test_text = "This is a simple test document. It contains basic information."
        
        start_time = time.time()
        result = extractor.extract_structured_data(
            test_text, 
            ['dates', 'names'], 
            prefer_private_gpt4=True
        )
        extraction_time = time.time() - start_time
        
        print(f"⏱️  Extraction completed in {extraction_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        
        # Test 2: Larger text extraction
        print("\n3. Testing Larger Text Extraction...")
        larger_text = """
        CONTRACT AGREEMENT
        
        This agreement is made between ABC Company and XYZ Corporation on January 15, 2024.
        
        Section 1: Definitions
        1.1 "Vendor" means ABC Company, a corporation organized under the laws of Delaware
        1.2 "Client" means XYZ Corporation, a corporation organized under the laws of California
        1.3 "Services" means the IT consulting services described in Section 2
        
        Section 2: Services
        2.1 The Vendor shall provide IT consulting services to the Client
        2.2 Services shall commence on January 1, 2024 and continue for 12 months
        2.3 The total contract value is $500,000 USD
        
        Section 3: Payment Terms
        3.1 Client shall pay Vendor $41,667 per month
        3.2 Payment is due within 30 days of invoice
        3.3 Late payments incur 1.5% monthly interest
        
        Section 4: Termination
        4.1 Either party may terminate with 30 days written notice
        4.2 Client may terminate for cause with immediate effect
        4.3 Vendor shall provide transition assistance for 60 days
        
        Section 5: Confidentiality
        5.1 Both parties agree to maintain confidentiality
        5.2 Confidential information includes technical specifications and business plans
        5.3 Confidentiality survives termination for 3 years
        
        Section 6: Liability
        6.1 Vendor's liability is limited to fees paid
        6.2 Neither party is liable for indirect damages
        6.3 Force majeure events excuse performance
        
        Section 7: Governing Law
        7.1 This agreement is governed by California law
        7.2 Disputes shall be resolved in San Francisco courts
        7.3 The prevailing party is entitled to attorney fees
        
        IN WITNESS WHEREOF, the parties have executed this agreement as of the date first written above.
        
        ABC Company
        By: John Smith, CEO
        Date: January 15, 2024
        
        XYZ Corporation
        By: Jane Doe, CTO
        Date: January 15, 2024
        """
        
        start_time = time.time()
        result = extractor.extract_structured_data(
            larger_text, 
            ['dates', 'names', 'amounts', 'contracts'], 
            prefer_private_gpt4=True
        )
        extraction_time = time.time() - start_time
        
        print(f"⏱️  Large extraction completed in {extraction_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        elif result.get('extracted_data'):
            print(f"✅ Extracted data keys: {list(result['extracted_data'].keys())}")
        
        # Test 3: Text enhancement
        print("\n4. Testing Text Enhancement...")
        start_time = time.time()
        result = extractor.enhance_text_extraction(
            larger_text, 
            ".pdf", 
            prefer_private_gpt4=True
        )
        enhancement_time = time.time() - start_time
        
        print(f"⏱️  Enhancement completed in {enhancement_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        
        # Test 4: Contract analysis
        print("\n5. Testing Contract Analysis...")
        start_time = time.time()
        result = extractor.extract_legal_contract_data(
            larger_text, 
            prefer_private_gpt4=True
        )
        contract_time = time.time() - start_time
        
        print(f"⏱️  Contract analysis completed in {contract_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logger.exception("Detailed error information:")
        return False

def test_private_gpt4_chunking_timeout():
    """Test Private GPT-4 chunking with timeout monitoring"""
    
    print("\n🔍 Testing Private GPT-4 Chunking with Timeout Monitoring")
    print("=" * 60)
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    try:
        from gpt4_chunking import GPT4Chunker
        
        print("\n1. Initializing GPT-4 Chunker...")
        start_time = time.time()
        
        chunker = GPT4Chunker(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            private_gpt4_url=private_gpt4_url,
            private_gpt4_key=private_gpt4_key
        )
        
        init_time = time.time() - start_time
        print(f"✅ Chunker initialized in {init_time:.2f} seconds")
        
        # Test 1: Simple chunking
        print("\n2. Testing Simple Chunking...")
        test_text = """
        This is a simple document.
        It has multiple paragraphs.
        Each paragraph should be a separate chunk.
        """
        
        start_time = time.time()
        result = chunker.chunk_document_with_gpt4(
            test_text, 
            "general", 
            True, 
            prefer_private_gpt4=True
        )
        chunking_time = time.time() - start_time
        
        print(f"⏱️  Simple chunking completed in {chunking_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        elif result.get('chunks'):
            print(f"✅ Generated {len(result['chunks'])} chunks")
        
        # Test 2: Complex chunking
        print("\n3. Testing Complex Chunking...")
        complex_text = """
        CONTRACT AGREEMENT
        
        This agreement is made between ABC Company and XYZ Corporation on January 15, 2024.
        
        Section 1: Definitions
        1.1 "Vendor" means ABC Company, a corporation organized under the laws of Delaware
        1.2 "Client" means XYZ Corporation, a corporation organized under the laws of California
        1.3 "Services" means the IT consulting services described in Section 2
        
        Section 2: Services
        2.1 The Vendor shall provide IT consulting services to the Client
        2.2 Services shall commence on January 1, 2024 and continue for 12 months
        2.3 The total contract value is $500,000 USD
        
        Section 3: Payment Terms
        3.1 Client shall pay Vendor $41,667 per month
        3.2 Payment is due within 30 days of invoice
        3.3 Late payments incur 1.5% monthly interest
        
        Section 4: Termination
        4.1 Either party may terminate with 30 days written notice
        4.2 Client may terminate for cause with immediate effect
        4.3 Vendor shall provide transition assistance for 60 days
        
        Section 5: Confidentiality
        5.1 Both parties agree to maintain confidentiality
        5.2 Confidential information includes technical specifications and business plans
        5.3 Confidentiality survives termination for 3 years
        
        Section 6: Liability
        6.1 Vendor's liability is limited to fees paid
        6.2 Neither party is liable for indirect damages
        6.3 Force majeure events excuse performance
        
        Section 7: Governing Law
        7.1 This agreement is governed by California law
        7.2 Disputes shall be resolved in San Francisco courts
        7.3 The prevailing party is entitled to attorney fees
        
        IN WITNESS WHEREOF, the parties have executed this agreement as of the date first written above.
        
        ABC Company
        By: John Smith, CEO
        Date: January 15, 2024
        
        XYZ Corporation
        By: Jane Doe, CTO
        Date: January 15, 2024
        """
        
        start_time = time.time()
        result = chunker.chunk_document_with_gpt4(
            complex_text, 
            "legal", 
            True, 
            prefer_private_gpt4=True
        )
        chunking_time = time.time() - start_time
        
        print(f"⏱️  Complex chunking completed in {chunking_time:.2f} seconds")
        print(f"📊 Result: {result.get('success', False)}")
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
        elif result.get('chunks'):
            print(f"✅ Generated {len(result['chunks'])} chunks")
            for i, chunk in enumerate(result['chunks'][:3]):  # Show first 3 chunks
                print(f"   Chunk {i+1}: {chunk.get('content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during chunking test: {e}")
        logger.exception("Detailed error information:")
        return False

def test_direct_private_gpt4_api():
    """Test direct API calls to Private GPT-4"""
    
    print("\n🔍 Testing Direct Private GPT-4 API Calls")
    print("=" * 60)
    
    import requests
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if not private_gpt4_key:
        print("❌ Private GPT-4 API key not found")
        return False
    
    # Test 1: Simple completion
    print("\n1. Testing Simple Completion...")
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "Say 'Hello, Private GPT-4 is working!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        start_time = time.time()
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
        api_time = time.time() - start_time
        
        print(f"⏱️  API call completed in {api_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ API call timed out after 30 seconds")
    except Exception as e:
        print(f"❌ API call failed: {e}")
    
    # Test 2: Structured extraction
    print("\n2. Testing Structured Extraction...")
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert document analyzer. Extract dates and names from the text and return as JSON."},
            {"role": "user", "content": "The contract was signed by John Smith on January 15, 2024 with ABC Company."}
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }
    
    try:
        start_time = time.time()
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=30)
        api_time = time.time() - start_time
        
        print(f"⏱️  Structured extraction completed in {api_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ API call timed out after 30 seconds")
    except Exception as e:
        print(f"❌ API call failed: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Private GPT-4 Processing Debug Tests")
    print("=" * 60)
    
    # Test direct API calls first
    test_direct_private_gpt4_api()
    
    # Test extraction with timeout monitoring
    extraction_success = test_private_gpt4_extraction_timeout()
    
    # Test chunking with timeout monitoring
    chunking_success = test_private_gpt4_chunking_timeout()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Extraction: {'✅ PASS' if extraction_success else '❌ FAIL'}")
    print(f"   Chunking: {'✅ PASS' if chunking_success else '❌ FAIL'}")
    
    if extraction_success and chunking_success:
        print("\n🎉 All tests passed! Private GPT-4 processing is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 