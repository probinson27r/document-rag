#!/usr/bin/env python3
"""
Script to analyze section detection and improve it for section 3.2.
"""

from legal_document_rag import process_legal_pdf_nemo, identify_document_sections, detect_section_start
import os
import re

def analyze_section_detection():
    """Analyze section detection in detail"""
    try:
        pdf_path = "uploads/ED19024_Consolidated_ICT_Services_Agreement.pdf"
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return
        
        print("=== DETAILED SECTION DETECTION ANALYSIS ===")
        
        # First, let's look at the raw text to understand the document structure
        import fitz
        doc = fitz.open(pdf_path)
        
        # Extract text from pages around where section 3.2 should be
        print("=== ANALYZING PAGES AROUND SECTION 3 ===")
        
        for page_num in range(10, 15):  # Check pages 10-15
            try:
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():
                    print(f"\n--- Page {page_num + 1} ---")
                    lines = text.split('\n')
                    
                    for i, line in enumerate(lines[:20]):  # First 20 lines
                        line = line.strip()
                        if line:
                            # Check if this line might be a section
                            if any(keyword in line for keyword in ['3.', 'OBJECTIVES', 'Goals', 'objectives']):
                                print(f"  Line {i}: '{line}'")
                                
                                # Test section detection
                                section_info = detect_section_start(line)
                                if section_info:
                                    print(f"    -> DETECTED: Section {section_info['number']}: {section_info['title']}")
                                else:
                                    print(f"    -> NOT DETECTED")
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
        
        doc.close()
        
        # Now test the improved chunking
        print("\n=== TESTING IMPROVED CHUNKING ===")
        result = process_legal_pdf_nemo(pdf_path)
        
        if not result or not result.get('chunks'):
            print("No chunks generated")
            return
        
        chunks = result['chunks']
        
        # Look for chunks that might contain section 3.2
        print("\n=== SEARCHING FOR SECTION 3.2 CONTENT ===")
        potential_32_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk['content']
            
            # Look for various patterns that might indicate section 3.2
            if any(pattern in content for pattern in [
                '3.2', 'List of Objectives', 'objectives of this Agreement',
                'objectives are to', 'Specific Goals'
            ]):
                potential_32_chunks.append((i, chunk))
        
        print(f"Found {len(potential_32_chunks)} potential section 3.2 chunks:")
        
        for i, (chunk_idx, chunk) in enumerate(potential_32_chunks):
            print(f"\n--- Potential 3.2 Chunk {i+1} (Chunk {chunk_idx}) ---")
            print(f"Section: {chunk.get('section_number', 'N/A')}")
            print(f"Title: {chunk.get('section_title', 'N/A')}")
            print(f"Pages: {chunk.get('pages', 'N/A')}")
            print(f"Content length: {len(chunk['content'])} characters")
            print(f"Content:")
            print(chunk['content'])
            print("-" * 80)
        
        # Analyze the section detection patterns
        print("\n=== ANALYZING SECTION DETECTION PATTERNS ===")
        
        # Look at all chunks to understand what sections are being detected
        section_patterns = {}
        
        for chunk in chunks:
            section_num = chunk.get('section_number', '')
            section_title = chunk.get('section_title', '')
            
            if section_num:
                if section_num not in section_patterns:
                    section_patterns[section_num] = []
                section_patterns[section_num].append(section_title)
        
        # Show sections that start with "3"
        print("Sections starting with '3':")
        for section_num in sorted(section_patterns.keys()):
            if section_num.startswith('3'):
                print(f"  {section_num}: {section_patterns[section_num][0]}")
        
        # Test specific patterns that might be missing
        print("\n=== TESTING MISSING PATTERNS ===")
        test_patterns = [
            "3.2 List of Objectives",
            "3.2",
            "List of Objectives",
            "3.2 Specific Goals",
            "3.2(a)",
            "3.2 (a)",
            "3.2.1",
            "3.2.1 Service Bundle",
            "3.2 Service Bundle",
            "3.2 Continuous service improvement"
        ]
        
        print("Testing specific patterns:")
        for pattern in test_patterns:
            section_info = detect_section_start(pattern)
            if section_info:
                print(f"  '{pattern}' -> Section {section_info['number']}: {section_info['title']}")
            else:
                print(f"  '{pattern}' -> NOT DETECTED")
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_section_detection() 