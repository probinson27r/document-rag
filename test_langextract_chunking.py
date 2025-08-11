#!/usr/bin/env python3
"""
Test script for LangExtract chunking implementation
"""

import os
import sys
from langextract_chunking import LangExtractChunker

def test_langextract_chunking():
    """Test the LangExtract chunking functionality"""
    
    print("Testing LangExtract Chunking Implementation")
    print("=" * 50)
    
    # Test document text
    test_text = """
## 3.2 Objectives

The objectives of this agreement are:

1. Collaboration: Build a collaborative relationship between the Customer and the Contractor to achieve shared outcomes.

2. Value for Money: Deliver services in a manner that provides measurable value for money for the Customer.

3. Continuous Improvement: Ensure ongoing enhancements in the quality, efficiency, and effectiveness of the services.

4. Innovation: Encourage innovation to meet evolving requirements and challenges faced by the Customer.

5. Risk Management: Proactively manage risks to minimize disruptions and ensure service continuity.

6. Compliance: Adhere to all applicable laws, regulations, and policies governing the services.

7. Performance Transparency: Maintain clear and measurable service delivery performance levels, supported by timely reporting.

8. Customer Satisfaction: Deliver services in a manner that optimally meets the needs of end-users and stakeholders.

9. Sustainability: Support environmentally and socially sustainable practices in the delivery of services.

## 3.3 Achievement of Objectives

The Contractor must continuously seek ways to improve services to better achieve these objectives.

## 4.1 Scope of Services

The Contractor shall provide the following services:

a) Technical consulting and support
b) System integration and deployment
c) Training and documentation
d) Ongoing maintenance and updates

## 4.2 Service Levels

The Contractor shall maintain the following service levels:

- 99.9% uptime for critical systems
- 4-hour response time for urgent issues
- 24-hour response time for standard issues
- Monthly performance reports
"""
    
    # Initialize LangExtract chunker
    print("Initializing LangExtract chunker...")
    chunker = LangExtractChunker(
        max_chunk_size=2000,
        min_chunk_size=200,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False  # Use fallback for testing
    )
    
    print(f"LangExtract available: {chunker.langextract_available}")
    print(f"Using fallback chunking: {not chunker.langextract_available}")
    
    # Test chunking
    print("\nTesting document chunking...")
    chunks = chunker.chunk_document(test_text)
    
    print(f"\nResults:")
    print(f"Total chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Type: {chunk.chunk_type}")
        print(f"  Section Type: {chunk.section_type}")
        print(f"  Section Title: {chunk.section_title}")
        print(f"  Semantic Theme: {chunk.semantic_theme}")
        print(f"  Confidence: {chunk.confidence}")
        print(f"  Extraction Method: {chunk.extraction_method}")
        print(f"  List Items: {len(chunk.list_items)}")
        print(f"  Content Length: {len(chunk.content)} characters")
        print(f"  Content Preview: {chunk.content[:100]}...")
        
        if chunk.list_items:
            print("  List Items Found:")
            for item in chunk.list_items[:3]:  # Show first 3 items
                print(f"    {item['number']}. {item['text'][:50]}...")
    
    # Test with different chunking methods
    print("\n" + "=" * 50)
    print("Testing different chunking configurations...")
    
    # Test with smaller chunk size
    chunker_small = LangExtractChunker(
        max_chunk_size=1000,
        min_chunk_size=100,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False
    )
    
    chunks_small = chunker_small.chunk_document(test_text)
    print(f"Small chunks: {len(chunks_small)} chunks created")
    
    # Test with larger chunk size
    chunker_large = LangExtractChunker(
        max_chunk_size=3000,
        min_chunk_size=500,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False
    )
    
    chunks_large = chunker_large.chunk_document(test_text)
    print(f"Large chunks: {len(chunks_large)} chunks created")
    
    print("\nLangExtract chunking test completed successfully!")
    return True

def test_integration_with_document_rag():
    """Test integration with DocumentRAG class"""
    
    print("\n" + "=" * 50)
    print("Testing integration with DocumentRAG...")
    
    try:
        from document_rag import DocumentRAG
        
        # Test with semantic chunking (default)
        print("Testing with semantic chunking...")
        rag_semantic = DocumentRAG(chunking_method='semantic')
        print(f"Semantic chunking method: {rag_semantic.chunking_method}")
        
        # Test with LangExtract chunking
        print("Testing with LangExtract chunking...")
        rag_langextract = DocumentRAG(chunking_method='langextract')
        print(f"LangExtract chunking method: {rag_langextract.chunking_method}")
        
        # Test with traditional chunking
        print("Testing with traditional chunking...")
        rag_traditional = DocumentRAG(chunking_method='traditional')
        print(f"Traditional chunking method: {rag_traditional.chunking_method}")
        
        print("DocumentRAG integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"DocumentRAG integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("LangExtract Chunking Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    test1_success = test_langextract_chunking()
    
    # Test integration
    test2_success = test_integration_with_document_rag()
    
    if test1_success and test2_success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
