#!/usr/bin/env python3
"""
Inspect the actual content being returned for Section 3.2 queries
"""

import chromadb
from hybrid_search import HybridSearch

def inspect_section_content():
    """
    Inspect the actual content being returned for Section 3.2
    """
    print("🔍 Inspecting Section 3.2 content...")
    
    # Initialize hybrid search
    hybrid_search = HybridSearch()
    
    # Run the exact query the user is having trouble with
    query = "Give me the objectives in Section 3.2"
    print(f"🎯 Query: '{query}'")
    
    results = hybrid_search.search_with_fallback(query, n_results=3)
    
    print(f"📊 Found {len(results)} results\n")
    
    for i, result in enumerate(results):
        print(f"📄 Result {i+1}:")
        print(f"   ID: {result.get('id', 'Unknown')}")
        print(f"   Type: {result.get('search_type', 'Unknown')}")
        print(f"   Score: {result.get('combined_score', 1.0 - result.get('distance', 1.0)):.4f}")
        
        # Check for Section 3.2 content
        content = result['text']
        print(f"   Length: {len(content)} characters")
        
        # Look for Section 3.2 specifically
        if '3.2' in content:
            print("   ✅ Contains '3.2'")
            
            # Find the Section 3.2 part
            lines = content.split('\n')
            section_32_found = False
            section_content = []
            
            for line_num, line in enumerate(lines):
                if '3.2' in line and ('List of Objectives' in line or 'objective' in line.lower()):
                    print(f"   🎯 Found Section 3.2 at line {line_num}: '{line.strip()}'")
                    section_32_found = True
                    section_content.append(line)
                    
                    # Get the next 10 lines to see the objectives
                    for next_line_num in range(line_num + 1, min(len(lines), line_num + 11)):
                        next_line = lines[next_line_num].strip()
                        if next_line:
                            section_content.append(next_line)
                            if next_line.startswith('##') and '3.3' in next_line:
                                break  # Stop at next section
                    break
            
            if section_32_found and section_content:
                print(f"   📋 Section 3.2 content:")
                for content_line in section_content:
                    print(f"      {content_line}")
            else:
                print("   ❌ Section 3.2 header found but no objectives content extracted")
                
                # Show context around 3.2
                print("   📋 Context around '3.2':")
                content_lines = content.split('\n')
                for line_num, line in enumerate(content_lines):
                    if '3.2' in line:
                        start = max(0, line_num - 3)
                        end = min(len(content_lines), line_num + 5)
                        for ctx_num in range(start, end):
                            prefix = "   >>> " if ctx_num == line_num else "       "
                            print(f"{prefix}{content_lines[ctx_num].strip()}")
                        break
        
        print("   " + "─" * 80)
        print()

def get_direct_chromadb_content():
    """
    Get content directly from ChromaDB to see full chunks
    """
    print("🗄️ Checking ChromaDB directly...")
    
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
        
        # Query for Section 3.2 content directly
        query_results = collection.query(
            query_texts=["Section 3.2 objectives"],
            n_results=5,
            include=['documents', 'metadatas']
        )
        
        print(f"📊 Direct ChromaDB query found {len(query_results['documents'][0])} results")
        
        for i, (doc, metadata) in enumerate(zip(query_results['documents'][0], query_results['metadatas'][0])):
            if '3.2' in doc:
                print(f"\n📄 Direct result {i+1}:")
                print(f"   Section: {metadata.get('section_number', 'Unknown')}")
                print(f"   Title: {metadata.get('section_title', 'Unknown')}")
                print(f"   Length: {len(doc)} characters")
                
                # Look for objectives in this chunk
                if 'List of Objectives' in doc:
                    print("   🎯 Found 'List of Objectives' in this chunk!")
                    
                    # Extract the objectives section
                    lines = doc.split('\n')
                    objectives_start = False
                    objectives_content = []
                    
                    for line in lines:
                        line = line.strip()
                        if 'List of Objectives' in line:
                            objectives_start = True
                            objectives_content.append(line)
                        elif objectives_start:
                            if line.startswith('##') and '3.3' in line:
                                break  # Next section
                            elif line:
                                objectives_content.append(line)
                    
                    print("   📋 Full Section 3.2 objectives content:")
                    for obj_line in objectives_content:
                        print(f"      {obj_line}")
                
                else:
                    print("   ❌ No 'List of Objectives' found in this chunk")
                    # Show what is in this chunk
                    print("   📋 Chunk content (first 500 chars):")
                    print(f"      {doc[:500]}...")
        
    except Exception as e:
        print(f"❌ Error accessing ChromaDB directly: {e}")

if __name__ == "__main__":
    print("🔍 Inspecting Section 3.2 Content Retrieval")
    print("=" * 60)
    
    # Method 1: Through hybrid search
    inspect_section_content()
    
    print("\n" + "=" * 60)
    
    # Method 2: Direct ChromaDB query
    get_direct_chromadb_content()
    
    print("\n🎯 Analysis complete!")
    print("If Section 3.2 objectives are being found but truncated,")
    print("the issue is likely in how the content is being chunked or displayed.")
