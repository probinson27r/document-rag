#!/usr/bin/env python3
"""
Fix Section 3.2 chunking issue by creating a query enhancement that combines
related chunks for complete section responses.
"""

import chromadb
import re
from typing import List, Dict, Any

def find_section_chunks(section_number: str) -> List[Dict[str, Any]]:
    """
    Find all chunks related to a specific section number
    """
    print(f"🔍 Finding all chunks for section {section_number}...")
    
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
        
        # Search for the section in multiple ways
        search_patterns = [
            f"Section {section_number}",
            f"## {section_number}",
            f"{section_number} ",
            f"clause {section_number}",
            f"paragraph {section_number}"
        ]
        
        all_chunks = {}
        
        for pattern in search_patterns:
            results = collection.query(
                query_texts=[pattern],
                n_results=20,
                include=['documents', 'metadatas', 'distances']
            )
            
            for doc, metadata, distance in zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            ):
                # Check if this chunk contains the section number
                if section_number in doc:
                    chunk_id = metadata.get('chunk_id', f'chunk_{hash(doc[:50])}')
                    all_chunks[chunk_id] = {
                        'content': doc,
                        'metadata': metadata,
                        'distance': distance,
                        'relevance_score': 1.0 - distance
                    }
        
        # Sort by relevance
        sorted_chunks = sorted(all_chunks.values(), key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"   ✅ Found {len(sorted_chunks)} chunks for section {section_number}")
        return sorted_chunks
        
    except Exception as e:
        print(f"   ❌ Error finding section chunks: {e}")
        return []

def reconstruct_section(section_number: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Reconstruct a complete section from multiple chunks
    """
    print(f"🔧 Reconstructing section {section_number} from {len(chunks)} chunks...")
    
    # Identify section parts
    section_header = ""
    section_content = []
    objectives_parts = []
    
    for chunk in chunks:
        content = chunk['content']
        lines = content.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            
            # Look for section header
            if f"{section_number}" in line_clean and any(keyword in line_clean.lower() for keyword in ['objective', 'list']):
                if not section_header or len(line_clean) > len(section_header):
                    section_header = line_clean
            
            # Look for enumerated objectives
            if re.match(r'\([a-z]\)', line_clean):
                objectives_parts.append(line_clean)
            elif 'objectives of this Agreement are to' in line_clean:
                objectives_parts.append(line_clean)
            elif line_clean and section_number in content and not line_clean.startswith('##') and not line_clean.startswith('...'):
                # Other content from this section
                if line_clean not in section_content and len(line_clean) > 10:
                    section_content.append(line_clean)
    
    # Reconstruct the section
    reconstructed = []
    
    if section_header:
        reconstructed.append(section_header)
        reconstructed.append("")
    
    if objectives_parts:
        # Sort objectives alphabetically
        objectives_parts.sort()
        reconstructed.extend(objectives_parts)
        reconstructed.append("")
    
    if section_content:
        reconstructed.extend(section_content)
    
    result = '\n'.join(reconstructed).strip()
    
    if result:
        print(f"   ✅ Successfully reconstructed section {section_number}")
        return result
    else:
        print(f"   ❌ Could not reconstruct section {section_number}")
        # Fall back to just combining all content
        return '\n\n'.join([chunk['content'] for chunk in chunks[:3]])

def enhanced_section_query(query: str) -> str:
    """
    Enhanced query processing that combines chunks for complete section responses
    """
    print(f"🚀 Processing enhanced section query: '{query}'")
    
    # Extract section number from query
    section_match = re.search(r'(\d+\.\d+)', query)
    if not section_match:
        print("   ❌ No section number found in query")
        return "No section number found in query"
    
    section_number = section_match.group(1)
    print(f"   🎯 Target section: {section_number}")
    
    # Find all related chunks
    chunks = find_section_chunks(section_number)
    
    if not chunks:
        return f"No content found for section {section_number}"
    
    # Reconstruct the complete section
    complete_section = reconstruct_section(section_number, chunks)
    
    # Enhance the response based on query intent
    if 'objective' in query.lower():
        # Focus on objectives
        lines = complete_section.split('\n')
        objectives_only = []
        
        for line in lines:
            if 'objective' in line.lower() or re.match(r'\([a-z]\)', line.strip()):
                objectives_only.append(line)
        
        if objectives_only:
            complete_section = '\n'.join(objectives_only)
    
    return complete_section

def test_enhanced_query():
    """
    Test the enhanced query processing
    """
    print("\n🧪 Testing enhanced section query processing...")
    
    test_queries = [
        "Give me the objectives in Section 3.2",
        "Section 3.2 objectives",
        "What are the objectives in section 3.2?",
        "List the objectives from section 3.2"
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: '{query}'")
        result = enhanced_section_query(query)
        print(f"📄 Result ({len(result)} chars):")
        print("─" * 60)
        print(result)
        print("─" * 60)

if __name__ == "__main__":
    print("🔧 Fixing Section 3.2 Chunking Issue")
    print("=" * 60)
    
    # Test the enhanced query processing
    test_enhanced_query()
    
    print("\n🎯 Solution Summary:")
    print("This script demonstrates how to combine related chunks to provide")
    print("complete section responses, which solves the chunking split issue.")
    print("\nTo implement this fix permanently:")
    print("1. Integrate this logic into the hybrid_search.py search_with_fallback method")
    print("2. Detect section queries and use enhanced reconstruction")
    print("3. Consider re-processing documents with better chunking strategies")
