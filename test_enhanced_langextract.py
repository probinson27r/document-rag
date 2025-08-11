#!/usr/bin/env python3
"""
Enhanced test script for LangExtract chunking with improved list detection
"""

import os
import sys
from langextract_chunking import LangExtractChunker

def test_enhanced_list_detection():
    """Test the enhanced list detection capabilities"""
    
    print("Testing Enhanced LangExtract List Detection")
    print("=" * 60)
    
    # Test document with various list formats
    test_text = """
## 3.2 Objectives

The objectives of this agreement are:

1. Collaboration: Build a collaborative relationship between the Customer and the Contractor to achieve shared outcomes.

2. Value for Money: Deliver services in a manner that provides measurable value for money for the Customer.

3. Continuous Improvement: Ensure ongoing enhancements in the quality, efficiency, and effectiveness of the services.

a) Innovation: Encourage innovation to meet evolving requirements and challenges faced by the Customer.

b) Risk Management: Proactively manage risks to minimize disruptions and ensure service continuity.

4. Compliance: Adhere to all applicable laws, regulations, and policies governing the services.

5. Performance Transparency: Maintain clear and measurable service delivery performance levels, supported by timely reporting.

6. Customer Satisfaction: Deliver services in a manner that optimally meets the needs of end-users and stakeholders.

7. Sustainability: Support environmentally and socially sustainable practices in the delivery of services.

## 3.3 Service Requirements

The Contractor shall provide the following services:

• Technical consulting and support
• System integration and deployment  
• Training and documentation
• Ongoing maintenance and updates

## 3.4 Service Levels

The Contractor shall maintain the following service levels:

i. 99.9% uptime for critical systems
ii. 4-hour response time for urgent issues
iii. 24-hour response time for standard issues
iv. Monthly performance reports

## 3.5 Contract Terms

1) Payment Terms:
   a. Monthly invoicing
   b. 30-day payment terms
   c. Late payment penalties apply

2) Termination:
   a. 30-day notice required
   b. Final payment within 14 days
   c. Return of all materials

## 3.6 Legal Provisions

Clause 1.1: Governing Law
This agreement shall be governed by the laws of the jurisdiction.

Clause 1.2: Dispute Resolution
Any disputes shall be resolved through arbitration.

Section 2.1: Confidentiality
All information shared shall remain confidential.

Section 2.2: Non-Disclosure
Neither party shall disclose confidential information to third parties.
"""
    
    # Test different configurations
    configurations = [
        {
            'name': 'Basic Configuration',
            'config': {
                'enable_roman_numerals': False,
                'enable_bullet_points': False,
                'enable_indented_lists': False,
                'enable_legal_patterns': False,
                'enable_multi_level': False
            }
        },
        {
            'name': 'Enhanced Configuration (All Features)',
            'config': {
                'enable_roman_numerals': True,
                'enable_bullet_points': True,
                'enable_indented_lists': True,
                'enable_legal_patterns': True,
                'enable_multi_level': True
            }
        },
        {
            'name': 'Legal Document Configuration',
            'config': {
                'enable_roman_numerals': True,
                'enable_bullet_points': True,
                'enable_indented_lists': True,
                'enable_legal_patterns': True,
                'enable_multi_level': True,
                'custom_list_patterns': [
                    r'^Clause\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',
                    r'^Section\s+(\d+\.\d+)\s*[:.]?\s*(.+)$'
                ]
            }
        }
    ]
    
    for config_info in configurations:
        print(f"\n{config_info['name']}")
        print("-" * 40)
        
        # Initialize chunker with specific configuration
        chunker = LangExtractChunker(
            max_chunk_size=2000,
            min_chunk_size=200,
            preserve_lists=True,
            preserve_sections=True,
            use_langextract_api=False,
            **config_info['config']
        )
        
        # Get configuration info
        config = chunker.get_configuration_info()
        print(f"Total list patterns: {config['total_list_patterns']}")
        print(f"Roman numerals enabled: {config['enable_roman_numerals']}")
        print(f"Bullet points enabled: {config['enable_bullet_points']}")
        print(f"Indented lists enabled: {config['enable_indented_lists']}")
        print(f"Legal patterns enabled: {config['enable_legal_patterns']}")
        print(f"Multi-level enabled: {config['enable_multi_level']}")
        
        # Test chunking
        chunks = chunker.chunk_document(test_text)
        
        print(f"\nChunks created: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1}: {chunk.section_title}")
            print(f"  Section Type: {chunk.section_type}")
            print(f"  List Items Found: {len(chunk.list_items)}")
            
            if chunk.list_items:
                print("  List Items:")
                for item in chunk.list_items:
                    indent = "    " * (item['hierarchy_level'] - 1)
                    print(f"    {indent}{item['number']}. {item['text'][:60]}...")
                    print(f"      Pattern: {item['pattern']}")
                    print(f"      Level: {item['hierarchy_level']}")
                    print(f"      Indentation: {item['indentation']} spaces")

def test_custom_patterns():
    """Test custom list pattern addition"""
    
    print("\n" + "=" * 60)
    print("Testing Custom Pattern Addition")
    print("=" * 60)
    
    # Custom patterns for specific document types
    custom_patterns = [
        r'^Requirement\s+(\d+)\s*[:.]?\s*(.+)$',  # Requirement 1: Description
        r'^Task\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',    # Task 1.1: Description
        r'^Step\s+(\d+)\s*[:.]?\s*(.+)$',         # Step 1: Description
    ]
    
    test_text = """
## 4.1 Project Requirements

Requirement 1: The system must be scalable
Requirement 2: The system must be secure
Requirement 3: The system must be user-friendly

## 4.2 Implementation Tasks

Task 1.1: Design the database schema
Task 1.2: Implement the API endpoints
Task 1.3: Create the user interface

## 4.3 Deployment Steps

Step 1: Prepare the production environment
Step 2: Deploy the application
Step 3: Run integration tests
Step 4: Monitor system performance
"""
    
    # Initialize chunker with custom patterns
    chunker = LangExtractChunker(
        max_chunk_size=2000,
        min_chunk_size=200,
        preserve_lists=True,
        preserve_sections=True,
        use_langextract_api=False,
        custom_list_patterns=custom_patterns
    )
    
    # Get configuration info
    config = chunker.get_configuration_info()
    print(f"Total list patterns: {config['total_list_patterns']}")
    print(f"Custom patterns: {len(config['custom_list_patterns'])}")
    
    # Test chunking
    chunks = chunker.chunk_document(test_text)
    
    print(f"\nChunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.section_title}")
        print(f"  List Items Found: {len(chunk.list_items)}")
        
        if chunk.list_items:
            print("  List Items:")
            for item in chunk.list_items:
                print(f"    {item['number']}. {item['text']}")
                print(f"      Pattern: {item['pattern']}")

def test_pattern_tuning():
    """Test pattern tuning for specific use cases"""
    
    print("\n" + "=" * 60)
    print("Testing Pattern Tuning")
    print("=" * 60)
    
    # Test document with mixed list formats
    test_text = """
## 5.1 Mixed List Formats

1. First numbered item
   a. Sub-item with letter
   b. Another sub-item
2. Second numbered item
   • Bullet point sub-item
   • Another bullet point
3. Third numbered item
   i. Roman numeral sub-item
   ii. Another roman numeral

## 5.2 Indented Lists

   1. Indented numbered item
   2. Another indented item
      a. Double-indented item
      b. Another double-indented item
"""
    
    # Test with different tuning options
    tuning_options = [
        {
            'name': 'Basic Only',
            'config': {
                'enable_roman_numerals': False,
                'enable_bullet_points': False,
                'enable_indented_lists': False,
                'enable_legal_patterns': False,
                'enable_multi_level': False
            }
        },
        {
            'name': 'With Indented Lists',
            'config': {
                'enable_roman_numerals': False,
                'enable_bullet_points': False,
                'enable_indented_lists': True,
                'enable_legal_patterns': False,
                'enable_multi_level': False
            }
        },
        {
            'name': 'With All Features',
            'config': {
                'enable_roman_numerals': True,
                'enable_bullet_points': True,
                'enable_indented_lists': True,
                'enable_legal_patterns': False,
                'enable_multi_level': True
            }
        }
    ]
    
    for option in tuning_options:
        print(f"\n{option['name']}")
        print("-" * 30)
        
        chunker = LangExtractChunker(
            max_chunk_size=2000,
            min_chunk_size=200,
            preserve_lists=True,
            preserve_sections=True,
            use_langextract_api=False,
            **option['config']
        )
        
        chunks = chunker.chunk_document(test_text)
        
        total_items = sum(len(chunk.list_items) for chunk in chunks)
        print(f"Total list items detected: {total_items}")
        
        for chunk in chunks:
            if chunk.list_items:
                print(f"  {chunk.section_title}: {len(chunk.list_items)} items")
                for item in chunk.list_items[:3]:  # Show first 3 items
                    print(f"    {item['number']}. {item['text'][:40]}...")

if __name__ == "__main__":
    print("Enhanced LangExtract List Detection Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_enhanced_list_detection()
    test_custom_patterns()
    test_pattern_tuning()
    
    print("\n" + "=" * 60)
    print("✅ Enhanced list detection tests completed!")
    print("=" * 60)
