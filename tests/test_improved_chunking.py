#!/usr/bin/env python3
"""
Test script to verify the improved section detection and cross-page section management.
"""

from legal_document_rag import process_legal_pdf_nemo, identify_document_sections, detect_section_start
import os

def test_improved_chunking():
    """Test the improved chunking strategy"""
    try:
        # Test with one of the PDF files
        pdf_path = "uploads/ED19024_Consolidated_ICT_Services_Agreement.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return
        
        print("=== TESTING IMPROVED CHUNKING STRATEGY ===")
        print(f"Processing: {pdf_path}")
        
        # Process the PDF with improved chunking
        result = process_legal_pdf_nemo(pdf_path)
        
        if not result or not result.get('chunks'):
            print("No chunks generated")
            return
        
        chunks = result['chunks']
        print(f"Generated {len(chunks)} chunks")
        print()
        
        # Analyze chunks for section information
        print("=== SECTION ANALYSIS ===")
        sections_found = {}
        chunks_with_sections = 0
        
        for i, chunk in enumerate(chunks):
            section_number = chunk.get('section_number', '')
            section_title = chunk.get('section_title', '')
            
            if section_number:
                chunks_with_sections += 1
                if section_number not in sections_found:
                    sections_found[section_number] = {
                        'title': section_title,
                        'chunks': [],
                        'pages': set()
                    }
                
                sections_found[section_number]['chunks'].append(i)
                if chunk.get('pages'):
                    sections_found[section_number]['pages'].update(chunk['pages'])
        
        print(f"Chunks with section information: {chunks_with_sections}/{len(chunks)}")
        print(f"Unique sections found: {len(sections_found)}")
        print()
        
        # Show sections that span multiple pages
        print("=== SECTIONS SPANNING MULTIPLE PAGES ===")
        multi_page_sections = []
        
        for section_num, section_info in sections_found.items():
            if len(section_info['pages']) > 1:
                multi_page_sections.append((section_num, section_info))
        
        print(f"Found {len(multi_page_sections)} sections spanning multiple pages:")
        
        for section_num, section_info in multi_page_sections:
            print(f"\nSection {section_num}: {section_info['title']}")
            print(f"  Pages: {sorted(section_info['pages'])}")
            print(f"  Chunks: {len(section_info['chunks'])}")
            
            # Show first chunk content
            first_chunk_idx = section_info['chunks'][0]
            first_chunk = chunks[first_chunk_idx]
            print(f"  First chunk preview: {first_chunk['content'][:200]}...")
        
        # Look specifically for section 3.2
        print("\n=== SECTION 3.2 ANALYSIS ===")
        if '3.2' in sections_found:
            section_32 = sections_found['3.2']
            print(f"Section 3.2: {section_32['title']}")
            print(f"Pages: {sorted(section_32['pages'])}")
            print(f"Number of chunks: {len(section_32['chunks'])}")
            
            print("\nSection 3.2 chunks:")
            for i, chunk_idx in enumerate(section_32['chunks']):
                chunk = chunks[chunk_idx]
                print(f"  Chunk {i+1}:")
                print(f"    Pages: {chunk.get('pages', [])}")
                print(f"    Content length: {len(chunk['content'])} characters")
                print(f"    Content preview: {chunk['content'][:300]}...")
                print()
        else:
            print("Section 3.2 not found in sections")
            
            # Look for chunks containing "3.2" in content
            chunks_with_32 = []
            for i, chunk in enumerate(chunks):
                if '3.2' in chunk['content']:
                    chunks_with_32.append((i, chunk))
            
            print(f"Found {len(chunks_with_32)} chunks containing '3.2' in content:")
            for i, (chunk_idx, chunk) in enumerate(chunks_with_32[:3]):
                print(f"  Chunk {chunk_idx}:")
                print(f"    Section: {chunk.get('section_number', 'N/A')}")
                print(f"    Title: {chunk.get('section_title', 'N/A')}")
                print(f"    Content: {chunk['content'][:200]}...")
        
        # Test section detection on sample text
        print("\n=== TESTING SECTION DETECTION ===")
        test_lines = [
            "3 OBJECTIVES",
            "3.1 List of Objectives",
            "3.2 Specific Goals",
            "4 SCOPE",
            "4.1 Project Scope",
            "Some regular text",
            "1.1 Definitions",
            "2.1 Interpretation"
        ]
        
        print("Testing section detection on sample lines:")
        for line in test_lines:
            section_info = detect_section_start(line)
            if section_info:
                print(f"  '{line}' -> Section {section_info['number']}: {section_info['title']}")
            else:
                print(f"  '{line}' -> Not a section")
        
    except Exception as e:
        print(f"Error testing improved chunking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_chunking() 