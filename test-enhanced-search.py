#!/usr/bin/env python3
"""
Test the enhanced section search functionality
"""

from hybrid_search import HybridSearch

def test_enhanced_section_search():
    """
    Test the enhanced Section 3.2 reconstruction
    """
    print("🧪 Testing Enhanced Section 3.2 Search")
    print("=" * 60)
    
    # Initialize hybrid search
    hybrid_search = HybridSearch()
    
    # Test the specific problematic query
    test_queries = [
        "Give me the objectives in Section 3.2",
        "Section 3.2 objectives", 
        "What are the objectives in section 3.2?",
        "List the objectives from section 3.2"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n🔍 Test {i+1}: '{query}'")
        print("─" * 50)
        
        # Run the enhanced search
        results = hybrid_search.search_with_fallback(query, n_results=3)
        
        print(f"📊 Found {len(results)} results")
        
        for j, result in enumerate(results):
            result_type = result.get('search_type', 'unknown')
            score = result.get('combined_score', 1.0 - result.get('distance', 1.0))
            
            print(f"\n📄 Result {j+1}:")
            print(f"   Type: {result_type}")
            print(f"   Score: {score:.4f}")
            print(f"   ID: {result.get('id', 'unknown')}")
            
            if result_type == 'reconstructed_section':
                print(f"   🎯 RECONSTRUCTED SECTION (from {result.get('source_chunks', 0)} chunks)")
                print(f"   Content:")
                print("   " + "─" * 45)
                content = result['text']
                for line in content.split('\n'):
                    if line.strip():
                        print(f"   {line}")
                print("   " + "─" * 45)
                
                # Check if we found objectives
                objectives_found = content.count('(')
                print(f"   📋 Objectives found: {objectives_found}")
                
                if '(a)' in content and '(b)' in content:
                    print("   ✅ SUCCESS: Found multiple objectives!")
                elif 'objective' in content.lower():
                    print("   ⚡ PARTIAL: Found objectives content but may be incomplete")
                else:
                    print("   ❌ FAILED: No clear objectives found")
            else:
                print(f"   Content preview: {result['text'][:200]}...")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    test_enhanced_section_search()
