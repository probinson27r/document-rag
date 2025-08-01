#!/usr/bin/env python3
"""
Debug script for PDF processing hanging issue
"""

import os
import time
import signal
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function timed out")

def test_pdf_processing_step_by_step():
    """Test PDF processing step by step to identify where it hangs"""
    
    print("🔍 Testing PDF Processing Step by Step")
    print("=" * 60)
    
    pdf_path = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"✅ Found PDF file: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    
    try:
        from document_rag import DocumentProcessor
        
        print("\n1. Initializing DocumentProcessor...")
        start_time = time.time()
        
        processor = DocumentProcessor()
        
        init_time = time.time() - start_time
        print(f"✅ DocumentProcessor initialized in {init_time:.2f} seconds")
        
        # Step 1: Test PDF text extraction
        print("\n2. Testing PDF Text Extraction...")
        start_time = time.time()
        
        try:
            # Set up timeout for text extraction
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(120)  # 2 minute timeout for text extraction
            
            text = processor.extract_text_from_pdf(pdf_path)
            signal.alarm(0)  # Cancel the alarm
            
            extraction_time = time.time() - start_time
            print(f"⏱️  Text extraction completed in {extraction_time:.2f} seconds")
            print(f"📊 Extracted text length: {len(text)} characters")
            print(f"📄 First 200 characters: {text[:200]}...")
            
            if len(text.strip()) < 100:
                print("⚠️  Warning: Very little text extracted from PDF")
                return False
            else:
                print("✅ Text extraction appears successful")
                
        except TimeoutError:
            print("❌ Text extraction timed out after 120 seconds")
            return False
        except Exception as e:
            print(f"❌ Text extraction error: {e}")
            return False
        
        # Step 2: Test GPT-4 enhancement with timeout
        print("\n3. Testing GPT-4 Text Enhancement...")
        start_time = time.time()
        
        try:
            # Set up timeout for enhancement
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(180)  # 3 minute timeout for enhancement
            
            enhanced_data = processor.enhance_text_with_gpt4(text, ".pdf", prefer_private_gpt4=True)
            signal.alarm(0)  # Cancel the alarm
            
            enhancement_time = time.time() - start_time
            print(f"⏱️  Enhancement completed in {enhancement_time:.2f} seconds")
            print(f"📊 Enhancement result: {enhanced_data.get('success', False)}")
            
            if enhanced_data.get('success'):
                enhanced_text = enhanced_data.get('enhanced_text', '')
                print(f"📊 Enhanced text length: {len(enhanced_text)} characters")
                print("✅ Text enhancement successful!")
            else:
                print(f"❌ Enhancement failed: {enhanced_data.get('error', 'Unknown error')}")
                
        except TimeoutError:
            print("❌ Enhancement timed out after 180 seconds")
            return False
        except Exception as e:
            print(f"❌ Enhancement error: {e}")
            return False
        
        # Step 3: Test GPT-4 chunking with timeout
        print("\n4. Testing GPT-4 Chunking...")
        start_time = time.time()
        
        try:
            # Set up timeout for chunking
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(180)  # 3 minute timeout for chunking
            
            chunking_result = processor.chunk_text_with_gpt4(text, "legal", True, prefer_private_gpt4=True)
            signal.alarm(0)  # Cancel the alarm
            
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
                
        except TimeoutError:
            print("❌ Chunking timed out after 180 seconds")
            return False
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error during step-by-step test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_rag_with_timeout():
    """Test DocumentRAG with timeout monitoring"""
    
    print("\n🔍 Testing DocumentRAG with Timeout Monitoring")
    print("=" * 60)
    
    pdf_path = "uploads/120_ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    try:
        from document_rag import DocumentRAG
        
        print("1. Initializing DocumentRAG...")
        start_time = time.time()
        
        rag = DocumentRAG()
        
        init_time = time.time() - start_time
        print(f"✅ DocumentRAG initialized in {init_time:.2f} seconds")
        
        # Test document ingestion with timeout
        print("\n2. Testing Document Ingestion with Timeout...")
        start_time = time.time()
        
        try:
            # Set up timeout for ingestion
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(300)  # 5 minute timeout for ingestion
            
            result = rag.ingest_document(pdf_path)
            signal.alarm(0)  # Cancel the alarm
            
            ingestion_time = time.time() - start_time
            print(f"⏱️  Document ingestion completed in {ingestion_time:.2f} seconds")
            print(f"📊 Result: {result}")
            
            if "successfully ingested" in result.lower():
                print("✅ Document ingestion successful!")
                return True
            else:
                print(f"⚠️  Ingestion result: {result}")
                return False
                
        except TimeoutError:
            print("❌ Document ingestion timed out after 300 seconds")
            return False
        except Exception as e:
            print(f"❌ Document ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Error during DocumentRAG test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_smaller_pdf():
    """Test with a smaller PDF to see if size is the issue"""
    
    print("\n🔍 Testing with Smaller PDF")
    print("=" * 60)
    
    # Create a small test PDF
    test_pdf_path = "uploads/test_small.pdf"
    
    try:
        from fpdf import FPDF
        
        # Create a simple PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Test Contract Agreement", ln=1, align='C')
        pdf.cell(200, 10, txt="This is a test contract between ABC Company and XYZ Corporation.", ln=1, align='L')
        pdf.cell(200, 10, txt="The total contract value is $100,000 USD.", ln=1, align='L')
        pdf.cell(200, 10, txt="Services shall commence on January 1, 2024.", ln=1, align='L')
        pdf.output(test_pdf_path)
        
        print(f"✅ Created test PDF: {test_pdf_path}")
        print(f"📊 File size: {os.path.getsize(test_pdf_path) / 1024:.1f} KB")
        
        # Test with the small PDF
        from document_rag import DocumentRAG
        
        rag = DocumentRAG()
        
        print("\nTesting ingestion of small PDF...")
        start_time = time.time()
        
        try:
            # Set up timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 1 minute timeout
            
            result = rag.ingest_document(test_pdf_path)
            signal.alarm(0)  # Cancel the alarm
            
            ingestion_time = time.time() - start_time
            print(f"⏱️  Small PDF ingestion completed in {ingestion_time:.2f} seconds")
            print(f"📊 Result: {result}")
            
            if "successfully ingested" in result.lower():
                print("✅ Small PDF ingestion successful!")
                return True
            else:
                print(f"⚠️  Small PDF ingestion result: {result}")
                return False
                
        except TimeoutError:
            print("❌ Small PDF ingestion timed out after 60 seconds")
            return False
        except Exception as e:
            print(f"❌ Small PDF ingestion failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error creating test PDF: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting PDF Hanging Debug Tests")
    print("=" * 60)
    
    # Test step by step processing
    step_by_step_success = test_pdf_processing_step_by_step()
    
    # Test DocumentRAG with timeout
    rag_success = test_document_rag_with_timeout()
    
    # Test with smaller PDF
    small_pdf_success = test_with_smaller_pdf()
    
    print("\n" + "=" * 60)
    print("📊 PDF Hanging Debug Test Summary:")
    print(f"   Step-by-Step Processing: {'✅ PASS' if step_by_step_success else '❌ FAIL'}")
    print(f"   DocumentRAG Processing: {'✅ PASS' if rag_success else '❌ FAIL'}")
    print(f"   Small PDF Processing: {'✅ PASS' if small_pdf_success else '❌ FAIL'}")
    
    if step_by_step_success and rag_success and small_pdf_success:
        print("\n🎉 All tests passed! PDF processing should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for hanging issues.") 