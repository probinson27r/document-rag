#!/usr/bin/env python3
"""
Debug LangExtract Sections Missing

This script specifically tests LangExtract chunking to debug why 
section 3.2 (a) with objectives (i) through (ix) is being missed.
"""

import tempfile
import os
from app import ingest_document_with_improved_chunking

def test_langextract_section_missing():
    """Test LangExtract chunking with a document containing section 3.2 (a)"""
    
    print("🐛 Debugging LangExtract Section 3.2 (a) Missing")
    print("=" * 60)
    
    # Create a test document that includes the problematic section
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
    
    print("📄 Test Document Created:")
    print(f"  Contains section 3.2 (a) with objectives (i) through (ix)")
    print(f"  Document length: {len(test_document)} characters")
    
    # Configuration for LangExtract chunking
    config = {
        'extraction_method': 'traditional',  # Use traditional extraction
        'chunking_method': 'langextract',    # Use LangExtract chunking
        'enable_ocr': False,
        'prefer_private_gpt4': False
    }
    
    print(f"\n🔧 Configuration:")
    print(f"  📄 Extraction Method: {config['extraction_method']}")
    print(f"  🔗 Chunking Method: {config['chunking_method']}")
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_document)
        temp_file = f.name
    
    try:
        print(f"\n📂 Processing document: {os.path.basename(temp_file)}")
        
        result = ingest_document_with_improved_chunking(
            temp_file,
            processing_id='langextract_section_debug_789',
            passed_config=config
        )
        
        print(f"\n📊 Processing Results:")
        print(f"  ✅ Success: {result.get('success', False)}")
        print(f"  📊 Total Chunks: {result.get('total_chunks', 'Unknown')}")
        print(f"  🔧 Extraction Method: {result.get('extraction_method', 'Unknown')}")
        
        if result.get('success'):
            print("\n🔍 Analyzing Generated Chunks...")
            
            # Find the most recent LangExtract chunks file
            debug_dir = "debug_json/chunks"
            if os.path.exists(debug_dir):
                import glob
                import json
                
                langextract_files = glob.glob(f"{debug_dir}/*langextract*.json")
                if langextract_files:
                    latest_file = max(langextract_files, key=os.path.getmtime)
                    print(f"  📄 Reading: {os.path.basename(latest_file)}")
                    
                    with open(latest_file, 'r') as f:
                        chunk_data = json.load(f)
                    
                    chunks = chunk_data.get('chunks', [])
                    print(f"  📊 Total chunks found: {len(chunks)}")
                    
                    # Analyze each chunk for section 3.2 (a) content
                    section_32a_found = False
                    objectives_found = []
                    
                    for i, chunk in enumerate(chunks):
                        content = chunk.get('content', '')
                        print(f"\n  📝 Chunk {i}:")
                        print(f"    Type: {chunk.get('chunk_type', 'unknown')}")
                        print(f"    Tokens: {chunk.get('tokens', 0)}")
                        print(f"    Content length: {len(content)}")
                        
                        # Check for section 3.2 (a)
                        if '3.2' in content and '(a)' in content:
                            section_32a_found = True
                            print(f"    ✅ Contains section 3.2 (a)!")
                        
                        # Check for specific objectives
                        for obj_num in ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', '(ix)']:
                            if obj_num in content:
                                objectives_found.append(obj_num)
                                print(f"    🎯 Contains objective {obj_num}")
                        
                        # Show content preview
                        preview = content[:200].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
                    
                    # Summary
                    print(f"\n📋 Analysis Summary:")
                    print(f"  🔍 Section 3.2 (a) found: {'✅ YES' if section_32a_found else '❌ NO'}")
                    print(f"  🎯 Objectives found: {len(objectives_found)}/9")
                    if objectives_found:
                        print(f"    Found: {', '.join(objectives_found)}")
                    
                    missing_objectives = [f'({chr(105+i)})' for i in range(9) if f'({chr(105+i)})' not in objectives_found]
                    if missing_objectives:
                        print(f"    Missing: {', '.join(missing_objectives)}")
                    
                    # Identify the issue
                    if not section_32a_found:
                        print("\n❌ ISSUE IDENTIFIED: Section 3.2 (a) is missing from chunks!")
                        print("   Possible causes:")
                        print("   - LangExtract is splitting the section incorrectly")
                        print("   - The section header is not being preserved")
                        print("   - Content is being merged with other sections")
                    
                    elif len(objectives_found) < 9:
                        print(f"\n⚠️  ISSUE IDENTIFIED: Only {len(objectives_found)}/9 objectives found!")
                        print("   Possible causes:")
                        print("   - List is being split across multiple chunks")
                        print("   - Some objectives are being filtered out")
                        print("   - Roman numeral detection issues")
                
                else:
                    print("  ❌ No LangExtract chunk files found in debug directory")
            
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

def analyze_langextract_chunking_logic():
    """Analyze the LangExtract chunking logic itself"""
    
    print("\n🔍 Analyzing LangExtract Chunking Logic")
    print("-" * 50)
    
    try:
        from langextract_chunking import LangExtractChunker
        
        # Test the chunker directly
        chunker = LangExtractChunker(use_langextract_api=True)
        
        if chunker.langextract_available:
            print("✅ LangExtract API is available")
            
            # Test with a simple section structure that includes objectives
            test_text = """3.2 Specific Service Objectives

(a) The Service Provider will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of ICT services;
(ii) reduce costs while maintaining service quality;
(iii) ensure timely delivery of all ICT services;
(iv) develop innovative approaches to service delivery;
(v) establish effective communication protocols;
(vi) implement quality assurance measures;
(vii) provide regular training opportunities;
(viii) maintain confidentiality and security standards;
(ix) achieve measurable performance improvements."""
            
            print(f"\n🧪 Testing LangExtract directly with section 3.2 (a):")
            print(f"  Input text:")
            print(f"  {test_text[:200]}...")
            print(f"  Input length: {len(test_text)} characters")
            
            # Call the chunking method directly
            chunks = chunker._chunk_with_langextract_api(test_text)
            
            print(f"  Output chunks: {len(chunks)}")
            
            for i, chunk in enumerate(chunks):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                print(f"\n  Chunk {i}:")
                print(f"    Length: {len(content)}")
                print(f"    Type: {getattr(chunk, 'chunk_type', 'unknown')}")
                print(f"    Content: {content}")
                
                # Check for objectives
                objectives_in_chunk = []
                for obj_num in ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', '(ix)']:
                    if obj_num in content:
                        objectives_in_chunk.append(obj_num)
                
                if objectives_in_chunk:
                    print(f"    ✅ Objectives: {', '.join(objectives_in_chunk)}")
                else:
                    print(f"    ❌ No objectives found")
        
        else:
            print("❌ LangExtract API is not available")
            print("   This could be why LangExtract chunking is not working properly")
    
    except Exception as e:
        print(f"❌ Error analyzing LangExtract logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting LangExtract Section Missing Debug")
    print("=" * 70)
    
    # Test 1: Document processing with LangExtract
    success = test_langextract_section_missing()
    
    # Test 2: Direct LangExtract analysis
    analyze_langextract_chunking_logic()
    
    print("\n" + "=" * 70)
    print("📊 Debug Summary:")
    if success:
        print("✅ Processing completed - check analysis above for issues")
    else:
        print("❌ Processing failed - check errors above")
    
    print("\n💡 Next Steps:")
    print("  1. Check debug_json/chunks/ for detailed chunk analysis")
    print("  2. Verify LangExtract API availability and configuration")
    print("  3. Consider adjusting LangExtract chunking parameters")
    print("  4. Test with different document structures")
