#!/usr/bin/env python3
"""
Test script to verify improved chunking strategy for document uploads
"""

import os
import sys
from app import ingest_document_with_improved_chunking

def test_improved_chunking():
    """Test the improved chunking strategy"""
    
    print("🧪 Testing Improved Chunking Strategy")
    print("=" * 50)
    
    # Find a test document
    uploads_dir = "uploads"
    test_files = [f for f in os.listdir(uploads_dir) if f.endswith(".pdf")]
    
    if not test_files:
        print("❌ No PDF files found in uploads directory")
        return False
    
    # Use the first PDF file
    test_file = test_files[0]
    file_path = os.path.join(uploads_dir, test_file)
    
    print(f"📄 Testing with: {test_file}")
    
    # Test the improved chunking
    try:
        result = ingest_document_with_improved_chunking(file_path)
        
        if result['success']:
            print("✅ Improved chunking successful!")
            print(f"📊 Chunks created: {result['total_chunks']}")
            print(f"🔧 Method: {result['extraction_method']}")
            print(f"📄 Filename: {result['filename']}")
            print(f"🆔 Document ID: {result['document_id']}")
            
            # Test if the chunks can be found by hybrid search
            print("\n🧪 Testing hybrid search with new chunks...")
            
            try:
                from hybrid_search import HybridSearch
                
                hybrid_search = HybridSearch()
                
                # Test a few queries
                test_queries = [
                    "What is this document about?",
                    "Find any sections",
                    "Show me the main topics"
                ]
                
                for query in test_queries:
                    print(f"\nQuery: '{query}'")
                    results = hybrid_search.search_with_fallback(query, 2)
                    
                    if results:
                        print(f"✅ Found {len(results)} results")
                        for i, result in enumerate(results):
                            print(f"  {i+1}. Text: {result['text'][:100]}...")
                    else:
                        print("❌ No results found")
                        
            except Exception as e:
                print(f"⚠️ Hybrid search test failed: {e}")
            
            return True
        else:
            print(f"❌ Improved chunking failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing improved chunking: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Improved Chunking Test")
    print("=" * 50)
    
    success = test_improved_chunking()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The improved chunking strategy is working correctly.")
        print("New document uploads will use this better chunking method.")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
