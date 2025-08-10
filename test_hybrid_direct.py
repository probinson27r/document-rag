#!/usr/bin/env python3
"""
Direct test of hybrid search functionality
"""

from hybrid_search import HybridSearch
import sys

def test_hybrid_search_direct():
    """Test hybrid search directly"""
    
    print("Testing Hybrid Search Directly")
    print("=" * 50)
    
    try:
        # Initialize hybrid search
        hybrid_search = HybridSearch()
        print("✅ Hybrid search initialized successfully")
        
        # Test queries
        test_queries = [
            "What is Section 11.4 about?",
            "Section 11.4",
            "11.4",
            "No commitment",
            "Tell me about the no commitment section"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            try:
                results = hybrid_search.search_with_fallback(query, 3)
                
                if results:
                    print(f"✅ Found {len(results)} results")
                    
                    found_11_4 = False
                    for i, result in enumerate(results):
                        contains_11_4 = '11.4' in result['text']
                        if contains_11_4:
                            found_11_4 = True
                        
                        relevance = '✓ RELEVANT' if contains_11_4 else '✗ NOT RELEVANT'
                        score = result.get('combined_score', 1.0 - result['distance'])
                        
                        print(f"  {i+1}. Score: {score:.4f} | {relevance}")
                        print(f"     Type: {result.get('search_type', 'unknown')}")
                        print(f"     Text: {result['text'][:100]}...")
                        
                        if contains_11_4:
                            print(f"     ✓ Found 11.4 in this result!")
                    
                    if found_11_4:
                        print(f"✅ Query '{query}' successfully found Section 11.4!")
                    else:
                        print(f"⚠️ Query '{query}' did not find Section 11.4")
                        
                else:
                    print(f"❌ No results found for '{query}'")
                    
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
                
    except Exception as e:
        print(f"❌ Error initializing hybrid search: {e}")
        return False
    
    return True

def test_integration_with_document_rag():
    """Test integration with DocumentRAG class"""
    
    print("\n\nTesting Integration with DocumentRAG")
    print("=" * 50)
    
    try:
        from document_rag import DocumentRAG
        
        # Initialize DocumentRAG
        rag = DocumentRAG()
        print("✅ DocumentRAG initialized successfully")
        
        # Test search
        test_query = "What is Section 11.4 about?"
        print(f"\nTesting search with: '{test_query}'")
        
        search_results = rag.search_documents(test_query, 3)
        
        if search_results:
            print(f"✅ Found {len(search_results)} results")
            
            found_11_4 = False
            for i, result in enumerate(search_results):
                contains_11_4 = '11.4' in result['document']
                if contains_11_4:
                    found_11_4 = True
                
                relevance = '✓ RELEVANT' if contains_11_4 else '✗ NOT RELEVANT'
                distance = result.get('distance', 0)
                search_type = result.get('search_type', 'unknown')
                
                print(f"  {i+1}. Distance: {distance:.4f} | {relevance}")
                print(f"     Type: {search_type}")
                print(f"     Text: {result['document'][:100]}...")
                
                if contains_11_4:
                    print(f"     ✓ Found 11.4 in this result!")
            
            if found_11_4:
                print(f"✅ DocumentRAG successfully found Section 11.4!")
                return True
            else:
                print(f"⚠️ DocumentRAG did not find Section 11.4")
                return False
        else:
            print(f"❌ No results found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DocumentRAG integration: {e}")
        return False

if __name__ == "__main__":
    print("Hybrid Search Direct Test")
    print("=" * 50)
    
    # Test hybrid search directly
    hybrid_success = test_hybrid_search_direct()
    
    # Test integration with DocumentRAG
    rag_success = test_integration_with_document_rag()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Hybrid Search: {'✅ PASS' if hybrid_success else '❌ FAIL'}")
    print(f"DocumentRAG Integration: {'✅ PASS' if rag_success else '❌ FAIL'}")
    
    if hybrid_success and rag_success:
        print("\n🎉 All tests passed! Hybrid search is working correctly.")
        print("You can now use it in your Flask app.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        sys.exit(1)
