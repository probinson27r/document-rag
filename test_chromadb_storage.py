#!/usr/bin/env python3
"""
Test script to verify ChromaDB storage is working correctly
"""

import chromadb
import os

def test_chromadb_storage():
    """Test if ChromaDB storage is working"""
    
    print("🧪 Testing ChromaDB Storage")
    print("=" * 50)
    
    try:
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        print("✅ ChromaDB client initialized")
        
        # Get current document count
        results = collection.get(limit=1)
        current_count = len(results['ids'])
        print(f"📊 Current document count: {current_count}")
        
        # Try to add a test document
        test_id = "test_storage_123"
        test_text = "This is a test document for storage verification."
        test_metadata = {"filename": "test_storage.txt", "document_id": "test_storage_123"}
        
        print("📝 Adding test document...")
        
        # Add the test document
        collection.add(
            ids=[test_id],
            documents=[test_text],
            metadatas=[test_metadata]
        )
        
        print("✅ Test document added")
        
        # Verify it was stored
        results = collection.get(ids=[test_id])
        if results['ids']:
            print("✅ Test document retrieved successfully")
            print(f"📄 Retrieved text: {results['documents'][0]}")
            print(f"📋 Retrieved metadata: {results['metadatas'][0]}")
            
            # Clean up - remove the test document
            collection.delete(ids=[test_id])
            print("🧹 Test document cleaned up")
            
            return True
        else:
            print("❌ Test document not found after storage")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ChromaDB storage: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 ChromaDB Storage Test")
    print("=" * 50)
    
    success = test_chromadb_storage()
    
    if success:
        print("\n✅ ChromaDB storage is working correctly!")
    else:
        print("\n❌ ChromaDB storage has issues!")
