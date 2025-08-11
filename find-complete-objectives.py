#!/usr/bin/env python3
"""
Find all chunks containing Section 3.2 objectives to see the complete list
"""

import chromadb
import re

def find_all_objectives():
    """
    Find all chunks that might contain parts of Section 3.2 objectives
    """
    print("🔍 Finding all Section 3.2 objectives chunks...")
    
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
        
        # Search for different patterns that might contain the objectives
        search_terms = [
            "3.2 List of Objectives",
            "objectives of this Agreement",
            "objectives are to",
            "(a) The objectives",
            "(b)",
            "(c)",
            "(d)",
            "(e)",
            "Agreement are to"
        ]
        
        all_relevant_chunks = {}  # Use dict to avoid duplicates
        
        for term in search_terms:
            print(f"\n🔍 Searching for: '{term}'")
            
            results = collection.query(
                query_texts=[term],
                n_results=10,
                include=['documents', 'metadatas']
            )
            
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                chunk_id = metadata.get('chunk_id', 'unknown')
                
                # Check if this chunk is related to Section 3.2 objectives
                if ('3.2' in doc or 'objective' in doc.lower()) and any(pattern in doc for pattern in ['(a)', '(b)', '(c)', '(d)', '(e)', 'Agreement are to']):
                    all_relevant_chunks[chunk_id] = {
                        'content': doc,
                        'metadata': metadata,
                        'search_term': term
                    }
                    print(f"   ✅ Found relevant chunk: {chunk_id}")
        
        print(f"\n📊 Found {len(all_relevant_chunks)} unique relevant chunks")
        
        # Sort chunks and analyze them
        print("\n📋 All Section 3.2 objectives-related chunks:")
        print("=" * 80)
        
        for i, (chunk_id, chunk_data) in enumerate(all_relevant_chunks.items()):
            content = chunk_data['content']
            metadata = chunk_data['metadata']
            
            print(f"\n📄 Chunk {i+1}: {chunk_id}")
            print(f"   Found via: {chunk_data['search_term']}")
            print(f"   Section: {metadata.get('section_number', 'Unknown')}")
            print(f"   Title: {metadata.get('section_title', 'Unknown')}")
            print(f"   Length: {len(content)} characters")
            print(f"   Content:")
            
            # Look for enumerated objectives
            lines = content.split('\n')
            in_objectives = False
            
            for line_num, line in enumerate(lines):
                line_clean = line.strip()
                
                # Check if this line contains objectives
                if 'List of Objectives' in line or 'objectives of this Agreement' in line:
                    in_objectives = True
                    print(f"      📌 {line_clean}")
                elif in_objectives and line_clean:
                    # Check for enumerated items or continuation
                    if re.match(r'\([a-z]\)', line_clean) or 'Agreement are to' in line_clean or line_clean.startswith('('):
                        print(f"      🎯 {line_clean}")
                    elif line_clean.startswith('##') and '3.3' in line_clean:
                        print(f"      📌 {line_clean}")
                        break  # End of section 3.2
                    elif line_clean and not line_clean.startswith('...'):
                        print(f"      📝 {line_clean}")
                elif '(a)' in line_clean or '(b)' in line_clean or '(c)' in line_clean:
                    print(f"      🎯 {line_clean}")
                elif line_clean and (i < 3 or 'Agreement are to' in line_clean):  # Show first few lines or key content
                    print(f"      📝 {line_clean}")
            
            print("   " + "─" * 70)
        
        # Try to reconstruct the complete objectives
        print(f"\n🔧 Attempting to reconstruct complete Section 3.2 objectives:")
        print("=" * 80)
        
        complete_objectives = []
        
        for chunk_data in all_relevant_chunks.values():
            content = chunk_data['content']
            
            # Look for enumerated objectives
            lines = content.split('\n')
            for line in lines:
                line_clean = line.strip()
                
                # Look for objectives patterns
                if re.match(r'\([a-z]\)', line_clean):
                    complete_objectives.append(line_clean)
                elif 'objectives of this Agreement are to' in line_clean:
                    complete_objectives.append(line_clean)
                elif 'Agreement are to' in line_clean and '(a)' not in line_clean:
                    complete_objectives.append(line_clean)
        
        if complete_objectives:
            print("📋 Reconstructed objectives:")
            for obj in complete_objectives:
                print(f"   {obj}")
        else:
            print("❌ Could not reconstruct complete objectives from chunks")
            print("   This suggests the objectives may be split across chunks")
            print("   or the content might be incomplete in the chunking process")
        
        return all_relevant_chunks
        
    except Exception as e:
        print(f"❌ Error finding objectives: {e}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    print("🎯 Finding Complete Section 3.2 Objectives")
    print("=" * 60)
    
    chunks = find_all_objectives()
    
    print(f"\n🎯 Summary:")
    print(f"   Total relevant chunks found: {len(chunks)}")
    
    if chunks:
        print("\n💡 Recommendations:")
        print("   1. The objectives exist but may be split across multiple chunks")
        print("   2. The chunking strategy should be improved to keep complete lists together")
        print("   3. Consider re-processing the document with better section preservation")
    else:
        print("   ❌ No complete objectives found - document may need to be re-uploaded/processed")
