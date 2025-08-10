#!/usr/bin/env python3
"""
Test script to debug document grouping logic
"""

import chromadb

def test_document_grouping():
    """Test the document grouping logic"""
    
    print("🧪 Testing Document Grouping Logic")
    print("=" * 50)
    
    try:
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all documents
        results = collection.get(limit=10000)
        
        print(f"📊 Total documents in collection: {len(results['ids'])}")
        
        # Group by document using document_id from metadata
        documents = {}
        for i, metadata in enumerate(results['metadatas']):
            # Use document_id from metadata if available, otherwise fall back to filename
            document_id = metadata.get('document_id', '')
            filename = metadata.get('filename', '')
            
            if not document_id:
                # Fallback: try to extract from chunk_id (for backward compatibility)
                chunk_id = results['ids'][i]
                if '_chunk_' in chunk_id:
                    # New format: document_id_chunk_number
                    document_id = chunk_id.split('_chunk_')[0]
                else:
                    # Old format: try to extract filename from chunk_id
                    # Handle various chunk_id formats
                    if '_' in chunk_id:
                        # Format like: filename_hash_chunk_number
                        parts = chunk_id.split('_')
                        if len(parts) >= 3:
                            # Extract filename from first part
                            document_id = parts[0]
                        else:
                            document_id = chunk_id
                    else:
                        document_id = chunk_id
            
            if not filename:
                # Extract filename from document_id if available
                if document_id and '_' in document_id:
                    filename = document_id.split('_')[0]
                else:
                    filename = document_id if document_id else 'Unknown'
            
            # Use document_id as the key for grouping
            if document_id not in documents:
                documents[document_id] = {
                    'document_id': document_id,
                    'filename': filename,
                    'total_chunks': 0,
                    'file_type': metadata.get('file_type', '.pdf'),
                    'upload_timestamp': metadata.get('upload_timestamp', ''),
                    'extraction_method': metadata.get('extraction_method', 'unknown')
                }
            
            documents[document_id]['total_chunks'] += 1
        
        print(f"📁 Grouped into {len(documents)} unique documents")
        
        # Look for test documents
        test_docs = {k: v for k, v in documents.items() if 'test_doc.txt' in k or 'test_doc.txt' in v['filename']}
        
        print(f"\n🔍 Found {len(test_docs)} test documents:")
        for doc_id, doc_info in test_docs.items():
            print(f"  - Document ID: {doc_id}")
            print(f"    Filename: {doc_info['filename']}")
            print(f"    Chunks: {doc_info['total_chunks']}")
            print(f"    File Type: {doc_info['file_type']}")
            print(f"    Upload Timestamp: {doc_info['upload_timestamp']}")
            print(f"    Extraction Method: {doc_info['extraction_method']}")
            print()
        
        # Show all documents
        print("📋 All documents:")
        for doc_id, doc_info in documents.items():
            print(f"  - {doc_info['filename']} ({doc_info['total_chunks']} chunks)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing document grouping: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Document Grouping Test")
    print("=" * 50)
    
    success = test_document_grouping()
    
    if success:
        print("\n✅ Document grouping test completed!")
    else:
        print("\n❌ Document grouping test failed!")
