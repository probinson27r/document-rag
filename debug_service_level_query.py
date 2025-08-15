#!/usr/bin/env python3
"""
Debug service level query to understand why no results are returned
"""

import chromadb
import re
from typing import List, Dict

def search_for_service_level_content():
    """Search for service level content in ChromaDB"""
    
    print("🔍 Searching for Service Level Content")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks
        results = collection.get(limit=1000)
        
        print(f"📊 Total chunks in database: {len(results['ids'])}")
        
        # Search for service level content
        service_level_chunks = []
        service_level_keywords = [
            'service level',
            'sla',
            'kpi',
            'metric',
            'requirement',
            'bundle',
            'availability',
            'uptime',
            'performance',
            'report',
            'frequency',
            'mechanism',
            'ref.',
            '%',
            'hours',
            'days'
        ]
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Check for service level keywords
            content_lower = content.lower()
            matches = []
            
            for keyword in service_level_keywords:
                if keyword in content_lower:
                    matches.append(keyword)
            
            if matches:
                service_level_chunks.append({
                    'chunk_id': chunk_id,
                    'content': content,
                    'metadata': metadata,
                    'matches': matches,
                    'index': i
                })
        
        print(f"📊 Found {len(service_level_chunks)} chunks with service level content")
        
        if service_level_chunks:
            print(f"\n🎯 Service Level Chunks Found:")
            for chunk in service_level_chunks[:10]:  # Show first 10
                print(f"\nChunk #{chunk['index']}: {chunk['chunk_id']}")
                print(f"  Matches: {', '.join(chunk['matches'])}")
                print(f"  Content preview: {chunk['content'][:200]}...")
        else:
            print(f"\n❌ No service level content found!")
            print(f"   This means the document needs to be reprocessed with OCR enabled")
        
        return service_level_chunks
        
    except Exception as e:
        print(f"❌ Error searching for service level content: {e}")
        return None

def test_semantic_search():
    """Test semantic search for service level query"""
    
    print(f"\n🧪 Testing Semantic Search")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Test query
        test_query = "Provide a full breakdown of each service level, including the specific requirements and metrics, include the Service Bundle Ref. column from the table"
        
        print(f"🔍 Testing query: '{test_query}'")
        
        # Perform semantic search
        search_results = collection.query(
            query_texts=[test_query],
            n_results=5
        )
        
        print(f"📊 Search returned {len(search_results['ids'][0])} results")
        
        if search_results['ids'][0]:
            print(f"\n🎯 Top Search Results:")
            for i, (chunk_id, content, distance) in enumerate(zip(search_results['ids'][0], search_results['documents'][0], search_results['distances'][0])):
                print(f"\nResult {i+1}: {chunk_id}")
                print(f"  Distance: {distance}")
                print(f"  Content preview: {content[:200]}...")
                
                # Check if this result contains service level content
                content_lower = content.lower()
                has_service_level = any(keyword in content_lower for keyword in ['service level', 'sla', 'kpi', 'metric', 'requirement'])
                print(f"  Has service level content: {has_service_level}")
        else:
            print(f"❌ No search results returned!")
        
        return search_results
        
    except Exception as e:
        print(f"❌ Error testing semantic search: {e}")
        return None

def check_chunk_content_quality():
    """Check the quality of chunk content"""
    
    print(f"\n🔍 Checking Chunk Content Quality")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get first 20 chunks
        results = collection.get(limit=20)
        
        print(f"📊 Analyzing first {len(results['ids'])} chunks:")
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\nChunk {i+1}: {chunk_id}")
            print(f"  Content length: {len(content)} characters")
            print(f"  Extraction method: {metadata.get('extraction_method', 'unknown')}")
            print(f"  Chunking method: {metadata.get('chunking_method', 'unknown')}")
            
            # Check content quality
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            print(f"  Non-empty lines: {len(non_empty_lines)}")
            
            # Show first few lines
            for j, line in enumerate(non_empty_lines[:3]):
                print(f"    Line {j+1}: {line}")
            
            if len(non_empty_lines) > 3:
                print(f"    ... and {len(non_empty_lines) - 3} more lines")
        
    except Exception as e:
        print(f"❌ Error checking chunk content quality: {e}")

def suggest_reprocessing_steps():
    """Suggest steps to reprocess the document"""
    
    print(f"\n💡 Reprocessing Steps")
    print("=" * 50)
    
    steps = """
## Steps to Fix Service Level Query

### Step 1: Clear Current Data
```bash
# Backup current data
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)

# Clear current chunks
rm -rf chroma_db/*
```

### Step 2: Re-upload Document with Correct Settings
1. Go to your web interface
2. Upload the document again
3. Use these **exact settings**:
   - **Extraction Method**: Traditional (for better table extraction)
   - **Chunking Method**: Semantic (uses table-aware chunking)
   - **Enable OCR**: True (for better table detection)
   - **Text Enhancement**: Enabled
   - **Structured Data**: Enabled

### Step 3: Verify Processing
After upload, check the logs for:
```
[DEBUG] OCR enabled: True
[OCR] OCR is enabled - processing with image conversion...
[DEBUG] Table-aware chunking enabled
```

### Step 4: Test the Query
After reprocessing, test with:
> "Provide a full breakdown of each service level, including the specific requirements and metrics, include the Service Bundle Ref. column from the table"

### Expected Results:
- ✅ Complete service level tables
- ✅ All metrics and requirements
- ✅ Service Bundle Ref. column data
- ✅ Full table structure preserved

### Why This Will Work:
1. **OCR Enabled**: Better text extraction from PDFs
2. **Traditional Extraction**: Better table detection
3. **Table-Aware Chunking**: Preserves complete tables
4. **Semantic Chunking**: Better content organization
"""
    
    print(steps)

if __name__ == "__main__":
    # Search for service level content
    service_level_chunks = search_for_service_level_content()
    
    # Test semantic search
    search_results = test_semantic_search()
    
    # Check chunk content quality
    check_chunk_content_quality()
    
    # Suggest reprocessing steps
    suggest_reprocessing_steps()
    
    print(f"\n🎯 Summary:")
    print("=" * 50)
    if service_level_chunks:
        print(f"✅ Found {len(service_level_chunks)} chunks with service level content")
        print(f"   - Content exists but may not be searchable")
        print(f"   - May need to reprocess with better settings")
    else:
        print(f"❌ No service level content found!")
        print(f"   - Document needs to be reprocessed with OCR enabled")
        print(f"   - Current extraction may not have captured tables properly")
    
    if search_results and search_results['ids'][0]:
        print(f"✅ Semantic search is working")
        print(f"   - Found {len(search_results['ids'][0])} results")
        print(f"   - May need to improve search relevance")
    else:
        print(f"❌ Semantic search returned no results")
        print(f"   - Indicates content quality issues")
        print(f"   - Reprocessing required")
    
    print(f"\n🔧 Next Action: Reprocess document with OCR enabled and table-aware chunking")
