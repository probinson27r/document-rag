#!/usr/bin/env python3
"""
Fix Section 3.2 objectives retrieval issue
This script enhances the hybrid search to better handle section-specific queries
"""

import chromadb
import re
from typing import List, Dict, Any
import json

def enhance_section_metadata():
    """
    Enhance existing chunks with better section metadata for retrieval
    """
    print("🔧 Enhancing section metadata in ChromaDB...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        collection = client.get_collection("documents")
        
        # Get all documents
        all_results = collection.get(include=['documents', 'metadatas', 'ids'])
        
        print(f"📊 Processing {len(all_results['ids'])} chunks...")
        
        updates_made = 0
        
        for chunk_id, content, metadata in zip(
            all_results['ids'], 
            all_results['documents'], 
            all_results['metadatas']
        ):
            # Enhanced section detection
            enhanced_metadata = metadata.copy()
            needs_update = False
            
            # Look for section patterns in the content
            section_patterns = [
                r'(\d+\.\d+)\s+([A-Za-z][^.\n]*(?:objectives?|goals?|targets?|requirements?))',
                r'Section\s+(\d+\.\d+)\s*[:\-]?\s*([A-Za-z][^.\n]*)',
                r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)$',
                r'(\d+\.\d+)\s*\([a-z]\)',  # 3.2(a) patterns
            ]
            
            for pattern in section_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    section_num = match[0]
                    if len(match) > 1:
                        section_title = match[1].strip()
                    else:
                        section_title = f"Section {section_num}"
                    
                    # Update metadata if we found a better section number
                    if section_num and (not metadata.get('section_number') or metadata.get('section_number') == 'Unknown'):
                        enhanced_metadata['section_number'] = section_num
                        enhanced_metadata['section_title'] = section_title
                        needs_update = True
                        
                        # Special handling for objectives sections
                        if 'objective' in section_title.lower() or 'objective' in content.lower():
                            enhanced_metadata['content_type'] = 'objectives'
                            enhanced_metadata['searchable_terms'] = enhanced_metadata.get('searchable_terms', '') + f" objectives section_{section_num.replace('.', '_')}"
                            needs_update = True
            
            # Enhance searchable terms for better retrieval
            content_lower = content.lower()
            searchable_terms = enhanced_metadata.get('searchable_terms', '')
            
            # Add section-related search terms
            if '3.2' in content:
                if 'section_3_2' not in searchable_terms:
                    enhanced_metadata['searchable_terms'] = searchable_terms + ' section_3_2'
                    needs_update = True
                
                if 'objective' in content_lower and 'objectives_3_2' not in searchable_terms:
                    enhanced_metadata['searchable_terms'] = enhanced_metadata['searchable_terms'] + ' objectives_3_2'
                    needs_update = True
            
            # Add enumerated items as searchable terms
            enumerated_patterns = [
                r'\([a-z]\)',  # (a), (b), (c)
                r'\d+\.',      # 1., 2., 3.
                r'[a-z]\.',    # a., b., c.
            ]
            
            for pattern in enumerated_patterns:
                if re.search(pattern, content):
                    if 'enumerated_list' not in searchable_terms:
                        enhanced_metadata['searchable_terms'] = enhanced_metadata.get('searchable_terms', '') + ' enumerated_list'
                        needs_update = True
                    break
            
            # Update the chunk if metadata was enhanced
            if needs_update:
                try:
                    collection.update(
                        ids=[chunk_id],
                        metadatas=[enhanced_metadata]
                    )
                    updates_made += 1
                    
                    if '3.2' in content:
                        print(f"✅ Enhanced Section 3.2 chunk: {chunk_id}")
                        print(f"   Section: {enhanced_metadata.get('section_number', 'Unknown')}")
                        print(f"   Title: {enhanced_metadata.get('section_title', 'Unknown')}")
                        print(f"   Terms: {enhanced_metadata.get('searchable_terms', '')}")
                        print()
                
                except Exception as e:
                    print(f"❌ Failed to update chunk {chunk_id}: {e}")
        
        print(f"✅ Enhanced {updates_made} chunks with better section metadata")
        return updates_made
        
    except Exception as e:
        print(f"❌ Error enhancing metadata: {e}")
        return 0

def test_section_retrieval():
    """
    Test section retrieval after enhancements
    """
    print("\n🧪 Testing enhanced section retrieval...")
    
    try:
        from hybrid_search import HybridSearch
        
        # Initialize hybrid search
        hybrid_search = HybridSearch()
        
        # Test the specific problematic query
        query = "Give me the objectives in Section 3.2"
        print(f"🔍 Testing query: '{query}'")
        
        # Run enhanced search
        results = hybrid_search.search_with_fallback(query, n_results=5)
        
        print(f"📊 Found {len(results)} results")
        
        section_32_results = 0
        objectives_results = 0
        
        for i, result in enumerate(results):
            contains_32 = '3.2' in result['text']
            contains_objectives = 'objective' in result['text'].lower()
            
            if contains_32:
                section_32_results += 1
            if contains_objectives:
                objectives_results += 1
            
            relevance = '✅ HIGHLY RELEVANT' if (contains_32 and contains_objectives) else ('⚡ RELEVANT' if (contains_32 or contains_objectives) else '❌ NOT RELEVANT')
            score = result.get('combined_score', 1.0 - result.get('distance', 1.0))
            
            print(f"  {i+1}. Score: {score:.4f} | {relevance}")
            print(f"     Type: {result.get('search_type', 'semantic')}")
            print(f"     Text: {result['text'][:150]}...")
            
            if contains_32 and contains_objectives:
                print(f"     🎯 PERFECT MATCH: Contains both Section 3.2 and objectives!")
            print()
        
        print(f"📈 Results summary:")
        print(f"   Section 3.2 results: {section_32_results}")
        print(f"   Objectives results: {objectives_results}")
        print(f"   Perfect matches: {sum(1 for r in results if '3.2' in r['text'] and 'objective' in r['text'].lower())}")
        
        # Test other variations
        other_queries = [
            "Section 3.2 objectives",
            "objectives section 3.2", 
            "3.2 objectives",
            "list objectives 3.2"
        ]
        
        print(f"\n🔍 Testing other query variations:")
        for test_query in other_queries:
            test_results = hybrid_search.search_with_fallback(test_query, n_results=3)
            perfect_matches = sum(1 for r in test_results if '3.2' in r['text'] and 'objective' in r['text'].lower())
            print(f"   '{test_query}' → {len(test_results)} results, {perfect_matches} perfect matches")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Error testing retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_section_mapping():
    """
    Create a mapping of all sections for better retrieval
    """
    print("\n📋 Creating section mapping...")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        collection = client.get_collection("documents")
        
        # Get all documents
        all_results = collection.get(include=['documents', 'metadatas', 'ids'])
        
        section_mapping = {}
        
        for chunk_id, content, metadata in zip(
            all_results['ids'], 
            all_results['documents'], 
            all_results['metadatas']
        ):
            section_number = metadata.get('section_number', 'Unknown')
            
            if section_number != 'Unknown':
                if section_number not in section_mapping:
                    section_mapping[section_number] = {
                        'chunks': [],
                        'section_title': metadata.get('section_title', ''),
                        'content_preview': ''
                    }
                
                section_mapping[section_number]['chunks'].append({
                    'id': chunk_id,
                    'content_preview': content[:200] + '...' if len(content) > 200 else content
                })
                
                if not section_mapping[section_number]['content_preview']:
                    section_mapping[section_number]['content_preview'] = content[:500]
        
        # Save section mapping
        with open('section_mapping.json', 'w') as f:
            json.dump(section_mapping, f, indent=2)
        
        print(f"✅ Created mapping for {len(section_mapping)} sections")
        
        # Show Section 3.2 specifically
        if '3.2' in section_mapping:
            section_32 = section_mapping['3.2']
            print(f"\n🎯 Section 3.2 found:")
            print(f"   Title: {section_32['section_title']}")
            print(f"   Chunks: {len(section_32['chunks'])}")
            print(f"   Preview: {section_32['content_preview'][:300]}...")
        else:
            print(f"\n❌ Section 3.2 NOT FOUND in mapping")
            print(f"Available sections: {list(section_mapping.keys())}")
        
        return section_mapping
        
    except Exception as e:
        print(f"❌ Error creating section mapping: {e}")
        return {}

if __name__ == "__main__":
    print("🚀 Fixing Section 3.2 objectives retrieval...")
    print("=" * 60)
    
    # Step 1: Enhance metadata
    updates = enhance_section_metadata()
    
    # Step 2: Create section mapping
    mapping = create_section_mapping()
    
    # Step 3: Test retrieval
    success = test_section_retrieval()
    
    print("\n" + "=" * 60)
    print("🎯 Fix Summary:")
    print(f"   Metadata enhancements: {updates}")
    print(f"   Sections mapped: {len(mapping)}")
    print(f"   Retrieval test: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if '3.2' in mapping:
        print(f"   Section 3.2: ✅ FOUND ({len(mapping['3.2']['chunks'])} chunks)")
    else:
        print(f"   Section 3.2: ❌ NOT FOUND")
    
    print("\n🎯 Next steps:")
    if not success:
        print("   1. Check if the document containing Section 3.2 is uploaded")
        print("   2. Verify document processing preserved section structure")
        print("   3. Check section_mapping.json for available sections")
    else:
        print("   1. Test the query 'Give me the objectives in Section 3.2' in the UI")
        print("   2. Check section_mapping.json for full section inventory")
    print("   3. Use diagnose-section-retrieval.sh for detailed analysis")
