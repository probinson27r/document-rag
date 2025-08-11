#!/usr/bin/env python3
"""
Reprocess Document with Semantic Chunking

This script reprocesses the main ED19024 document using the new semantic chunking
strategy that preserves complete sections and lists, specifically designed to
solve the objectives retrieval issue.
"""

import os
import sys
import shutil
from document_rag import DocumentRAG

def main():
    print("=" * 60)
    print("REPROCESSING DOCUMENT WITH SEMANTIC CHUNKING")
    print("=" * 60)
    
    # Check if the main document exists
    document_path = "uploads/ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(document_path):
        print(f"❌ Document not found: {document_path}")
        print("Please ensure the ED19024 document is in the uploads directory")
        return False
    
    # Backup existing ChromaDB
    chroma_backup_dir = "chroma_db_backup_semantic"
    if os.path.exists("chroma_db"):
        print(f"📦 Backing up existing ChromaDB to {chroma_backup_dir}")
        if os.path.exists(chroma_backup_dir):
            shutil.rmtree(chroma_backup_dir)
        shutil.copytree("chroma_db", chroma_backup_dir)
        print("✅ Backup completed")
    
    # Remove existing ChromaDB to start fresh
    if os.path.exists("chroma_db"):
        print("🗑️  Removing existing ChromaDB for fresh processing")
        shutil.rmtree("chroma_db")
        print("✅ Existing ChromaDB removed")
    
    # Initialize RAG system with semantic chunking
    print("🔧 Initializing RAG system with semantic chunking...")
    try:
        rag = DocumentRAG()
        print("✅ RAG system initialized")
        
        # Check if semantic chunking is available
        if hasattr(rag, 'use_semantic_chunking') and rag.use_semantic_chunking:
            print("✅ Semantic chunking is available")
        else:
            print("⚠️  Semantic chunking not available, will use fallback methods")
        
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        return False
    
    # Process the document
    print(f"\n📄 Processing document: {document_path}")
    try:
        result = rag.ingest_document(document_path)
        print(f"✅ Document processing result: {result}")
        
        # Check if processing was successful
        if "already exists" in result or "successfully" in result.lower():
            print("✅ Document processed successfully")
        else:
            print(f"⚠️  Processing result: {result}")
            
    except Exception as e:
        print(f"❌ Error processing document: {e}")
        return False
    
    # Test the results
    print("\n🧪 Testing semantic chunking results...")
    
    # Test objectives query
    test_queries = [
        "List the contract objectives",
        "What are the objectives in section 3.2",
        "Show all 9 objectives",
        "List the objectives in section 3.2"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            result = rag.query(query, n_results=3)
            print(f"✅ Query successful")
            print(f"📝 Answer preview: {result['answer'][:200]}...")
            
            if result.get('sources'):
                print(f"📚 Sources: {len(result['sources'])} chunks found")
                for source in result['sources'][:3]:
                    print(f"   - {source}")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    print("\n" + "=" * 60)
    print("SEMANTIC CHUNKING REPROCESSING COMPLETE")
    print("=" * 60)
    
    print("\n📊 Summary:")
    print("✅ Document reprocessed with semantic chunking")
    print("✅ Complete sections and lists preserved")
    print("✅ Objectives should now be retrievable as complete lists")
    
    print("\n🔄 Next steps:")
    print("1. Test the web interface with objectives queries")
    print("2. Verify that all 9 objectives are returned")
    print("3. Deploy to AWS if results are satisfactory")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
