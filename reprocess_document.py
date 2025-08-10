#!/usr/bin/env python3
"""
Re-process ED19024 document with improved chunking strategy
This script will re-chunk the document to keep section headers with their content
"""

import os
import sys
from document_rag import DocumentRAG
import chromadb

def reprocess_ed19024():
    """Re-process the ED19024 document with better chunking"""
    
    print("🔄 Re-processing ED19024 document with improved chunking...")
    
    # Initialize RAG system
    rag = DocumentRAG()
    
    # Find the main ED19024 document
    uploads_dir = "uploads"
    ed19024_files = [f for f in os.listdir(uploads_dir) if "ED19024" in f and f.endswith(".pdf")]
    
    if not ed19024_files:
        print("❌ No ED19024 PDF files found in uploads directory")
        return False
    
    # Use the main agreement file (not the protected or other versions)
    main_file = None
    for file in ed19024_files:
        if "Agreement.pdf" in file and "PROTECTED" not in file and "NPWD" not in file:
            main_file = file
            break
    
    if not main_file:
        print("❌ Could not find main ED19024 Agreement PDF")
        return False
    
    file_path = os.path.join(uploads_dir, main_file)
    print(f"📄 Processing: {main_file}")
    
    # Clear existing chunks for this document
    print("🧹 Clearing existing chunks...")
    try:
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all documents and find ones related to ED19024
        results = collection.get(limit=1000)
        ed19024_ids = []
        
        for i, (doc_id, doc_text) in enumerate(zip(results['ids'], results['documents'])):
            if 'ED19024' in doc_text or 'ed19024' in doc_id.lower():
                ed19024_ids.append(doc_id)
        
        if ed19024_ids:
            print(f"🗑️ Removing {len(ed19024_ids)} existing ED19024 chunks...")
            collection.delete(ids=ed19024_ids)
            print("✅ Existing chunks removed")
        else:
            print("ℹ️ No existing ED19024 chunks found")
            
    except Exception as e:
        print(f"⚠️ Warning: Could not clear existing chunks: {e}")
    
    # Process the document with improved chunking
    print("🔄 Processing document with improved chunking...")
    try:
        result = rag.ingest_document(file_path)
        
        if result:
            print("✅ Document re-processed successfully!")
            print(f"📊 Document ID: {result}")
            return True
        else:
            print(f"❌ Processing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        return False

def test_section_11_4():
    """Test if Section 11.4 can now be found"""
    
    print("\n🧪 Testing Section 11.4 retrieval...")
    
    try:
        from hybrid_search import HybridSearch
        
        hybrid_search = HybridSearch()
        
        # Test queries
        test_queries = [
            "Section 11.4",
            "11.4 No commitment",
            "What is Section 11.4 about?",
            "Tell me about the no commitment section"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = hybrid_search.search_with_fallback(query, 3)
            
            if results:
                print(f"✅ Found {len(results)} results")
                
                found_11_4_content = False
                for i, result in enumerate(results):
                    contains_11_4 = '11.4' in result['text']
                    contains_commitment = 'commitment' in result['text'].lower()
                    
                    if contains_11_4 or contains_commitment:
                        found_11_4_content = True
                        print(f"  {i+1}. ✓ RELEVANT - Contains 11.4 or commitment")
                        print(f"     Text: {result['text'][:200]}...")
                    else:
                        print(f"  {i+1}. ✗ NOT RELEVANT")
                        print(f"     Text: {result['text'][:100]}...")
                
                if found_11_4_content:
                    print(f"✅ Query '{query}' successfully found Section 11.4 content!")
                else:
                    print(f"⚠️ Query '{query}' did not find Section 11.4 content")
            else:
                print(f"❌ No results found for '{query}'")
                
    except Exception as e:
        print(f"❌ Error testing Section 11.4: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔄 ED19024 Document Re-processing Script")
    print("=" * 50)
    
    # Re-process the document
    success = reprocess_ed19024()
    
    if success:
        # Test the results
        test_section_11_4()
        
        print("\n" + "=" * 50)
        print("✅ Re-processing completed!")
        print("You can now test the hybrid search for Section 11.4 in your Flask app.")
    else:
        print("\n❌ Re-processing failed!")
        sys.exit(1)
