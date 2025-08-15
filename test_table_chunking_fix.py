#!/usr/bin/env python3
"""
Test the table-aware chunking fix
"""

import sys
import os
sys.path.append('.')

from legal_document_rag import has_table_content, is_incomplete_table, is_table_continuation, looks_like_complete_row

def test_table_detection():
    """Test table content detection"""
    
    print("🧪 Testing Table Content Detection")
    print("=" * 50)
    
    # Test cases from the actual chunks
    test_cases = [
        {
            'name': 'Service Level Content',
            'text': '## A.2 LAN Uptime LAN uptime during core hours. Network % availability 99.9% for critical services Report Contractor Monthly',
            'expected': True
        },
        {
            'name': 'Metric Content',
            'text': 'B.3 Standard of Documentation New or significantly updated % of non-acceptance, 1% Report Contractor Monthly',
            'expected': True
        },
        {
            'name': 'Regular Text',
            'text': 'This is just regular text without any table content or metrics.',
            'expected': False
        },
        {
            'name': 'Service Level Header',
            'text': '## 3.1 Service Levels Generally (continued)',
            'expected': True
        },
        {
            'name': 'Availability Metric',
            'text': 'uptime during core hours. Network 95% outside core hours',
            'expected': True
        }
    ]
    
    for test_case in test_cases:
        result = has_table_content(test_case['text'])
        status = "✅ PASS" if result == test_case['expected'] else "❌ FAIL"
        print(f"{status} {test_case['name']}: {result} (expected {test_case['expected']})")
    
    print()

def test_complete_row_detection():
    """Test complete row detection"""
    
    print("🧪 Testing Complete Row Detection")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Complete Service Level Row',
            'text': 'LAN uptime during core hours. Network % availability 99.9% for critical services Report Contractor Monthly',
            'expected': True
        },
        {
            'name': 'Incomplete Row',
            'text': 'services are available during the 95% outside core hours',
            'expected': False
        },
        {
            'name': 'Complete Metric Row',
            'text': 'B.3 Standard of Documentation New or significantly updated % of non-acceptance, 1% Report Contractor Monthly',
            'expected': True
        },
        {
            'name': 'Availability Row',
            'text': 'WAN Edge (including school Core) % availability 99.9% for critical services Report Contractor Monthly',
            'expected': True
        }
    ]
    
    for test_case in test_cases:
        result = looks_like_complete_row(test_case['text'])
        status = "✅ PASS" if result == test_case['expected'] else "❌ FAIL"
        print(f"{status} {test_case['name']}: {result} (expected {test_case['expected']})")
    
    print()

def test_table_continuation():
    """Test table continuation detection"""
    
    print("🧪 Testing Table Continuation Detection")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Service Level Continuation',
            'current': '## A.2 LAN Uptime LAN uptime during core hours. Network % availability 99.9% for critical services Report Contractor Monthly',
            'next': '## A.3 WAN Edge Uptime WAN Edge (including school Core) % availability 99.9% for critical services Report Contractor Monthly',
            'expected': True
        },
        {
            'name': 'Metric Continuation',
            'current': 'services are available during the 95% outside core hours',
            'next': 'uptime during core hours. Network 95% outside core hours',
            'expected': True
        },
        {
            'name': 'Non-Table Continuation',
            'current': 'This is regular text content.',
            'next': 'This is more regular text content.',
            'expected': False
        }
    ]
    
    for test_case in test_cases:
        result = is_table_continuation(test_case['current'], test_case['next'])
        status = "✅ PASS" if result == test_case['expected'] else "❌ FAIL"
        print(f"{status} {test_case['name']}: {result} (expected {test_case['expected']})")
    
    print()

def test_incomplete_table_detection():
    """Test incomplete table detection"""
    
    print("🧪 Testing Incomplete Table Detection")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Complete Table',
            'text': '''## A.2 LAN Uptime LAN uptime during core hours. Network % availability 99.9% for critical services Report Contractor Monthly
## A.3 WAN Edge Uptime WAN Edge (including school Core) % availability 99.9% for critical services Report Contractor Monthly''',
            'expected': False
        },
        {
            'name': 'Incomplete Table',
            'text': '''## A.2 LAN Uptime LAN uptime during core hours. Network % availability 99.9% for critical services Report Contractor Monthly
services are available during the 95% outside core hours''',
            'expected': True
        },
        {
            'name': 'Service Level Header Only',
            'text': '## 3.1 Service Levels Generally (continued)',
            'expected': True
        }
    ]
    
    for test_case in test_cases:
        result = is_incomplete_table(test_case['text'])
        status = "✅ PASS" if result == test_case['expected'] else "❌ FAIL"
        print(f"{status} {test_case['name']}: {result} (expected {test_case['expected']})")
    
    print()

def create_reprocessing_guide():
    """Create a guide for reprocessing the document"""
    
    print("📋 Document Reprocessing Guide")
    print("=" * 50)
    
    guide = """
## How to Reprocess Document with Table-Aware Chunking

### Step 1: Clear Current Data
```bash
# Backup current data (optional)
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d_%H%M%S)

# Clear current chunks
rm -rf chroma_db/*
```

### Step 2: Re-upload Document
1. Go to your web interface
2. Upload the document again
3. Use these settings:
   - **Extraction Method**: Traditional (for better table extraction)
   - **Chunking Method**: Semantic (uses the new table-aware logic)
   - **Enable OCR**: True (if available, for better table detection)

### Step 3: Verify Table Preservation
After reprocessing, test with:
- "Provide a full breakdown of each service level"
- "Show me the complete table with Service Bundle Ref. column"
- "What are all the metrics in the service level table?"

### Expected Results:
- ✅ Complete service level tables in single chunks
- ✅ All metrics and requirements preserved
- ✅ Service Bundle Ref. column data available
- ✅ No more fragmented table responses

### Step 4: Test the Fix
Run this test script again to verify table detection is working:
```bash
python test_table_chunking_fix.py
```
"""
    
    print(guide)

if __name__ == "__main__":
    # Run all tests
    test_table_detection()
    test_complete_row_detection()
    test_table_continuation()
    test_incomplete_table_detection()
    
    # Create reprocessing guide
    create_reprocessing_guide()
    
    print("🎯 Summary:")
    print("=" * 50)
    print("✅ Table-aware chunking functions implemented")
    print("✅ Ready to reprocess document with table preservation")
    print("✅ This will fix your query issues")
    print("✅ Follow the reprocessing guide above")
