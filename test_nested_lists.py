#!/usr/bin/env python3
"""
Test script for LangExtract nested list handling
"""

import os
import sys
from langextract_chunking import LangExtractChunker

def test_nested_list_detection():
    """Test nested list detection with mixed ordered and unordered lists"""
    
    print("Testing LangExtract Nested List Detection")
    print("=" * 60)
    
    # Test document with complex nested lists
    test_text = """
## 3.2 Contract Terms and Conditions

The following terms and conditions apply to this agreement:

1. Payment Terms
   a. Monthly invoicing will be provided
   b. Payment is due within 30 days
   c. Late payments will incur penalties
   • 5% penalty for payments over 30 days late
   • 10% penalty for payments over 60 days late
   • Legal action for payments over 90 days late

2. Service Delivery
   a. Services will be delivered according to the schedule
   b. Quality standards must be maintained
   • All deliverables must meet specification requirements
   • Testing must be completed before delivery
   • Documentation must be provided with each delivery
   c. Communication protocols must be followed
   • Weekly status reports required
   • Monthly review meetings scheduled
   • Emergency contact procedures established

3. Termination Conditions
   a. Either party may terminate with 30 days notice
   b. Immediate termination for breach of contract
   • Non-payment of invoices
   • Failure to deliver services
   • Violation of confidentiality terms
   c. Final settlement procedures
   • Return of all materials and equipment
   • Final payment within 14 days
   • Transfer of knowledge and documentation

## 3.3 Technical Requirements

The Contractor shall provide the following technical services:

1. System Architecture
   • Design scalable and maintainable systems
   • Implement security best practices
   • Ensure compliance with industry standards

2. Development Standards
   a. Code Quality
   • Follow established coding standards
   • Implement comprehensive testing
   • Maintain detailed documentation
   b. Version Control
   • Use Git for source code management
   • Maintain feature branches
   • Implement code review processes

3. Deployment Procedures
   a. Environment Management
   • Development environment setup
   • Staging environment configuration
   • Production deployment procedures
   b. Monitoring and Maintenance
   • System health monitoring
   • Performance optimization
   • Regular security updates

## 3.4 Legal Provisions

1. Governing Law
   • This agreement is governed by the laws of the jurisdiction
   • Any disputes will be resolved through arbitration
   • Venue for legal proceedings is specified in the agreement

2. Confidentiality
   a. Non-Disclosure Requirements
   • All information shared remains confidential
   • No disclosure to third parties without written consent
   • Confidentiality obligations survive termination
   b. Data Protection
   • Compliance with data protection regulations
   • Secure handling of personal information
   • Regular security audits and assessments

3. Intellectual Property
   • All IP developed remains with the Customer
   • Contractor retains rights to pre-existing IP
   • Joint development requires written agreement
"""
    
    # Initialize chunker with all features enabled
    chunker = LangExtractChunker(
        max_chunk_size=2000,
        min_chunk_size=200,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False,
        enable_roman_numerals=True,
        enable_bullet_points=True,
        enable_indented_lists=True,
        enable_legal_patterns=True,
        enable_multi_level=True
    )
    
    print("Configuration:")
    config = chunker.get_configuration_info()
    print(f"  Total patterns: {config['total_list_patterns']}")
    print(f"  Nested list support: Enabled")
    print()
    
    # Test chunking
    chunks = chunker.chunk_document(test_text)
    
    print(f"Chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.section_title}")
        print(f"  Section Type: {chunk.section_type}")
        print(f"  Total List Items: {len(chunk.list_items)}")
        
        if chunk.list_items:
            print("  Nested List Structure:")
            print("  " + "-" * 50)
            
            # Show nested structure
            for item in chunk.list_items:
                print(f"  {item['number']}. {item['text'][:60]}...")
                print(f"    Type: {item.get('list_type', 'unknown')}")
                print(f"    Level: {item.get('hierarchy_level', 'unknown')}")
                print(f"    Indentation: {item.get('indentation', 0)} spaces")
                print(f"    Has Children: {item.get('has_children', False)}")
                print(f"    Nesting Depth: {item.get('nesting_depth', 0)}")
                
                if item.get('children'):
                    print(f"    Children ({len(item['children'])}):")
                    for child in item['children']:
                        child_indent = "      " + "  " * child.get('nesting_depth', 0)
                        print(f"{child_indent}{child['number']}. {child['text'][:40]}...")
                        print(f"{child_indent}  Type: {child.get('list_type', 'unknown')}")
                
                print()

def test_complex_nesting():
    """Test very complex nested list structures"""
    
    print("\n" + "=" * 60)
    print("Testing Complex Nested List Structures")
    print("=" * 60)
    
    # Complex nested structure
    test_text = """
## 4.1 Complex Nested Structure

1. First Level Item
   a. Second Level Ordered
      • Third Level Unordered
         i. Fourth Level Roman
            A. Fifth Level Letter
               (1) Sixth Level Parenthesis
                   - Seventh Level Bullet
                     1. Eighth Level Number
                        a. Ninth Level Letter
                           • Tenth Level Bullet

2. Another First Level
   • Mixed Second Level
      1. Mixed Third Level
         a. Mixed Fourth Level
            • Mixed Fifth Level
               i. Mixed Sixth Level
                  A. Mixed Seventh Level
                     (1) Mixed Eighth Level
                         - Mixed Ninth Level
                           1. Mixed Tenth Level

## 4.2 Mixed List Types

1. Ordered with Unordered Children
   • Unordered child 1
   • Unordered child 2
     1. Ordered grandchild
     2. Another ordered grandchild
        • Unordered great-grandchild

2. Unordered with Ordered Children
   • Unordered parent
     1. Ordered child
     2. Another ordered child
        • Unordered grandchild
        • Another unordered grandchild
          1. Ordered great-grandchild
"""
    
    chunker = LangExtractChunker(
        max_chunk_size=2000,
        min_chunk_size=200,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False,
        enable_roman_numerals=True,
        enable_bullet_points=True,
        enable_indented_lists=True,
        enable_legal_patterns=True,
        enable_multi_level=True
    )
    
    chunks = chunker.chunk_document(test_text)
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.section_title}")
        print(f"  Total List Items: {len(chunk.list_items)}")
        
        if chunk.list_items:
            print("  Nested Structure Analysis:")
            
            # Analyze nesting patterns
            max_depth = 0
            list_types = set()
            nesting_patterns = []
            
            def analyze_item(item, depth=0):
                nonlocal max_depth
                max_depth = max(max_depth, depth)
                list_types.add(item.get('list_type', 'unknown'))
                
                pattern = {
                    'depth': depth,
                    'type': item.get('list_type', 'unknown'),
                    'number': item['number'],
                    'text': item['text'][:30] + '...'
                }
                nesting_patterns.append(pattern)
                
                for child in item.get('children', []):
                    analyze_item(child, depth + 1)
            
            for item in chunk.list_items:
                analyze_item(item)
            
            print(f"    Maximum nesting depth: {max_depth}")
            print(f"    List types found: {', '.join(list_types)}")
            print(f"    Total items in structure: {len(nesting_patterns)}")
            
            print("    Nesting pattern:")
            for pattern in nesting_patterns[:10]:  # Show first 10
                indent = "      " + "  " * pattern['depth']
                print(f"{indent}{pattern['number']} ({pattern['type']}) - {pattern['text']}")

def test_nested_list_visualization():
    """Test the nested list visualization feature"""
    
    print("\n" + "=" * 60)
    print("Testing Nested List Visualization")
    print("=" * 60)
    
    test_text = """
## 5.1 Visualization Test

1. Main Item
   a. Sub-item
      • Bullet point
         i. Roman numeral
            A. Letter item
   b. Another sub-item
      • Another bullet
      1. Mixed ordered item

2. Second Main Item
   • Unordered child
     1. Ordered grandchild
        a. Letter great-grandchild
"""
    
    chunker = LangExtractChunker(
        max_chunk_size=2000,
        min_chunk_size=200,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False,
        enable_roman_numerals=True,
        enable_bullet_points=True,
        enable_indented_lists=True,
        enable_legal_patterns=True,
        enable_multi_level=True
    )
    
    chunks = chunker.chunk_document(test_text)
    
    for chunk in chunks:
        if chunk.list_items:
            print(f"\nVisualization for: {chunk.section_title}")
            print("-" * 40)
            
            # Create visualization
            visualization = chunker._visualize_nested_structure(chunk.list_items)
            print(visualization)
            
            print(f"\nFlattened structure:")
            flattened = chunker._flatten_nested_items(chunk.list_items)
            for item in flattened:
                indent = "  " * item.get('display_level', 0)
                print(f"{indent}{item['number']}. {item['text'][:40]}...")

if __name__ == "__main__":
    print("LangExtract Nested List Detection Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_nested_list_detection()
    test_complex_nesting()
    test_nested_list_visualization()
    
    print("\n" + "=" * 60)
    print("✅ Nested list detection tests completed!")
    print("=" * 60)
