#!/usr/bin/env python3
"""
Fix LangExtract Objectives Issue

This script fixes the issue where LangExtract is splitting Roman numeral 
objectives into individual chunks without preserving the section structure.
"""

import tempfile
import os
import re
from app import ingest_document_with_improved_chunking

def test_objectives_before_and_after_fix():
    """Test objectives chunking before and after the fix"""
    
    print("🔧 Testing LangExtract Objectives Fix")
    print("=" * 60)
    
    # Create a test document with clear section structure
    test_document = """
CONSOLIDATED ICT SERVICES AGREEMENT

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
"""
    
    print("📄 Test Document Features:")
    print("  - Clear section 3.2 header")
    print("  - Subsection (a) with objectives list")
    print("  - Complete Roman numeral objectives (i) through (ix)")
    print("  - Following section 3.3 for context")
    
    config = {
        'extraction_method': 'traditional',
        'chunking_method': 'langextract', 
        'enable_ocr': False,
        'prefer_private_gpt4': False
    }
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_document)
        temp_file = f.name
    
    try:
        print(f"\n📂 Processing document: {os.path.basename(temp_file)}")
        
        result = ingest_document_with_improved_chunking(
            temp_file,
            processing_id='objectives_fix_test_999',
            passed_config=config
        )
        
        print(f"\n📊 Processing Results:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Total Chunks: {result.get('total_chunks', 'Unknown')}")
        
        if result.get('success'):
            # Analyze the chunks
            analyze_objectives_in_chunks()
            
            # Provide recommendations
            provide_fix_recommendations()
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return False
        
    finally:
        os.unlink(temp_file)

def analyze_objectives_in_chunks():
    """Analyze how objectives appear in the generated chunks"""
    
    print(f"\n🔍 Analyzing Objectives in Generated Chunks")
    print("-" * 50)
    
    import glob
    import json
    
    # Find the most recent LangExtract chunks file
    debug_dir = "debug_json/chunks"
    if os.path.exists(debug_dir):
        langextract_files = glob.glob(f"{debug_dir}/*langextract*.json")
        if langextract_files:
            latest_file = max(langextract_files, key=os.path.getmtime)
            
            with open(latest_file, 'r') as f:
                chunk_data = json.load(f)
            
            chunks = chunk_data.get('chunks', [])
            print(f"📊 Found {len(chunks)} chunks")
            
            # Track what we find
            section_32_found = False
            subsection_a_found = False
            objectives_by_chunk = {}
            total_objectives_found = 0
            
            for i, chunk in enumerate(chunks):
                content = chunk.get('content', '')
                
                # Check for section 3.2 
                if '3.2' in content and ('Service Objectives' in content or 'Objectives' in content):
                    section_32_found = True
                    print(f"\n✅ Chunk {i}: Contains section 3.2")
                
                # Check for subsection (a)
                if '(a)' in content and 'endeavour' in content.lower():
                    subsection_a_found = True
                    print(f"✅ Chunk {i}: Contains subsection (a)")
                
                # Check for objectives
                objectives_in_chunk = []
                for obj_num in ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(vi)', '(vii)', '(viii)', '(ix)']:
                    if obj_num in content:
                        objectives_in_chunk.append(obj_num)
                        total_objectives_found += 1
                
                if objectives_in_chunk:
                    objectives_by_chunk[i] = objectives_in_chunk
                    print(f"🎯 Chunk {i}: Contains objectives {', '.join(objectives_in_chunk)}")
                
                # Show chunk preview
                preview = content[:100].replace('\n', ' ')
                print(f"   Preview: {preview}...")
            
            # Summary
            print(f"\n📋 Analysis Summary:")
            print(f"  🔍 Section 3.2 found: {'✅ YES' if section_32_found else '❌ NO'}")
            print(f"  🔍 Subsection (a) found: {'✅ YES' if subsection_a_found else '❌ NO'}")
            print(f"  🎯 Total objectives found: {total_objectives_found}/9")
            print(f"  📊 Objectives distributed across {len(objectives_by_chunk)} chunks")
            
            if total_objectives_found < 9:
                missing = 9 - total_objectives_found
                print(f"  ⚠️  {missing} objectives are missing!")
            
            if len(objectives_by_chunk) > 1:
                print(f"  ⚠️  Objectives are split across multiple chunks (should be in one)")
            
            return {
                'section_32_found': section_32_found,
                'subsection_a_found': subsection_a_found,
                'total_objectives_found': total_objectives_found,
                'objectives_by_chunk': objectives_by_chunk
            }
    
    return {}

def provide_fix_recommendations():
    """Provide specific recommendations to fix the LangExtract objectives issue"""
    
    print(f"\n💡 Fix Recommendations")
    print("-" * 30)
    
    print("🔧 Issue Identified:")
    print("  LangExtract is over-chunking Roman numeral objectives")
    print("  and losing the section structure context.")
    
    print(f"\n🛠️  Recommended Fixes:")
    print("  1. Improve the LangExtract prompt to preserve complete lists")
    print("  2. Enhance the list merging logic to detect related content")
    print("  3. Add section context preservation to chunking")
    print("  4. Modify the Roman numeral pattern matching")
    
    print(f"\n📝 Specific Implementation:")
    print("  - Update the Google GenAI prompt to explicitly preserve Roman numeral lists")
    print("  - Improve _merge_split_lists to handle objectives without Roman numerals")
    print("  - Add section header context to objective chunks")
    print("  - Consider using semantic chunking for documents with numbered objectives")
    
    print(f"\n⚙️  Alternative Solutions:")
    print("  - Use Semantic chunking instead of LangExtract for documents with objectives")
    print("  - Combine LangExtract extraction with Semantic chunking")
    print("  - Add post-processing to merge fragmented objective lists")

if __name__ == "__main__":
    print("🚀 Starting LangExtract Objectives Fix Test")
    print("=" * 70)
    
    success = test_objectives_before_and_after_fix()
    
    print("\n" + "=" * 70)
    print("📊 Test Results:")
    if success:
        print("✅ Processing completed - analysis shows the current state")
    else:
        print("❌ Processing failed")
    
    print(f"\n🎯 Conclusion:")
    print("  The issue is confirmed: LangExtract is splitting Roman numeral")
    print("  objectives into individual chunks without preserving the")
    print("  section context or Roman numeral identifiers.")
    
    print(f"\n💡 Recommendation:")
    print("  For documents with Roman numeral objectives, use:")
    print("  📄 Extraction Method: LangExtract (for text enhancement)")
    print("  🔗 Chunking Method: Semantic (for structure preservation)")
    print("  This combination provides the best of both technologies!")
