#!/usr/bin/env python3
"""
Test ChromaDB Metadata Fix

This script tests if the ChromaDB metadata type error is resolved by ingesting a simple document.
"""

import tempfile
import os
from app import ingest_document_with_improved_chunking

def test_chromadb_metadata_fix():
    """Test if ChromaDB metadata types are now compatible"""
    
    print("🧪 Testing ChromaDB Metadata Fix")
    print("=" * 40)
    
    # Simple test document
    test_document = """Section 1: Introduction

This is a test document to verify ChromaDB metadata compatibility.

Section 2: Details

(a) First item
(b) Second item
(c) Third item

Section 3: Conclusion

This concludes the test document."""
    
    print("📄 Test Document:")
    print("  - 3 clear sections")
    print("  - List items for testing list_items handling")
    print(f"  - Document length: {len(test_document)} characters")
    
    # Test with different configurations to check all metadata paths
    test_configs = [
        {
            'name': 'Traditional + Semantic',
            'config': {
                'extraction_method': 'traditional',
                'chunking_method': 'semantic',
                'enable_ocr': False,
                'prefer_private_gpt4': False
            }
        },
        {
            'name': 'LangExtract + Semantic', 
            'config': {
                'extraction_method': 'langextract',
                'chunking_method': 'semantic',
                'enable_ocr': False,
                'prefer_private_gpt4': False
            }
        }
    ]
    
    for test_case in test_configs:
        print(f"\n🔧 Testing: {test_case['name']}")
        print(f"  Configuration: {test_case['config']}")
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_document)
            temp_file = f.name
        
        try:
            result = ingest_document_with_improved_chunking(
                temp_file,
                processing_id=f'chromadb_test_{test_case["name"].lower().replace(" ", "_")}',
                passed_config=test_case['config']
            )
            
            print(f"  📊 Success: {result.get('success', False)}")
            print(f"  📊 Chunks: {result.get('total_chunks', 'Unknown')}")
            print(f"  📊 Method: {result.get('extraction_method', 'Unknown')}")
            
            if result.get('success'):
                print(f"  ✅ ChromaDB metadata types compatible!")
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            if "MetadataValue" in str(e):
                print(f"  🐛 Still has metadata type issues!")
            else:
                print(f"  ⚠️  Different error (not metadata related)")
                
        finally:
            os.unlink(temp_file)

if __name__ == "__main__":
    print("🚀 ChromaDB Metadata Fix Test")
    print("=" * 50)
    
    test_chromadb_metadata_fix()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("  This test verifies that all metadata values passed to ChromaDB")
    print("  are now compatible types (Bool, Int, Float, Str only).")
    print("  The fix converts complex objects like list_items to primitive types.")
    
    print(f"\n🔧 Fix Applied:")
    print("  - list_items (list) → list_items_count (int)")
    print("  - All string fields explicitly cast to str()")
    print("  - All numeric fields explicitly cast to int() or float()")
    print("  - Removed any complex nested objects from metadata")
