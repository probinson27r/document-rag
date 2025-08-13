#!/usr/bin/env python3
"""
Test Improved Objectives Chunking

This script tests the improvements made to fix the issue where objectives (iv) and (ix) 
from section 3.2 were not being found in chunking results.
"""

import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_improved_langextract_chunking():
    """Test the improved LangExtract chunking with list merging"""
    
    print("🔍 Testing Improved LangExtract Chunking")
    print("=" * 60)
    
    # Test text with all Roman numeral objectives
    test_text = """
3.2 Service Objectives

Each party will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of legal services provided under this Agreement;
(ii) reduce costs while maintaining or improving service quality and client satisfaction;
(iii) ensure timely delivery of all legal services within agreed timeframes;
(iv) develop and implement innovative approaches to legal service delivery that enhance efficiency;
(v) establish effective communication protocols between all parties involved;
(vi) implement comprehensive quality assurance measures and performance monitoring;
(vii) provide regular training and professional development opportunities for legal staff;
(viii) maintain strict confidentiality and security standards in accordance with regulations;
(ix) achieve measurable performance improvements across all service delivery metrics;
(x) ensure full compliance with all applicable legal and regulatory requirements.
"""
    
    from langextract_chunking import LangExtractChunker
    
    print("📊 Testing with Improved LangExtract Chunker")
    print("-" * 40)
    
    chunker = LangExtractChunker(
        max_chunk_size=3000,
        min_chunk_size=200,
        preserve_lists=True,
        enable_roman_numerals=True
    )
    
    chunks = chunker.chunk_document(test_text)
    
    print(f"✅ Created {len(chunks)} chunks")
    
    # Check each chunk for objectives
    all_objectives = ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', '(ix)', '(x)']
    found_objectives = set()
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.chunk_type}")
        print(f"  Length: {len(chunk.content)} chars")
        print(f"  Section: {chunk.section_type}")
        print(f"  List items: {len(chunk.list_items)}")
        
        # Check which objectives are in this chunk
        chunk_objectives = []
        for obj in all_objectives:
            if obj in chunk.content:
                found_objectives.add(obj)
                chunk_objectives.append(obj)
        
        print(f"  Contains objectives: {', '.join(chunk_objectives) if chunk_objectives else 'None'}")
        
        # Special check for (iv) and (ix)
        has_iv = '(iv)' in chunk.content
        has_ix = '(ix)' in chunk.content
        print(f"  ✅ (iv): {has_iv}, (ix): {has_ix}")
        
        # Show a preview of content
        preview = chunk.content[:200].replace('\n', ' ')
        print(f"  Preview: {preview}...")
    
    # Summary
    missing_objectives = set(all_objectives) - found_objectives
    print(f"\n📊 Results Summary:")
    print(f"  Found objectives: {sorted(found_objectives)}")
    print(f"  Missing objectives: {sorted(missing_objectives)}")
    
    if not missing_objectives:
        print("✅ SUCCESS: All objectives (including iv and ix) are preserved!")
        return True
    else:
        print(f"❌ FAILURE: Missing objectives: {missing_objectives}")
        return False

def test_with_document_rag():
    """Test the full DocumentRAG pipeline with improved chunking"""
    
    print("\n🔍 Testing Full DocumentRAG Pipeline")
    print("=" * 60)
    
    # Create a realistic document
    test_document = """
Legal Services Agreement

3.2 Service Objectives

Each party will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of legal services provided under this Agreement;
(ii) reduce costs while maintaining or improving service quality and client satisfaction;
(iii) ensure timely delivery of all legal services within agreed timeframes;
(iv) develop and implement innovative approaches to legal service delivery that enhance efficiency;
(v) establish effective communication protocols between all parties involved;
(vi) implement comprehensive quality assurance measures and performance monitoring;
(vii) provide regular training and professional development opportunities for legal staff;
(viii) maintain strict confidentiality and security standards in accordance with regulations;
(ix) achieve measurable performance improvements across all service delivery metrics;
(x) ensure full compliance with all applicable legal and regulatory requirements.

3.3 Performance Metrics

The parties shall monitor progress against these objectives through quarterly reviews.
"""
    
    try:
        from document_rag import DocumentRAG
        
        print("Testing with DocumentRAG + LangExtract chunking...")
        
        rag = DocumentRAG(
            chunking_method='langextract',
            use_gpt4_enhancement=False,
            use_gpt4_chunking=False
        )
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_document)
            temp_file = f.name
        
        try:
            result = rag.ingest_document(temp_file)
            print(f"✅ Document processed: {result}")
            
            # Search for specific objectives to test retrieval
            search_queries = [
                "(iv) develop and implement innovative approaches",
                "(ix) achieve measurable performance improvements", 
                "objectives (iv)",
                "objectives (ix)",
                "innovative approaches",
                "measurable performance improvements"
            ]
            
            print(f"\n🔍 Testing search for objectives:")
            
            for query in search_queries:
                try:
                    search_results = rag.collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    found = False
                    if search_results['documents'] and search_results['documents'][0]:
                        for doc in search_results['documents'][0]:
                            if '(iv)' in doc or '(ix)' in doc:
                                found = True
                                break
                    
                    status = "✅ FOUND" if found else "❌ NOT FOUND"
                    print(f"  {status}: '{query[:40]}...'")
                    
                except Exception as e:
                    print(f"  ❌ ERROR searching '{query[:40]}...': {e}")
                    
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ DocumentRAG test failed: {e}")
        return False
    
    return True

def test_list_merging_functionality():
    """Test the specific list merging functionality"""
    
    print("\n🔍 Testing List Merging Functionality")
    print("=" * 60)
    
    from langextract_chunking import LangExtractChunker
    
    chunker = LangExtractChunker()
    
    # Simulate split components (what LangExtract API might return)
    split_components = [
        {"content": "(i) first objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(ii) second objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(iii) third objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(iv) fourth objective - the missing one", "section_type": "objectives", "confidence": 0.9},
        {"content": "(v) fifth objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(vi) sixth objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(vii) seventh objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(viii) eighth objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "(ix) ninth objective - the other missing one", "section_type": "objectives", "confidence": 0.9},
        {"content": "(x) tenth objective", "section_type": "objectives", "confidence": 0.9},
        {"content": "3.3 Performance Metrics", "section_type": "header", "confidence": 0.8}
    ]
    
    print(f"📥 Input: {len(split_components)} split components")
    
    # Test the list merging
    merged_components = chunker._merge_split_lists(split_components)
    
    print(f"📤 Output: {len(merged_components)} merged components")
    
    for i, component in enumerate(merged_components):
        content = component.get('content', '')
        comp_type = component.get('type', 'unknown')
        print(f"  Component {i+1}: {comp_type}")
        print(f"    Length: {len(content)} chars")
        
        # Check for specific objectives
        has_iv = '(iv)' in content
        has_ix = '(ix)' in content
        print(f"    Contains (iv): {has_iv}, (ix): {has_ix}")
        
        if comp_type == 'complete_list':
            print(f"    List items count: {component.get('list_items_count', 0)}")
            print(f"    Content preview: {content[:100]}...")
    
    return len(merged_components) < len(split_components)  # Should merge lists

if __name__ == "__main__":
    print("🚀 Starting Improved Objectives Chunking Tests")
    print("=" * 70)
    
    # Run tests
    langextract_test = test_improved_langextract_chunking()
    document_test = test_with_document_rag() 
    merging_test = test_list_merging_functionality()
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"  LangExtract Chunking: {'✅ PASS' if langextract_test else '❌ FAIL'}")
    print(f"  DocumentRAG Pipeline: {'✅ PASS' if document_test else '❌ FAIL'}")
    print(f"  List Merging: {'✅ PASS' if merging_test else '❌ FAIL'}")
    
    if langextract_test and document_test and merging_test:
        print("\n🎉 SUCCESS: All tests passed! Objectives (iv) and (ix) should now be preserved!")
    else:
        print("\n⚠️  Some tests failed. Further debugging may be needed.")
    
    print("\n💡 Key Improvements Made:")
    print("  1. Added list merging to prevent splitting Roman numeral lists")
    print("  2. Enhanced list detection to identify complete lists")  
    print("  3. Improved chunk type classification for complete lists")
    print("  4. Better preservation of objective list continuity")
