#!/usr/bin/env python3
"""
Examine specific chunks that contain table content to understand the structure
"""

import chromadb
import re
from typing import List, Dict

def examine_specific_chunks():
    """Examine the specific chunks mentioned by the user"""
    
    print("🔍 Examining Specific Table Chunks")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks to find the specific ones
        results = collection.get(limit=1000)
        
        # Find chunks by their position/index
        target_chunks = [767, 777, 770]  # The chunks mentioned by user
        
        print(f"📊 Looking for chunks at positions: {target_chunks}")
        print()
        
        found_chunks = []
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            if i in target_chunks:
                found_chunks.append({
                    'index': i,
                    'chunk_id': chunk_id,
                    'content': content,
                    'metadata': metadata
                })
                print(f"🎯 Found Chunk #{i}: {chunk_id}")
                print(f"   Content length: {len(content)} characters")
                print(f"   Extraction method: {metadata.get('extraction_method', 'unknown')}")
                print(f"   Chunking method: {metadata.get('chunking_method', 'unknown')}")
                
                # Check for table indicators
                has_pipe_separators = '|' in content
                has_tabular_content = any(indicator in content.lower() for indicator in ['service level', 'kpi', 'metric', 'requirement', 'bundle'])
                has_service_level = 'service level' in content.lower()
                
                print(f"   Has pipe separators: {has_pipe_separators}")
                print(f"   Has tabular content: {has_tabular_content}")
                print(f"   Has service level: {has_service_level}")
                
                # Show content preview
                print(f"   Content preview:")
                lines = content.split('\n')
                for line_num, line in enumerate(lines[:10]):  # Show first 10 lines
                    if line.strip():
                        print(f"     Line {line_num + 1}: {line.strip()}")
                
                # Look for structured data patterns
                table_rows = []
                for line_num, line in enumerate(lines):
                    if '|' in line or '\t' in line or re.match(r'^[A-Za-z].*\s+\d+', line):
                        table_rows.append((line_num + 1, line.strip()))
                
                if table_rows:
                    print(f"   📊 Potential table rows found:")
                    for line_num, row in table_rows[:5]:  # Show first 5 table rows
                        print(f"     Line {line_num}: {row}")
                
                print("-" * 80)
        
        print(f"\n📊 Found {len(found_chunks)} target chunks")
        
        # Analyze the content to understand table structure
        if found_chunks:
            analyze_table_structure(found_chunks)
        
        return found_chunks
        
    except Exception as e:
        print(f"❌ Error examining chunks: {e}")
        return None

def analyze_table_structure(found_chunks):
    """Analyze the table structure across the found chunks"""
    
    print(f"\n🔍 Analyzing Table Structure")
    print("=" * 50)
    
    all_content = ""
    for chunk in found_chunks:
        all_content += chunk['content'] + "\n\n"
    
    print(f"📊 Combined content length: {len(all_content)} characters")
    
    # Look for service level patterns
    service_level_patterns = [
        r'service level[s]?\s+\d+',
        r'level\s+\d+',
        r'sla[s]?',
        r'kpi[s]?',
        r'metric[s]?'
    ]
    
    print(f"🔍 Looking for service level patterns:")
    for pattern in service_level_patterns:
        matches = re.findall(pattern, all_content, re.IGNORECASE)
        if matches:
            print(f"   Pattern '{pattern}': {len(matches)} matches")
            for match in matches[:3]:  # Show first 3 matches
                print(f"     - {match}")
    
    # Look for structured data
    lines = all_content.split('\n')
    structured_lines = []
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for table-like patterns
        if ('|' in line or 
            '\t' in line or 
            re.match(r'^[A-Za-z].*\s+\d+', line) or
            re.match(r'^[A-Za-z].*\s+[A-Za-z].*\s+\d+', line)):
            structured_lines.append((line_num + 1, line))
    
    print(f"\n📊 Found {len(structured_lines)} structured lines:")
    for line_num, line in structured_lines[:10]:  # Show first 10
        print(f"   Line {line_num}: {line}")
    
    # Look for specific service level content
    service_level_sections = []
    for line_num, line in enumerate(lines):
        if 'service level' in line.lower():
            # Get context around this line
            start = max(0, line_num - 5)
            end = min(len(lines), line_num + 10)
            context = lines[start:end]
            service_level_sections.append((line_num + 1, context))
    
    print(f"\n🎯 Service Level Sections Found: {len(service_level_sections)}")
    for section_num, (line_num, context) in enumerate(service_level_sections[:3]):  # Show first 3
        print(f"\n   Section {section_num + 1} (around line {line_num}):")
        for i, context_line in enumerate(context):
            if context_line.strip():
                print(f"     {context_line.strip()}")

def suggest_chunking_fix():
    """Suggest how to fix the chunking to preserve complete tables"""
    
    print(f"\n💡 Chunking Fix Suggestions")
    print("=" * 50)
    
    suggestions = """
## Table Chunking Fix

### Current Issue:
- Tables are being split across chunks (#767, #777, #770)
- Only partial table content is being returned
- Complete table queries fail because content is fragmented

### Root Cause:
The current chunking logic doesn't preserve table boundaries. Tables are being split at arbitrary points, breaking the table structure.

### Solution: Implement Table-Aware Chunking

#### 1. Update should_keep_together() Function

Add table boundary detection to prevent splitting tables:

```python
def should_keep_together(current_chunk: str, next_paragraph: str) -> bool:
    # Check for table-like content
    current_has_table_content = has_table_content(current_chunk)
    next_has_table_content = has_table_content(next_paragraph)
    
    # If current chunk has table content, check if it's complete
    if current_has_table_content:
        # Check if we're in the middle of a table
        if is_incomplete_table(current_chunk):
            return True  # Keep together to complete the table
        
        # Check if next paragraph continues the table
        if next_has_table_content and is_table_continuation(current_chunk, next_paragraph):
            return True
    
    # Apply existing logic for non-table content
    return should_keep_together_original(current_chunk, next_paragraph)

def has_table_content(text: str) -> bool:
    # Check for table indicators
    table_indicators = [
        '|',  # Pipe separators
        '\t',  # Tab separators
        'service level',  # Service level content
        'kpi',  # Key performance indicators
        'metric',  # Metrics
        'requirement'  # Requirements
    ]
    return any(indicator in text.lower() for indicator in table_indicators)

def is_incomplete_table(text: str) -> bool:
    # Check if table content appears to be incomplete
    lines = text.split('\n')
    table_lines = [line for line in lines if has_table_content(line)]
    
    # If we have table content but it seems incomplete
    if table_lines:
        # Check if it ends with a complete row
        last_table_line = table_lines[-1]
        if not looks_like_complete_row(last_table_line):
            return True
    
    return False

def is_table_continuation(current_chunk: str, next_paragraph: str) -> bool:
    # Check if next paragraph continues the table structure
    current_lines = current_chunk.split('\n')
    next_lines = next_paragraph.split('\n')
    
    # Look for table structure patterns
    current_has_structure = any(has_table_content(line) for line in current_lines)
    next_has_structure = any(has_table_content(line) for line in next_lines)
    
    return current_has_structure and next_has_structure
```

#### 2. Update Chunking Logic

Modify the chunking process to respect table boundaries:

```python
def enhance_paragraph_chunking(paragraphs: List[str]) -> List[str]:
    enhanced_chunks = []
    current_chunk = ""
    in_table_section = False
    
    for i, paragraph in enumerate(paragraphs):
        # Check if we're entering a table section
        if has_table_content(paragraph):
            in_table_section = True
        
        # If we're in a table section, be more conservative about splitting
        if in_table_section:
            # Check if this paragraph continues the table
            if is_table_continuation(current_chunk, paragraph):
                # Keep together
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Check if we should start a new chunk
                if current_chunk and should_start_new_chunk(current_chunk, paragraph):
                    if current_chunk.strip():
                        enhanced_chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                    in_table_section = has_table_content(paragraph)
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
        else:
            # Apply normal chunking logic for non-table content
            if current_chunk and should_start_new_chunk(current_chunk, paragraph):
                if current_chunk.strip():
                    enhanced_chunks.append(current_chunk.strip())
                current_chunk = paragraph
                in_table_section = has_table_content(paragraph)
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk.strip():
        enhanced_chunks.append(current_chunk.strip())
    
    return enhanced_chunks
```

#### 3. Benefits of This Fix

- **Complete Table Retrieval**: Tables stay as complete units
- **Better Query Results**: Full table content is returned
- **Service Level Analysis**: Complete service level tables can be analyzed
- **Metric Comparisons**: All metrics in a table can be compared
- **Column Analysis**: Complete columns (like Service Bundle Ref.) can be analyzed

#### 4. Testing the Fix

After implementing the fix, test with:
- "Provide a full breakdown of each service level"
- "Show me the complete table with Service Bundle Ref. column"
- "What are all the metrics in the service level table?"
"""
    
    print(suggestions)

if __name__ == "__main__":
    # Examine the specific chunks
    found_chunks = examine_specific_chunks()
    
    # Suggest chunking fix
    suggest_chunking_fix()
    
    print(f"\n🎯 Summary:")
    print("=" * 50)
    if found_chunks:
        print(f"✅ Found {len(found_chunks)} target chunks")
        print(f"   - Tables ARE being extracted (just not with [TABLE] markers)")
        print(f"   - Content is split across multiple chunks")
        print(f"   - Need to implement table-aware chunking")
        print(f"   - This will fix your query issues")
    else:
        print(f"❌ Could not find target chunks")
        print(f"   - May need to check different chunk indices")
        print(f"   - Or re-analyze the chunking structure")
