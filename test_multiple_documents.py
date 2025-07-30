#!/usr/bin/env python3
"""
Test script to verify multiple document loading functionality.
This script tests the fix for the "multiple documents cannot be loaded" defect.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multiple_documents():
    """Test multiple document loading functionality"""
    
    # Test configuration
    base_url = "http://localhost:5001"
    test_files = [
        "test_doc.txt",
        "test_doc2.txt"  # We'll create this
    ]
    
    print("🧪 Testing Multiple Document Loading Functionality")
    print("=" * 60)
    
    # Create a second test file
    test_doc2_content = """
    This is a second test document.
    
    Section 1: Introduction
    This document contains different content from the first document.
    
    Section 2: Main Content
    Here we have some unique information that should be distinguishable
    from the first document when searching.
    
    Section 3: Conclusion
    This concludes the second test document.
    """
    
    with open("test_doc2.txt", "w") as f:
        f.write(test_doc2_content)
    
    try:
        # Step 1: Check initial document count
        print("\n📋 Step 1: Checking initial document count...")
        response = requests.get(f"{base_url}/api/documents")
        if response.status_code == 200:
            initial_docs = response.json()
            print(f"   Initial documents: {len(initial_docs)}")
            for doc in initial_docs:
                print(f"   - {doc.get('filename', 'Unknown')} (ID: {doc.get('document_id', 'Unknown')})")
        else:
            print(f"   ❌ Failed to get documents: {response.status_code}")
            return False
        
        # Step 2: Upload first document
        print("\n📤 Step 2: Uploading first document...")
        with open("test_doc.txt", "rb") as f:
            files = {"file": f}
            response = requests.post(f"{base_url}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ First document uploaded: {result.get('message', 'Success')}")
            doc1_id = result.get('document_id', '')
            print(f"   Document ID: {doc1_id}")
        else:
            print(f"   ❌ Failed to upload first document: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Step 3: Upload second document
        print("\n📤 Step 3: Uploading second document...")
        with open("test_doc2.txt", "rb") as f:
            files = {"file": f}
            response = requests.post(f"{base_url}/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Second document uploaded: {result.get('message', 'Success')}")
            doc2_id = result.get('document_id', '')
            print(f"   Document ID: {doc2_id}")
        else:
            print(f"   ❌ Failed to upload second document: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Step 4: Verify both documents are listed
        print("\n📋 Step 4: Verifying both documents are listed...")
        response = requests.get(f"{base_url}/api/documents")
        if response.status_code == 200:
            docs = response.json()
            print(f"   Total documents: {len(docs)}")
            
            # Check if both documents are present
            doc1_found = False
            doc2_found = False
            
            for doc in docs:
                filename = doc.get('filename', '')
                doc_id = doc.get('document_id', '')
                chunks = doc.get('total_chunks', 0)
                print(f"   - {filename} (ID: {doc_id}, Chunks: {chunks})")
                
                if 'test_doc.txt' in filename:
                    doc1_found = True
                elif 'test_doc2.txt' in filename:
                    doc2_found = True
            
            if doc1_found and doc2_found:
                print("   ✅ Both documents found in the list")
            else:
                print("   ❌ Not all documents found")
                print(f"   Doc1 found: {doc1_found}, Doc2 found: {doc2_found}")
                return False
        else:
            print(f"   ❌ Failed to get documents: {response.status_code}")
            return False
        
        # Step 5: Test document-specific search
        print("\n🔍 Step 5: Testing document-specific search...")
        
        # Search in first document
        response = requests.get(f"{base_url}/api/documents/test_doc.txt/search?q=test document&n=5")
        if response.status_code == 200:
            result = response.json()
            print(f"   First document search results: {result.get('total_results', 0)}")
        else:
            print(f"   ❌ Failed to search first document: {response.status_code}")
        
        # Search in second document
        response = requests.get(f"{base_url}/api/documents/test_doc2.txt/search?q=unique information&n=5")
        if response.status_code == 200:
            result = response.json()
            print(f"   Second document search results: {result.get('total_results', 0)}")
        else:
            print(f"   ❌ Failed to search second document: {response.status_code}")
        
        # Step 6: Test document deletion
        print("\n🗑️ Step 6: Testing document deletion...")
        
        # Delete first document
        response = requests.delete(f"{base_url}/api/documents/test_doc.txt")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ First document deleted: {result.get('message', 'Success')}")
        else:
            print(f"   ❌ Failed to delete first document: {response.status_code}")
        
        # Verify only second document remains
        response = requests.get(f"{base_url}/api/documents")
        if response.status_code == 200:
            docs = response.json()
            print(f"   Documents after deletion: {len(docs)}")
            
            remaining_docs = [doc.get('filename', '') for doc in docs]
            if 'test_doc2.txt' in str(remaining_docs) and 'test_doc.txt' not in str(remaining_docs):
                print("   ✅ Only second document remains (correct)")
            else:
                print("   ❌ Document deletion verification failed")
                print(f"   Remaining documents: {remaining_docs}")
        
        # Clean up second document
        response = requests.delete(f"{base_url}/api/documents/test_doc2.txt")
        if response.status_code == 200:
            print("   ✅ Second document deleted (cleanup)")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    finally:
        # Clean up test files
        if os.path.exists("test_doc2.txt"):
            os.remove("test_doc2.txt")

if __name__ == "__main__":
    success = test_multiple_documents()
    sys.exit(0 if success else 1) 