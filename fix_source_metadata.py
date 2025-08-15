#!/usr/bin/env python3
"""
Fix source metadata by extracting section information from chunk content
"""

import chromadb
import re
from typing import List, Dict, Tuple, Optional

def extract_section_info_from_content(content: str) -> Tuple[str, str]:
    """
    Extract section number and title from chunk content
    
    Args:
        content: Chunk content
        
    Returns:
        Tuple of (section_number, section_title)
    """
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for section headers with ##
        if line.startswith('##'):
            # Pattern: ## 3.2 List of Objectives
            section_match = re.match(r'^##\s*(\d+(?:\.\d+)?)\s+(.+)$', line)
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2).strip()
                return section_number, section_title
        
        # Check for section headers without ##
        # Pattern: 3.2 List of Objectives
        section_match = re.match(r'^(\d+(?:\.\d+)?)\s+([A-Z][A-Za-z\s]+)$', line)
        if section_match:
            section_number = section_match.group(1)
            section_title = line.strip()
            return section_number, section_title
        
        # Check for clause patterns
        # Pattern: 1.1 Definitions
        clause_match = re.match(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)', line)
        if clause_match:
            section_number = clause_match.group(1)
            section_title = f"{section_number} {clause_match.group(2).strip()}"
            return section_number, section_title
    
    return '', ''

def fix_chromadb_metadata():
    """Fix the metadata in ChromaDB by extracting section information from content"""
    
    print("🔧 Fixing ChromaDB Metadata for Sources")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks
        results = collection.get(limit=1000)
        
        print(f"📊 Found {len(results['ids'])} chunks to process")
        
        # Track changes
        updated_chunks = 0
        chunks_with_sections = 0
        
        # Process each chunk
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Check if this chunk already has section information
            current_section_number = metadata.get('section_number', '')
            current_section_title = metadata.get('section_title', '')
            
            if current_section_number and current_section_title and current_section_number != 'Unknown':
                chunks_with_sections += 1
                continue
            
            # Extract section information from content
            section_number, section_title = extract_section_info_from_content(content)
            
            if section_number and section_title:
                # Update metadata
                metadata['section_number'] = section_number
                metadata['section_title'] = section_title
                
                # Update the chunk in ChromaDB
                collection.update(
                    ids=[chunk_id],
                    metadatas=[metadata]
                )
                
                updated_chunks += 1
                print(f"✅ Updated chunk {i+1}: {section_number} - {section_title}")
        
        print(f"\n📊 Summary:")
        print(f"  Total chunks processed: {len(results['ids'])}")
        print(f"  Chunks already had section info: {chunks_with_sections}")
        print(f"  Chunks updated with section info: {updated_chunks}")
        print(f"  Chunks still missing section info: {len(results['ids']) - chunks_with_sections - updated_chunks}")
        
        return {
            'total_chunks': len(results['ids']),
            'chunks_with_sections': chunks_with_sections,
            'updated_chunks': updated_chunks,
            'missing_sections': len(results['ids']) - chunks_with_sections - updated_chunks
        }
        
    except Exception as e:
        print(f"❌ Error fixing metadata: {e}")
        return None

if __name__ == "__main__":
    # Fix the metadata
    fix_result = fix_chromadb_metadata()
    
    print(f"\n🎯 Final Summary:")
    print("=" * 50)
    if fix_result:
        print(f"✅ Metadata fix completed:")
        print(f"  - Updated {fix_result['updated_chunks']} chunks with section information")
        print(f"  - {fix_result['chunks_with_sections']} chunks already had section info")
        print(f"  - {fix_result['missing_sections']} chunks still missing section info")
