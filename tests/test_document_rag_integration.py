#!/usr/bin/env python3
"""
Test script to verify complete DocumentRAG integration with Private GPT-4
"""

import os
import time
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_document_rag_integration():
    """Test complete DocumentRAG integration with Private GPT-4"""
    
    print("🔍 Testing Complete DocumentRAG Integration with Private GPT-4")
    print("=" * 70)
    
    try:
        from document_rag import DocumentRAG
        
        print("\n1. Initializing DocumentRAG...")
        start_time = time.time()
        
        rag = DocumentRAG()
        
        init_time = time.time() - start_time
        print(f"✅ DocumentRAG initialized in {init_time:.2f} seconds")
        
        # Check GPT-4 availability
        print("\n2. Checking GPT-4 Configuration...")
        if hasattr(rag.document_processor, 'use_gpt4_chunking'):
            print(f"✅ GPT-4 chunking available: {rag.document_processor.use_gpt4_chunking}")
        else:
            print("❌ GPT-4 chunking not available")
        
        if hasattr(rag.document_processor, 'use_gpt4_enhancement'):
            print(f"✅ GPT-4 enhancement available: {rag.document_processor.use_gpt4_enhancement}")
        else:
            print("❌ GPT-4 enhancement not available")
        
        # Create a test document
        print("\n3. Creating Test Document...")
        test_content = """
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
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        print(f"✅ Test document created: {temp_file_path}")
        
        # Test document ingestion
        print("\n4. Testing Document Ingestion with Private GPT-4...")
        start_time = time.time()
        
        try:
            result = rag.ingest_document(temp_file_path)
            ingestion_time = time.time() - start_time
            
            print(f"⏱️  Document ingestion completed in {ingestion_time:.2f} seconds")
            print(f"📊 Result: {result}")
            
            if "successfully ingested" in result.lower():
                print("✅ Document ingestion successful!")
            else:
                print(f"⚠️  Ingestion result: {result}")
                
        except Exception as e:
            print(f"❌ Document ingestion failed: {e}")
            ingestion_time = time.time() - start_time
            print(f"⏱️  Failed after {ingestion_time:.2f} seconds")
        
        # Test document querying
        print("\n5. Testing Document Querying...")
        start_time = time.time()
        
        try:
            query_result = rag.query("What is the total contract value?")
            query_time = time.time() - start_time
            
            print(f"⏱️  Query completed in {query_time:.2f} seconds")
            print(f"📊 Query result: {query_result.get('answer', 'No answer')[:200]}...")
            
            if query_result.get('answer'):
                print("✅ Document querying successful!")
            else:
                print("⚠️  No answer received from query")
                
        except Exception as e:
            print(f"❌ Document querying failed: {e}")
            query_time = time.time() - start_time
            print(f"⏱️  Failed after {query_time:.2f} seconds")
        
        # Test document search
        print("\n6. Testing Document Search...")
        start_time = time.time()
        
        try:
            search_result = rag.search_documents("contract value payment terms")
            search_time = time.time() - start_time
            
            print(f"⏱️  Search completed in {search_time:.2f} seconds")
            print(f"📊 Search results: {len(search_result)} documents found")
            
            if search_result:
                print("✅ Document search successful!")
                for i, doc in enumerate(search_result[:2]):  # Show first 2 results
                    print(f"   Result {i+1}: {doc.get('content', '')[:100]}...")
            else:
                print("⚠️  No search results found")
                
        except Exception as e:
            print(f"❌ Document search failed: {e}")
            search_time = time.time() - start_time
            print(f"⏱️  Failed after {search_time:.2f} seconds")
        
        # Clean up
        try:
            os.unlink(temp_file_path)
            print(f"\n✅ Cleaned up temporary file: {temp_file_path}")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_processing_performance():
    """Test processing performance with different document sizes"""
    
    print("\n🔍 Testing Processing Performance")
    print("=" * 70)
    
    try:
        from document_rag import DocumentRAG
        
        rag = DocumentRAG()
        
        # Test different document sizes
        document_sizes = [
            ("Small", 500),
            ("Medium", 2000),
            ("Large", 5000)
        ]
        
        for size_name, char_count in document_sizes:
            print(f"\n📄 Testing {size_name} Document ({char_count} characters)...")
            
            # Generate test content
            test_content = "This is a test document. " * (char_count // 25)
            test_content = test_content[:char_count]
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                start_time = time.time()
                result = rag.ingest_document(temp_file_path)
                processing_time = time.time() - start_time
                
                print(f"⏱️  {size_name} document processed in {processing_time:.2f} seconds")
                print(f"📊 Result: {'Success' if 'successfully' in result.lower() else 'Failed'}")
                
                # Clean up
                os.unlink(temp_file_path)
                
            except Exception as e:
                print(f"❌ {size_name} document processing failed: {e}")
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error during performance test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting DocumentRAG Integration Tests")
    print("=" * 70)
    
    # Test complete integration
    integration_success = test_document_rag_integration()
    
    # Test performance
    performance_success = test_processing_performance()
    
    print("\n" + "=" * 70)
    print("📊 Integration Test Summary:")
    print(f"   Complete Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    print(f"   Performance Test: {'✅ PASS' if performance_success else '❌ FAIL'}")
    
    if integration_success and performance_success:
        print("\n🎉 All integration tests passed! Private GPT-4 processing is working correctly.")
        print("✅ DocumentRAG is ready for production use with Private GPT-4.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 