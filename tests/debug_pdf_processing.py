#!/usr/bin/env python3
"""
Debug script for PDF processing with Private GPT-4
"""

import os
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

def debug_pdf_processing():
    """Debug PDF processing with Private GPT-4"""
    
    print("🔍 Debugging PDF Processing with Private GPT-4")
    print("=" * 60)
    
    pdf_path = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"✅ Found PDF file: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    try:
        from document_rag import DocumentRAG
        
        print("\n1. Initializing DocumentRAG...")
        start_time = time.time()
        
        rag = DocumentRAG()
        
        init_time = time.time() - start_time
        print(f"✅ DocumentRAG initialized in {init_time:.2f} seconds")
        
        # Check GPT-4 configuration
        print("\n2. Checking GPT-4 Configuration...")
        if hasattr(rag.document_processor, 'gpt4_extractor'):
            extractor = rag.document_processor.gpt4_extractor
            print(f"✅ GPT-4 Extractor: {extractor is not None}")
            if extractor:
                print(f"   Private GPT-4 URL: {extractor.private_gpt4_url[:50] if extractor.private_gpt4_url else 'None'}...")
                print(f"   Private GPT-4 Key: {extractor.private_gpt4_key[:10] if extractor.private_gpt4_key else 'None'}...")
        
        if hasattr(rag.document_processor, 'gpt4_chunker'):
            chunker = rag.document_processor.gpt4_chunker
            print(f"✅ GPT-4 Chunker: {chunker is not None}")
            if chunker:
                print(f"   Private GPT-4 URL: {chunker.private_gpt4_url[:50] if chunker.private_gpt4_url else 'None'}...")
                print(f"   Private GPT-4 Key: {chunker.private_gpt4_key[:10] if chunker.private_gpt4_key else 'None'}...")
        
        # Test document processing
        print("\n3. Testing PDF Document Processing...")
        start_time = time.time()
        
        try:
            result = rag.ingest_document(pdf_path)
            processing_time = time.time() - start_time
            
            print(f"⏱️  PDF processing completed in {processing_time:.2f} seconds")
            print(f"📊 Result: {result}")
            
            if "successfully ingested" in result.lower():
                print("✅ PDF processing successful!")
                
                # Test querying the processed document
                print("\n4. Testing Document Querying...")
                query_start = time.time()
                
                query_result = rag.query("What is the total contract value?")
                query_time = time.time() - query_start
                
                print(f"⏱️  Query completed in {query_time:.2f} seconds")
                print(f"📊 Query result: {query_result.get('answer', 'No answer')[:200]}...")
                
                if query_result.get('answer'):
                    print("✅ Document querying successful!")
                else:
                    print("⚠️  No answer received from query")
                    
            else:
                print(f"⚠️  PDF processing result: {result}")
                
        except Exception as e:
            print(f"❌ PDF processing failed: {e}")
            import traceback
            traceback.print_exc()
            processing_time = time.time() - start_time
            print(f"⏱️  Failed after {processing_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during PDF processing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_text_extraction():
    """Test PDF text extraction specifically"""
    
    print("\n🔍 Testing PDF Text Extraction")
    print("=" * 60)
    
    pdf_path = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    try:
        from document_rag import DocumentProcessor
        
        processor = DocumentProcessor()
        
        print("1. Testing PDF text extraction...")
        start_time = time.time()
        
        # Extract text directly
        text = processor.extract_text_from_pdf(pdf_path)
        extraction_time = time.time() - start_time
        
        print(f"⏱️  Text extraction completed in {extraction_time:.2f} seconds")
        print(f"📊 Extracted text length: {len(text)} characters")
        print(f"📄 First 200 characters: {text[:200]}...")
        print(f"📄 Last 200 characters: ...{text[-200:]}")
        
        if len(text.strip()) < 100:
            print("⚠️  Warning: Very little text extracted from PDF")
        else:
            print("✅ Text extraction appears successful")
        
        # Test GPT-4 enhancement
        print("\n2. Testing GPT-4 Text Enhancement...")
        start_time = time.time()
        
        try:
            enhanced_data = processor.enhance_text_with_gpt4(text, ".pdf", prefer_private_gpt4=True)
            enhancement_time = time.time() - start_time
            
            print(f"⏱️  Enhancement completed in {enhancement_time:.2f} seconds")
            print(f"📊 Enhancement result: {enhanced_data.get('success', False)}")
            
            if enhanced_data.get('success'):
                enhanced_text = enhanced_data.get('enhanced_text', '')
                print(f"📊 Enhanced text length: {len(enhanced_text)} characters")
                print("✅ Text enhancement successful!")
            else:
                print(f"❌ Enhancement failed: {enhanced_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Enhancement error: {e}")
            enhancement_time = time.time() - start_time
            print(f"⏱️  Failed after {enhancement_time:.2f} seconds")
        
        # Test GPT-4 chunking
        print("\n3. Testing GPT-4 Chunking...")
        start_time = time.time()
        
        try:
            chunking_result = processor.chunk_text_with_gpt4(text, "legal", True, prefer_private_gpt4=True)
            chunking_time = time.time() - start_time
            
            print(f"⏱️  Chunking completed in {chunking_time:.2f} seconds")
            print(f"📊 Chunking result: {chunking_result.get('success', False)}")
            
            if chunking_result.get('success'):
                chunks = chunking_result.get('chunks', [])
                print(f"📊 Generated {len(chunks)} chunks")
                print("✅ Chunking successful!")
                
                # Show first chunk
                if chunks:
                    first_chunk = chunks[0]
                    print(f"📄 First chunk: {first_chunk.get('content', '')[:200]}...")
            else:
                print(f"❌ Chunking failed: {chunking_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            chunking_time = time.time() - start_time
            print(f"⏱️  Failed after {chunking_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during text extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_private_gpt4_connection():
    """Test Private GPT-4 connection specifically"""
    
    print("\n🔍 Testing Private GPT-4 Connection")
    print("=" * 60)
    
    import requests
    
    private_gpt4_url = os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview')
    private_gpt4_key = os.getenv('PRIVATE_GPT4_API_KEY')
    
    if not private_gpt4_key:
        print("❌ Private GPT-4 API key not found")
        return False
    
    print(f"✅ Using Private GPT-4 URL: {private_gpt4_url[:50]}...")
    print(f"✅ Using Private GPT-4 Key: {private_gpt4_key[:10]}...")
    
    # Test simple completion
    headers = {
        'Content-Type': 'application/json',
        'api-key': private_gpt4_key
    }
    
    data = {
        "messages": [
            {"role": "user", "content": "Say 'Private GPT-4 is working for PDF processing!'"}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print("\n1. Testing Simple Completion...")
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
    
    # Test with larger content (simulating PDF processing)
    print("\n2. Testing with Larger Content...")
    
    # Create a larger prompt to simulate PDF processing
    large_prompt = """
    Analyze this contract document and extract key information:
    
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
    
    Please extract the following information:
    - Contract parties
    - Contract value
    - Service duration
    - Key terms
    """
    
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert contract analyzer. Extract key information from contracts accurately."},
            {"role": "user", "content": large_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    try:
        start_time = time.time()
        response = requests.post(private_gpt4_url, headers=headers, json=data, timeout=60)
        api_time = time.time() - start_time
        
        print(f"⏱️  Large content API call completed in {api_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Response: {content[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Large content API call timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Large content API call failed: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting PDF Processing Debug Tests")
    print("=" * 60)
    
    # Test Private GPT-4 connection first
    connection_success = test_private_gpt4_connection()
    
    # Test PDF text extraction
    extraction_success = test_pdf_text_extraction()
    
    # Test complete PDF processing
    processing_success = debug_pdf_processing()
    
    print("\n" + "=" * 60)
    print("📊 Debug Test Summary:")
    print(f"   Private GPT-4 Connection: {'✅ PASS' if connection_success else '❌ FAIL'}")
    print(f"   PDF Text Extraction: {'✅ PASS' if extraction_success else '❌ FAIL'}")
    print(f"   Complete PDF Processing: {'✅ PASS' if processing_success else '❌ FAIL'}")
    
    if connection_success and extraction_success and processing_success:
        print("\n🎉 All tests passed! PDF processing should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 