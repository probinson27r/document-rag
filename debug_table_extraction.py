#!/usr/bin/env python3
"""
Debug table extraction to understand why tables aren't being detected
"""

import chromadb
import re
from typing import List, Dict

def analyze_chunk_content():
    """Analyze chunk content to understand what's being extracted"""
    
    print("🔍 Analyzing Chunk Content for Table Detection")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks
        results = collection.get(limit=20)  # Look at first 20 chunks
        
        print(f"📊 Analyzing first {len(results['ids'])} chunks:")
        print()
        
        table_indicators = 0
        service_level_indicators = 0
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"Chunk {i+1}: {chunk_id}")
            print(f"  Content length: {len(content)} characters")
            print(f"  Extraction method: {metadata.get('extraction_method', 'unknown')}")
            print(f"  Chunking method: {metadata.get('chunking_method', 'unknown')}")
            
            # Check for table indicators
            has_table_markers = '[TABLE]' in content or '[/TABLE]' in content
            has_pipe_separators = '|' in content
            has_tabular_content = any(indicator in content.lower() for indicator in ['service level', 'kpi', 'metric', 'requirement'])
            
            if has_table_markers:
                table_indicators += 1
                print(f"  ✅ Has table markers: {has_table_markers}")
            if has_pipe_separators:
                print(f"  📊 Has pipe separators (potential table): {has_pipe_separators}")
            if has_tabular_content:
                service_level_indicators += 1
                print(f"  📋 Has service level content: {has_tabular_content}")
            
            # Show content preview
            content_preview = content[:200].replace('\n', ' ')
            print(f"  Content preview: {content_preview}...")
            
            # Check for specific table-like patterns
            if 'service level' in content.lower():
                print(f"  🎯 Contains 'service level' - this might be table content!")
                
                # Look for structured data patterns
                lines = content.split('\n')
                for line_num, line in enumerate(lines):
                    if '|' in line or '\t' in line:
                        print(f"    Line {line_num + 1}: Potential table row: {line.strip()}")
            
            print("-" * 80)
        
        print(f"\n📊 Summary:")
        print(f"  Chunks with table markers: {table_indicators}")
        print(f"  Chunks with service level content: {service_level_indicators}")
        print(f"  Total chunks analyzed: {len(results['ids'])}")
        
        if table_indicators == 0:
            print(f"\n❌ No table markers found!")
            print(f"   This means tables are not being extracted with [TABLE] markers.")
            print(f"   Possible causes:")
            print(f"   1. Tables are being extracted as plain text without markers")
            print(f"   2. Table extraction is disabled or failing")
            print(f"   3. Tables are not being detected by the extraction method")
        
        return {
            'total_chunks': len(results['ids']),
            'table_markers': table_indicators,
            'service_level_content': service_level_indicators
        }
        
    except Exception as e:
        print(f"❌ Error analyzing chunk content: {e}")
        return None

def check_extraction_methods():
    """Check what extraction methods are being used"""
    
    print(f"\n🔧 Checking Extraction Methods")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks
        results = collection.get(limit=1000)
        
        # Count extraction methods
        extraction_methods = {}
        chunking_methods = {}
        
        for metadata in results['metadatas']:
            extraction_method = metadata.get('extraction_method', 'unknown')
            chunking_method = metadata.get('chunking_method', 'unknown')
            
            extraction_methods[extraction_method] = extraction_methods.get(extraction_method, 0) + 1
            chunking_methods[chunking_method] = chunking_methods.get(chunking_method, 0) + 1
        
        print(f"📊 Extraction Methods Used:")
        for method, count in extraction_methods.items():
            print(f"  {method}: {count} chunks")
        
        print(f"\n📊 Chunking Methods Used:")
        for method, count in chunking_methods.items():
            print(f"  {method}: {count} chunks")
        
        # Check if OCR is being used
        ocr_enabled = any('ocr' in method.lower() or 'unstructured' in method.lower() for method in extraction_methods.keys())
        print(f"\n🔍 OCR Analysis:")
        print(f"  OCR-enabled extraction: {ocr_enabled}")
        
        if not ocr_enabled:
            print(f"  ⚠️  OCR is not being used - this might affect table extraction")
            print(f"     Tables in PDFs often require OCR for proper extraction")
        
        return {
            'extraction_methods': extraction_methods,
            'chunking_methods': chunking_methods,
            'ocr_enabled': ocr_enabled
        }
        
    except Exception as e:
        print(f"❌ Error checking extraction methods: {e}")
        return None

def suggest_table_extraction_fixes():
    """Suggest fixes for table extraction"""
    
    print(f"\n💡 Table Extraction Fix Suggestions")
    print("=" * 50)
    
    suggestions = """
## Table Extraction Issues and Fixes

### Issue 1: Tables Not Being Detected
**Problem**: Tables are not being extracted with [TABLE] markers
**Cause**: Extraction method may not be detecting table structures

**Fixes**:
1. **Enable OCR**: Tables often require OCR for proper extraction
   ```python
   # In document processing
   enable_ocr = True
   ```

2. **Use Unstructured.io**: Better table detection
   ```python
   # This should be used when OCR is enabled
   from unstructured.partition.pdf import partition_pdf
   ```

3. **Use PDFPlumber**: For native PDF table extraction
   ```python
   # This should be used when OCR is disabled
   import pdfplumber
   tables = page.extract_tables()
   ```

### Issue 2: Tables Being Extracted as Plain Text
**Problem**: Tables are extracted but without [TABLE] markers
**Cause**: Table content is being processed as regular text

**Fixes**:
1. **Check Extraction Method**: Ensure proper table detection
2. **Add Table Markers**: Manually add [TABLE] markers
3. **Use Table-Aware Chunking**: Preserve table boundaries

### Issue 3: Service Level Tables Not Found
**Problem**: Service level tables exist but aren't being retrieved
**Cause**: Tables may be in different sections or not properly indexed

**Fixes**:
1. **Search for Service Level Content**: Look for service level sections
2. **Check Section Boundaries**: Ensure complete sections are retrieved
3. **Use Enhanced Search**: Use section-specific search

### Recommended Actions:

1. **Re-process Document with OCR Enabled**:
   ```bash
   # Upload document again with OCR enabled
   # This should extract tables with [TABLE] markers
   ```

2. **Check Document Structure**:
   - Look for service level sections
   - Identify where tables should be
   - Verify table extraction is working

3. **Test Table Extraction**:
   ```python
   # Test with a simple table extraction
   import pdfplumber
   with pdfplumber.open('document.pdf') as pdf:
       for page in pdf.pages:
           tables = page.extract_tables()
           print(f"Found {len(tables)} tables on page")
   ```

4. **Update Chunking Logic**:
   - Implement table preservation in chunking
   - Ensure tables stay as complete units
   - Add table-aware search capabilities
"""
    
    print(suggestions)

if __name__ == "__main__":
    # Analyze chunk content
    content_analysis = analyze_chunk_content()
    
    # Check extraction methods
    method_analysis = check_extraction_methods()
    
    # Suggest fixes
    suggest_table_extraction_fixes()
    
    print(f"\n🎯 Summary:")
    print("=" * 50)
    if content_analysis:
        if content_analysis['table_markers'] == 0:
            print(f"❌ No tables are being extracted!")
            print(f"   - {content_analysis['service_level_content']} chunks have service level content")
            print(f"   - Tables may be extracted as plain text without markers")
            print(f"   - Re-process document with OCR enabled")
        else:
            print(f"✅ Tables are being extracted!")
            print(f"   - {content_analysis['table_markers']} chunks have table markers")
    
    if method_analysis:
        if not method_analysis['ocr_enabled']:
            print(f"⚠️  OCR is not being used - this may affect table extraction")
        else:
            print(f"✅ OCR is being used - table extraction should work")
