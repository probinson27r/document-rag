#!/usr/bin/env python3
"""
Comprehensive test script to validate the completed chunking strategy.
"""

import os
import sys
from legal_document_rag import (
    process_legal_pdf_nemo,
    identify_document_sections,
    detect_section_start,
    is_ordered_list_item,
    get_list_hierarchy_level,
    should_keep_together,
    detect_cross_references,
    validate_chunk_quality,
    generate_chunking_summary
)

def test_list_detection():
    """Test ordered list detection functionality"""
    print("=== TESTING LIST DETECTION ===")
    
    test_cases = [
        ("1. First item", True, "numeric", 1),
        ("A. Alphabetic item", True, "alpha_upper", 1),
        ("(a) Parenthetical item", True, "alpha_lower_paren", 1),
        ("I. Roman numeral", True, "roman", 1),
        ("(i) Lowercase roman", True, "roman_lower_paren", 1),
        ("3.2(a) Compact hierarchical", True, "compact_hierarchical", 2),
        ("3.2(a)(i) Nested compact", True, "compact_hierarchical", 3),
        ("3 OBJECTIVES", True, "section_heading", 1),
        ("3.1 List of Objectives", True, "subsection_heading", 2),
        ("Regular text without markers", False, "", 0),
    ]
    
    for text, expected_is_list, expected_type, expected_level in test_cases:
        is_list, marker_type, level = is_ordered_list_item(text)
        hierarchy_level = get_list_hierarchy_level(text)
        
        print(f"Text: '{text}'")
        print(f"  Expected: {expected_is_list}, {expected_type}, {expected_level}")
        print(f"  Actual: {is_list}, {marker_type}, {hierarchy_level}")
        print(f"  {'✓ PASS' if is_list == expected_is_list else '✗ FAIL'}")
        print()

def test_section_detection():
    """Test section detection functionality"""
    print("=== TESTING SECTION DETECTION ===")
    
    test_cases = [
        ("3 OBJECTIVES", {"number": "3", "title": "3 OBJECTIVES", "type": "section_heading"}),
        ("3.1 List of Objectives", {"number": "3", "title": "3.1 List of Objectives", "type": "subsection_heading"}),
        ("1.1 Definitions", {"number": "1", "title": "1.1 Definitions", "type": "subsection_heading"}),
        ("3.2(a) Specific Goals", {"number": "3.2", "title": "3.2(a) Specific Goals", "type": "subsection_letter"}),
        ("Regular text", None),
    ]
    
    for text, expected in test_cases:
        result = detect_section_start(text)
        print(f"Text: '{text}'")
        print(f"  Expected: {expected}")
        print(f"  Actual: {result}")
        if expected is None:
            print(f"  {'✓ PASS' if result is None else '✗ FAIL'}")
        else:
            print(f"  {'✓ PASS' if result and result.get('number') == expected['number'] else '✗ FAIL'}")
        print()

def test_cross_reference_detection():
    """Test cross-reference detection"""
    print("=== TESTING CROSS-REFERENCE DETECTION ===")
    
    test_text = """
    This section refers to section 3.2 above and section 4.1 below.
    As defined in section 1.1, the terms herein shall apply.
    Pursuant to section 2.3, the parties agree to the following.
    """
    
    cross_refs = detect_cross_references(test_text)
    print(f"Text: {test_text}")
    print(f"Cross-references found: {cross_refs}")
    print(f"Number of cross-references: {len(cross_refs)}")
    print()

def test_chunk_quality_validation():
    """Test chunk quality validation"""
    print("=== TESTING CHUNK QUALITY VALIDATION ===")
    
    test_cases = [
        ("This is a valid chunk with meaningful content that should pass validation.", True),
        ("", False),  # Empty
        ("123", False),  # Too short
        ("Page 1\nPage 2\nPage 3\nPage 4\nPage 5", False),  # Mostly footer content
        ("This is a good chunk with substantial content that should pass validation.", True),
    ]
    
    for text, expected in test_cases:
        result = validate_chunk_quality(text)
        print(f"Text: '{text[:50]}...'")
        print(f"  Expected: {expected}")
        print(f"  Actual: {result}")
        print(f"  {'✓ PASS' if result == expected else '✗ FAIL'}")
        print()

def test_should_keep_together():
    """Test chunking logic"""
    print("=== TESTING CHUNKING LOGIC ===")
    
    test_cases = [
        ("1. First item", "2. Second item", True),  # Same list type
        ("1. First item", "A. Different type", True),  # Different list types but related
        ("1. First item", "Regular text", True),  # Mixed content
        ("", "Any content", True),  # Empty current chunk
    ]
    
    for current, next_para, expected in test_cases:
        result = should_keep_together(current, next_para)
        print(f"Current: '{current[:30]}...'")
        print(f"Next: '{next_para[:30]}...'")
        print(f"  Expected: {expected}")
        print(f"  Actual: {result}")
        print(f"  {'✓ PASS' if result == expected else '✗ FAIL'}")
        print()

def test_complete_pdf_processing():
    """Test complete PDF processing"""
    print("=== TESTING COMPLETE PDF PROCESSING ===")
    
    # Test with a sample PDF if available
    pdf_path = "uploads/ED19024_Consolidated_ICT_Services_Agreement.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        print("Skipping complete PDF processing test")
        return
    
    try:
        print(f"Processing: {pdf_path}")
        result = process_legal_pdf_nemo(pdf_path)
        
        if not result or not result.get('chunks'):
            print("No chunks generated")
            return
        
        chunks = result['chunks']
        summary = result.get('summary', {})
        
        print(f"Generated {len(chunks)} chunks")
        print(f"Total characters: {summary.get('total_characters', 0)}")
        print(f"Average chunk size: {summary.get('average_chunk_size', 0)}")
        print(f"Sections found: {summary.get('sections_found', 0)}")
        print(f"Chunks with sections: {summary.get('chunks_with_sections', 0)}")
        print(f"Chunks with cross-references: {summary.get('chunks_with_cross_references', 0)}")
        
        # Analyze first few chunks
        print("\n=== SAMPLE CHUNKS ===")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i+1}:")
            print(f"  ID: {chunk['chunk_id']}")
            print(f"  Section: {chunk.get('section_number', 'N/A')} - {chunk.get('section_title', 'N/A')}")
            print(f"  Length: {len(chunk['content'])} characters")
            print(f"  Cross-references: {len(chunk.get('cross_references', []))}")
            print(f"  Content preview: {chunk['content'][:100]}...")
        
        print("\n✓ Complete PDF processing test completed successfully")
        
    except Exception as e:
        print(f"✗ Error during PDF processing: {e}")

def main():
    """Run all tests"""
    print("COMPREHENSIVE CHUNKING STRATEGY TEST")
    print("=" * 50)
    
    test_list_detection()
    test_section_detection()
    test_cross_reference_detection()
    test_chunk_quality_validation()
    test_should_keep_together()
    test_complete_pdf_processing()
    
    print("=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main() 