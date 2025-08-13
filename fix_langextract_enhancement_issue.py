#!/usr/bin/env python3
"""
Fix LangExtract Enhancement Issue

This script demonstrates the problem with LangExtract enhancement converting 
Roman numeral objectives and provides solutions.
"""

import tempfile
import os
from app import ingest_document_with_improved_chunking

def compare_extraction_enhancement():
    """Compare Traditional vs LangExtract extraction to show the difference"""
    
    print("🔬 Comparing Traditional vs LangExtract Extraction")
    print("=" * 60)
    
    # Test document with Roman numeral objectives
    test_document = """3.2 Specific Service Objectives

(a) The Service Provider will use all reasonable endeavours to facilitate achievement of the following objectives:

(i) maintain and improve the overall quality of ICT services provided under this Agreement;
(ii) reduce costs while maintaining or improving service quality and client satisfaction;
(iii) ensure timely delivery of all ICT services within agreed timeframes;
(iv) develop and implement innovative approaches to service delivery that enhance efficiency;
(v) establish effective communication protocols between all parties involved;
(ix) achieve measurable performance improvements across all service delivery metrics."""
    
    print("📄 Original Text:")
    print("  Section 3.2 with subsection (a)")
    print("  Roman numeral objectives: (i), (ii), (iii), (iv), (v), (ix)")
    
    extraction_methods = [
        ('traditional', 'Traditional (no enhancement)'),
        ('langextract', 'LangExtract (Google GenAI enhancement)')
    ]
    
    for method, description in extraction_methods:
        print(f"\n🧪 Testing {method.upper()}:")
        print(f"  {description}")
        
        config = {
            'extraction_method': method,
            'chunking_method': 'semantic',
            'enable_ocr': False,
            'prefer_private_gpt4': False
        }
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_document)
            temp_file = f.name
        
        try:
            result = ingest_document_with_improved_chunking(
                temp_file,
                processing_id=f'{method}_comparison_test',
                passed_config=config
            )
            
            print(f"  📊 Success: {result.get('success', False)}")
            print(f"  📊 Chunks: {result.get('total_chunks', 'Unknown')}")
            
            if result.get('success'):
                # Find and analyze the chunks
                analyze_chunks_for_objectives(method)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            os.unlink(temp_file)

def analyze_chunks_for_objectives(method_name):
    """Analyze chunks to see how objectives are preserved"""
    
    import glob
    import json
    
    debug_dir = "debug_json/chunks"
    if os.path.exists(debug_dir):
        chunk_files = glob.glob(f"{debug_dir}/*.json")
        if chunk_files:
            latest_file = max(chunk_files, key=os.path.getmtime)
            
            with open(latest_file, 'r') as f:
                chunk_data = json.load(f)
            
            chunks = chunk_data.get('chunks', [])
            
            print(f"  📝 Chunk Analysis:")
            for i, chunk in enumerate(chunks):
                content = chunk.get('content', '')
                
                # Check for original objectives
                original_objectives = []
                for obj in ['(i)', '(ii)', '(iii)', '(iv)', '(v)', '(ix)']:
                    if obj in content:
                        original_objectives.append(obj)
                
                # Check for converted objectives  
                converted_objectives = []
                for obj in ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)', '(g)', '(h)']:
                    if obj in content:
                        converted_objectives.append(obj)
                
                # Check for subsection (a)
                has_subsection_a = '(a) The Service Provider will use' in content
                
                print(f"    Chunk {i}:")
                if original_objectives:
                    print(f"      ✅ Original Roman numerals: {', '.join(original_objectives)}")
                if converted_objectives:
                    print(f"      🔄 Converted to letters: {', '.join(converted_objectives)}")
                if has_subsection_a:
                    print(f"      ✅ Subsection (a) header preserved")
                else:
                    print(f"      ❌ Subsection (a) header missing")

def provide_solution():
    """Provide solutions for the LangExtract enhancement issue"""
    
    print(f"\n💡 Solutions for LangExtract Enhancement Issue")
    print("=" * 55)
    
    print("🐛 **Problem Identified:**")
    print("  LangExtract enhancement is converting Roman numeral objectives")
    print("  (i), (ii), (iii), (iv), (ix) → (a), (b), (c), (d), (i)")
    print("  This breaks searches for specific Roman numeral objectives!")
    
    print(f"\n🛠️  **Solution Options:**")
    
    print(f"\n1️⃣ **Use Traditional Extraction + Semantic Chunking** (RECOMMENDED)")
    print("   ✅ Preserves original Roman numeral format")
    print("   ✅ Maintains section structure") 
    print("   ✅ Fast and reliable")
    print("   ❌ No text enhancement benefits")
    
    print(f"\n2️⃣ **Use Pure Semantic Chunking** (ALTERNATIVE)")
    print("   ✅ Preserves original format")
    print("   ✅ Structure-aware chunking")
    print("   ✅ No AI dependencies")
    print("   ❌ No extraction enhancement")
    
    print(f"\n3️⃣ **Fix LangExtract Enhancement Prompt** (FUTURE)")
    print("   ✅ Could preserve Roman numerals if prompt is improved")
    print("   ✅ Would get benefits of both enhancement and preservation")
    print("   ❌ Requires modifying the LangExtract prompt")
    
    print(f"\n🎯 **Immediate Recommendation:**")
    print("   For documents with Roman numeral objectives:")
    print("   📄 Extraction Method: Traditional")
    print("   🔗 Chunking Method: Semantic")
    print("   This preserves objectives (i) through (ix) exactly as written!")

if __name__ == "__main__":
    print("🚀 LangExtract Enhancement Issue Analysis")
    print("=" * 70)
    
    # Compare extraction methods
    compare_extraction_enhancement()
    
    # Provide solutions
    provide_solution()
    
    print("\n" + "=" * 70)
    print("📊 Summary:")
    print("  The issue is that LangExtract enhancement modifies Roman numeral")
    print("  objectives, making them unsearchable by their original identifiers.")
    print("  Use Traditional extraction + Semantic chunking to preserve them.")
    
    print(f"\n🔧 Configuration to use:")
    print("  extraction_method: 'traditional'")
    print("  chunking_method: 'semantic'")
    print("  This preserves section 3.2 (a) with objectives (i) through (ix)!")
