#!/usr/bin/env python3
"""
Clean up section titles by removing page numbers and formatting dots
"""

import chromadb
import re

def clean_section_title(title: str) -> str:
    """
    Clean up section title by removing page numbers and formatting dots
    
    Args:
        title: Raw section title
        
    Returns:
        Cleaned section title
    """
    if not title:
        return title
    
    # Remove page numbers at the end (e.g., "................ 8")
    title = re.sub(r'\s*\.+\s*\d+\s*$', '', title)
    
    # Remove multiple dots/periods
    title = re.sub(r'\.{2,}', '', title)
    
    # Clean up extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def clean_chromadb_titles():
    """Clean up section titles in ChromaDB"""
    
    print("🧹 Cleaning Section Titles in ChromaDB")
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
        
        # Process each chunk
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            current_section_title = metadata.get('section_title', '')
            
            if not current_section_title:
                continue
            
            # Clean the section title
            cleaned_title = clean_section_title(current_section_title)
            
            if cleaned_title != current_section_title:
                # Update metadata
                metadata['section_title'] = cleaned_title
                
                # Update the chunk in ChromaDB
                collection.update(
                    ids=[chunk_id],
                    metadatas=[metadata]
                )
                
                updated_chunks += 1
                print(f"✅ Cleaned chunk {i+1}: '{current_section_title}' → '{cleaned_title}'")
        
        print(f"\n📊 Summary:")
        print(f"  Total chunks processed: {len(results['ids'])}")
        print(f"  Chunks with cleaned titles: {updated_chunks}")
        
        return {
            'total_chunks': len(results['ids']),
            'updated_chunks': updated_chunks
        }
        
    except Exception as e:
        print(f"❌ Error cleaning titles: {e}")
        return None

def test_clean_sources():
    """Test the source generation with cleaned titles"""
    
    print(f"\n🧪 Testing Clean Source Generation:")
    print("-" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get a few chunks to test
        results = collection.get(limit=5)
        
        print(f"Testing source generation for {len(results['ids'])} chunks:")
        print()
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            filename = metadata.get('filename', 'Unknown Document')
            section_number = metadata.get('section_number', 'Unknown')
            section_title = metadata.get('section_title', 'Unknown')
            
            section_info = f"{section_number} - {section_title}"
            source_info = f"{filename}: {section_info}"
            
            print(f"Chunk {i+1}:")
            print(f"  Content preview: {content[:100]}...")
            print(f"  Section number: '{section_number}'")
            print(f"  Section title: '{section_title}'")
            print(f"  Generated source: '{source_info}'")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing clean sources: {e}")
        return False

if __name__ == "__main__":
    # Clean the titles
    clean_result = clean_chromadb_titles()
    
    # Test clean source generation
    test_success = test_clean_sources()
    
    print(f"\n🎯 Final Summary:")
    print("=" * 50)
    if clean_result:
        print(f"✅ Title cleaning completed:")
        print(f"  - Updated {clean_result['updated_chunks']} chunks with cleaned titles")
        print(f"  - Total chunks processed: {clean_result['total_chunks']}")
    
    if test_success:
        print(f"✅ Clean source generation test completed successfully!")
        print(f"  Sources now show clean, readable section information")
    else:
        print(f"❌ Clean source generation test failed")
