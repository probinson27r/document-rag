#!/usr/bin/env python3
"""
Debug script to examine why sources are showing "Unknown" in responses
"""

import chromadb
import json

def debug_sources():
    """Debug the source generation issue"""
    
    print("🔍 Debugging Source Generation Issue")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks with metadata
        results = collection.get(limit=10)
        
        print(f"📊 Examining first 10 chunks:")
        print()
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"Chunk {i+1}: {chunk_id}")
            print(f"  Content length: {len(content)} characters")
            print(f"  Content preview: {content[:100]}...")
            print(f"  Metadata:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
            print("-" * 80)
        
        # Test the source generation logic
        print(f"\n🧪 Testing Source Generation Logic:")
        print("-" * 50)
        
        # Simulate the source generation from app.py
        sources = []
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            filename = metadata.get('filename', 'Unknown Document')
            section_number = metadata.get('section_number', 'Unknown')
            section_title = metadata.get('section_title', 'Unknown')
            
            section_info = f"{section_number} - {section_title}"
            source_info = f"{filename}: {section_info}"
            
            print(f"Chunk {i+1}:")
            print(f"  Filename: '{filename}'")
            print(f"  Section number: '{section_number}'")
            print(f"  Section title: '{section_title}'")
            print(f"  Generated source: '{source_info}'")
            print()
            
            sources.append(source_info)
        
        # Check if any chunks have proper section information
        print(f"\n📋 Section Information Analysis:")
        print("-" * 50)
        
        chunks_with_sections = 0
        chunks_without_sections = 0
        
        for metadata in results['metadatas']:
            section_number = metadata.get('section_number', '')
            section_title = metadata.get('section_title', '')
            
            if section_number and section_number != 'Unknown' and section_title and section_title != 'Unknown':
                chunks_with_sections += 1
                print(f"✅ Chunk has section info: {section_number} - {section_title}")
            else:
                chunks_without_sections += 1
                print(f"❌ Chunk missing section info: section_number='{section_number}', section_title='{section_title}'")
        
        print(f"\n📊 Summary:")
        print(f"  Chunks with section info: {chunks_with_sections}")
        print(f"  Chunks without section info: {chunks_without_sections}")
        print(f"  Total chunks examined: {len(results['metadatas'])}")
        
        # Check the chunking process
        print(f"\n🔍 Examining Chunking Process:")
        print("-" * 50)
        
        # Look for chunks that should have section information
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Check if content contains section headers
            if '##' in content or 'Section' in content or any(section in content for section in ['3.2', '11.4', '5.', '6.']):
                print(f"Chunk {i+1} contains section-like content:")
                print(f"  ID: {chunk_id}")
                print(f"  Content preview: {content[:200]}...")
                print(f"  Section number in metadata: '{metadata.get('section_number', 'MISSING')}'")
                print(f"  Section title in metadata: '{metadata.get('section_title', 'MISSING')}'")
                print()
        
        return {
            'total_chunks': len(results['metadatas']),
            'chunks_with_sections': chunks_with_sections,
            'chunks_without_sections': chunks_without_sections
        }
        
    except Exception as e:
        print(f"❌ Error debugging sources: {e}")
        return None

def test_hybrid_search_sources():
    """Test how hybrid search results are processed for sources"""
    
    print(f"\n🧪 Testing Hybrid Search Source Generation:")
    print("-" * 50)
    
    try:
        from hybrid_search import HybridSearch
        
        # Initialize hybrid search
        hybrid_search = HybridSearch()
        
        # Test a query
        test_query = "contract objectives"
        results = hybrid_search.search_with_fallback(test_query, 3)
        
        print(f"Query: '{test_query}'")
        print(f"Found {len(results)} results")
        print()
        
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  ID: {result['id']}")
            print(f"  Search type: {result.get('search_type', 'unknown')}")
            print(f"  Distance: {result['distance']:.4f}")
            print(f"  Content preview: {result['text'][:100]}...")
            print()
        
        # Simulate the source generation from app.py
        print(f"Simulating source generation:")
        print("-" * 30)
        
        import chromadb
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        sources = []
        for result in results:
            try:
                metadata_result = collection.get(
                    ids=[result['id']],
                    include=['metadatas']
                )
                if metadata_result['metadatas']:
                    metadata = metadata_result['metadatas'][0]
                    filename = metadata.get('filename', 'Unknown Document')
                    section_info = f"{metadata.get('section_number', 'Unknown')} - {metadata.get('section_title', 'Unknown')}"
                    source_info = f"{filename}: {section_info}"
                    sources.append(source_info)
                    print(f"  Generated source: '{source_info}'")
                else:
                    sources.append(f"Document chunk: {result['id']}")
                    print(f"  No metadata found: Document chunk: {result['id']}")
            except Exception as e:
                sources.append(f"Document chunk: {result['id']}")
                print(f"  Error getting metadata: {e}")
        
        return sources
        
    except Exception as e:
        print(f"❌ Error testing hybrid search sources: {e}")
        return None

if __name__ == "__main__":
    # Debug the sources
    debug_data = debug_sources()
    
    # Test hybrid search sources
    sources = test_hybrid_search_sources()
    
    print(f"\n🎯 Summary:")
    print("=" * 50)
    if debug_data:
        print(f"Total chunks examined: {debug_data['total_chunks']}")
        print(f"Chunks with section info: {debug_data['chunks_with_sections']}")
        print(f"Chunks without section info: {debug_data['chunks_without_sections']}")
        
        if debug_data['chunks_without_sections'] > 0:
            print(f"❌ Problem identified: {debug_data['chunks_without_sections']} chunks are missing section information")
            print("This is why sources are showing 'Unknown'")
        else:
            print(f"✅ All chunks have proper section information")
    
    if sources:
        print(f"Generated sources: {sources}")
