#!/usr/bin/env python3
"""
Debug LangExtract Extraction + Semantic Chunking Combination

This script debugs the specific issue where LangExtract extraction + Semantic chunking
is not finding text in section 3.2.
"""

import tempfile
import os
from app import ingest_document_with_improved_chunking

def test_langextract_semantic_combo():
    """Test LangExtract extraction + Semantic chunking combination"""
    
    print("🔍 Debugging LangExtract Extraction + Semantic Chunking")
    print("=" * 65)
    
    # Create a test document with section 3.2 content
    test_document = """
CONSOLIDATED ICT SERVICES AGREEMENT

1. INTRODUCTION

This agreement establishes the framework for comprehensive ICT services.

2. DEFINITIONS

2.1 In this Agreement, unless the context otherwise requires:
(a) "ICT Services" means information and communication technology services;
(b) "Service Provider" means the entity providing ICT services;
(c) "Client" means the entity receiving ICT services.

3. SERVICE REQUIREMENTS

3.1 General Requirements

The Service Provider shall provide ICT services in accordance with this Agreement.

3.2 Specific Service Objectives

(a) The Service Provider will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of ICT services provided under this Agreement;
(ii) reduce costs while maintaining or improving service quality and client satisfaction;
(iii) ensure timely delivery of all ICT services within agreed timeframes;
(iv) develop and implement innovative approaches to service delivery that enhance efficiency;
(v) establish effective communication protocols between all parties involved;
(vi) implement comprehensive quality assurance measures and performance monitoring;
(vii) provide regular training and professional development opportunities for technical staff;
(viii) maintain strict confidentiality and security standards in accordance with regulations;
(ix) achieve measurable performance improvements across all service delivery metrics.

3.3 Performance Standards

The Service Provider shall meet the performance standards set out in Schedule A.

4. PAYMENT TERMS

4.1 The Client shall pay the Service Provider in accordance with the payment schedule.

5. TERMINATION

Either party may terminate this agreement with 30 days written notice.
"""
    
    print("📄 Test Document Features:")
    print("  - Clear section 3.2 with subsection (a)")
    print("  - Complete Roman numeral objectives (i) through (ix)")
    print("  - Surrounding context (sections 3.1 and 3.3)")
    print(f"  - Document length: {len(test_document)} characters")
    
    # Configuration: LangExtract extraction + Semantic chunking
    config = {
        'extraction_method': 'langextract',   # LangExtract for extraction
        'chunking_method': 'semantic',       # Semantic for chunking
        'enable_ocr': False,
        'prefer_private_gpt4': False
    }
    
    print(f"\n🔧 Configuration:")
    print(f"  📄 Extraction Method: {config['extraction_method']} (Google GenAI text enhancement)")
    print(f"  🔗 Chunking Method: {config['chunking_method']} (Structure-aware splitting)")
    print(f"  🔒 Private GPT-4: {config['prefer_private_gpt4']}")
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_document)
        temp_file = f.name
    
    try:
        print(f"\n📂 Processing document: {os.path.basename(temp_file)}")
        
        result = ingest_document_with_improved_chunking(
            temp_file,
            processing_id='langextract_semantic_debug_123',
            passed_config=config
        )
        
        print(f"\n📊 Processing Results:")
        print(f"  ✅ Success: {result.get('success', False)}")
        print(f"  📊 Total Chunks: {result.get('total_chunks', 'Unknown')}")
        print(f"  🔧 Extraction Method: {result.get('extraction_method', 'Unknown')}")
        
        if result.get('success'):
            print("\n🔍 Analyzing Generated Chunks...")
            
            # Find the most recent chunks file
            debug_dir = "debug_json/chunks"
            if os.path.exists(debug_dir):
                import glob
                import json
                
                chunk_files = glob.glob(f"{debug_dir}/*.json")
                if chunk_files:
                    latest_file = max(chunk_files, key=os.path.getmtime)
                    print(f"  📄 Reading: {os.path.basename(latest_file)}")
                    
                    with open(latest_file, 'r') as f:
                        chunk_data = json.load(f)
                    
                    chunks = chunk_data.get('chunks', [])
                    chunking_method = chunk_data.get('chunking_method', 'unknown')
                    
                    print(f"  📊 Total chunks found: {len(chunks)}")
                    print(f"  🔧 Chunking method used: {chunking_method}")
                    
                    # Analyze each chunk for section 3.2 content
                    section_32_found = False
                    subsection_a_found = False
                    objectives_found = []
                    section_32_chunk_index = None
                    
                    for i, chunk in enumerate(chunks):
                        content = chunk.get('content', '')
                        print(f"\n  📝 Chunk {i}:")
                        print(f"    Type: {chunk.get('chunk_type', 'unknown')}")
                        print(f"    Tokens: {chunk.get('tokens', 0)}")
                        print(f"    Content length: {len(content)}")
                        
                        # Check for section 3.2
                        if '3.2' in content:
                            section_32_found = True
                            section_32_chunk_index = i
                            print(f"    ✅ Contains section 3.2!")
                        
                        # Check for subsection (a)
                        if '(a)' in content and 'endeavour' in content.lower():
                            subsection_a_found = True
                            print(f"    ✅ Contains subsection (a)!")
                        
                        # Check for specific objectives
                        chunk_objectives = []
                        for obj_num in ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', '(ix)']:
                            if obj_num in content:
                                chunk_objectives.append(obj_num)
                                objectives_found.append(obj_num)
                        
                        if chunk_objectives:
                            print(f"    🎯 Contains objectives: {', '.join(chunk_objectives)}")
                        
                        # Show content preview
                        preview = content[:200].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
                    
                    # Summary
                    print(f"\n📋 Analysis Summary:")
                    print(f"  🔍 Section 3.2 found: {'✅ YES' if section_32_found else '❌ NO'}")
                    if section_32_chunk_index is not None:
                        print(f"    Located in chunk: {section_32_chunk_index}")
                    
                    print(f"  🔍 Subsection (a) found: {'✅ YES' if subsection_a_found else '❌ NO'}")
                    print(f"  🎯 Objectives found: {len(set(objectives_found))}/9")
                    if objectives_found:
                        unique_objectives = sorted(set(objectives_found))
                        print(f"    Found: {', '.join(unique_objectives)}")
                    
                    missing_objectives = [f'({chr(105+i)})' for i in range(9) if f'({chr(105+i)})' not in objectives_found]
                    if missing_objectives:
                        print(f"    Missing: {', '.join(missing_objectives)}")
                    
                    # Test searchability
                    print(f"\n🔍 Testing Section 3.2 Searchability:")
                    test_search_section_32(chunks)
                
                else:
                    print("  ❌ No chunk files found in debug directory")
            
            return True
        else:
            print(f"\n❌ Processing failed: {result}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        os.unlink(temp_file)

def test_search_section_32(chunks):
    """Test if section 3.2 content is searchable in the chunks"""
    
    # Test queries that should find section 3.2 content
    test_queries = [
        "section 3.2",
        "3.2 objectives",
        "Service Provider will use reasonable endeavours",
        "objective (iv)",
        "objective (ix)", 
        "innovative approaches to service delivery",
        "performance improvements across all service delivery metrics"
    ]
    
    for query in test_queries:
        found_in_chunks = []
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '').lower()
            query_lower = query.lower()
            
            if query_lower in content:
                found_in_chunks.append(i)
        
        if found_in_chunks:
            print(f"    ✅ '{query}' found in chunk(s): {found_in_chunks}")
        else:
            print(f"    ❌ '{query}' NOT found in any chunk")

def compare_extraction_methods():
    """Compare different extraction methods for section 3.2 content"""
    
    print(f"\n🔬 Comparing Extraction Methods for Section 3.2")
    print("-" * 55)
    
    test_document = """3.2 Specific Service Objectives

(a) The Service Provider will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of ICT services provided under this Agreement;
(iv) develop and implement innovative approaches to service delivery that enhance efficiency;
(ix) achieve measurable performance improvements across all service delivery metrics."""
    
    extraction_methods = [
        ('traditional', 'Traditional extraction (no AI enhancement)'),
        ('langextract', 'LangExtract extraction (Google GenAI enhancement)')
    ]
    
    print("📄 Test text preview:")
    print(f"  {test_document[:150]}...")
    
    for method, description in extraction_methods:
        print(f"\n🧪 Testing {method}:")
        print(f"  {description}")
        
        # This would require running the extraction directly
        # For now, just show what should happen
        print(f"  Expected: Section 3.2 with objectives should be preserved")
        print(f"  Chunking: Should work with both Semantic and LangExtract chunking")

if __name__ == "__main__":
    print("🚀 Starting LangExtract + Semantic Combination Debug")
    print("=" * 70)
    
    # Test 1: Full document processing
    success = test_langextract_semantic_combo()
    
    # Test 2: Compare extraction methods
    compare_extraction_methods()
    
    print("\n" + "=" * 70)
    print("📊 Debug Summary:")
    if success:
        print("✅ Processing completed - check analysis above for section 3.2 issues")
    else:
        print("❌ Processing failed")
    
    print(f"\n💡 Key Points:")
    print("  - LangExtract extraction enhances text quality before chunking")
    print("  - Semantic chunking preserves document structure and sections")
    print("  - This combination should preserve section 3.2 content")
    print("  - If section 3.2 is missing, check the extraction enhancement process")
    
    print(f"\n🔧 Troubleshooting:")
    print("  1. Verify LangExtract enhancement is working correctly")
    print("  2. Check if semantic chunking is detecting section boundaries")
    print("  3. Ensure objectives are not being filtered out during processing")
    print("  4. Test different chunking methods if issues persist")
