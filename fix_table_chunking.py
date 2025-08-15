#!/usr/bin/env python3
"""
Fix table chunking to ensure tables are preserved as complete units
"""

import chromadb
import re
from typing import List, Dict, Tuple

def detect_table_boundaries(text: str) -> List[Tuple[int, int]]:
    """
    Detect table boundaries in text
    
    Args:
        text: Text content
        
    Returns:
        List of (start_pos, end_pos) tuples for table boundaries
    """
    table_boundaries = []
    
    # Find all [TABLE] and [/TABLE] markers
    table_start_pattern = r'\[TABLE\]'
    table_end_pattern = r'\[/TABLE\]'
    
    start_matches = list(re.finditer(table_start_pattern, text))
    end_matches = list(re.finditer(table_end_pattern, text))
    
    # Match start and end markers
    for start_match in start_matches:
        start_pos = start_match.start()
        
        # Find the corresponding end marker
        for end_match in end_matches:
            end_pos = end_match.end()
            if end_pos > start_pos:
                table_boundaries.append((start_pos, end_pos))
                break
    
    return table_boundaries

def should_keep_together_with_tables(current_chunk: str, next_paragraph: str) -> bool:
    """
    Enhanced should_keep_together function that preserves table integrity
    
    Args:
        current_chunk: Current chunk content
        next_paragraph: Next paragraph to consider
        
    Returns:
        True if should keep together, False otherwise
    """
    # Check if current chunk contains an incomplete table
    current_has_table_start = '[TABLE]' in current_chunk
    current_has_table_end = '[/TABLE]' in current_chunk
    
    # Check if next paragraph contains table content
    next_has_table_start = '[TABLE]' in next_paragraph
    next_has_table_end = '[/TABLE]' in next_paragraph
    
    # Rule 1: If current chunk has [TABLE] but no [/TABLE], keep together
    if current_has_table_start and not current_has_table_end:
        return True
    
    # Rule 2: If next paragraph has [/TABLE] but no [TABLE], keep together
    if next_has_table_end and not next_has_table_start:
        return True
    
    # Rule 3: If both chunks contain table markers, check if they're part of the same table
    if current_has_table_start and next_has_table_end:
        # Count table markers in current chunk
        current_table_starts = current_chunk.count('[TABLE]')
        current_table_ends = current_chunk.count('[/TABLE]')
        
        # If we have more starts than ends, keep together
        if current_table_starts > current_table_ends:
            return True
    
    # Rule 4: If next paragraph starts a new table, break here
    if next_has_table_start and not current_has_table_start:
        # Check if current chunk is complete (has matching table markers)
        current_table_starts = current_chunk.count('[TABLE]')
        current_table_ends = current_chunk.count('[/TABLE]')
        if current_table_starts == current_table_ends:
            return False  # Start new chunk for new table
    
    # Rule 5: If we're in the middle of a table, keep together regardless of length
    if current_has_table_start and not current_has_table_end:
        # We're in the middle of a table, keep together
        return True
    
    # Apply original logic for non-table content
    # (This would be the existing should_keep_together logic)
    return should_keep_together_original(current_chunk, next_paragraph)

def should_keep_together_original(current_chunk: str, next_paragraph: str) -> bool:
    """
    Original should_keep_together logic (simplified version)
    """
    # If current chunk is empty, always add
    if not current_chunk.strip():
        return True
    
    # Check length constraints
    combined_length = len(current_chunk) + len(next_paragraph)
    return combined_length < 1000

def fix_table_chunks_in_chromadb():
    """Fix table chunks in ChromaDB by re-chunking with table preservation"""
    
    print("🔧 Fixing Table Chunking in ChromaDB")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./chroma_db')
        collection = client.get_collection('documents')
        
        # Get all chunks
        results = collection.get(limit=1000)
        
        print(f"📊 Found {len(results['ids'])} chunks to analyze")
        
        # Track chunks that need fixing
        chunks_with_incomplete_tables = []
        chunks_with_complete_tables = []
        
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Check for table markers
            has_table_start = '[TABLE]' in content
            has_table_end = '[/TABLE]' in content
            
            if has_table_start or has_table_end:
                table_starts = content.count('[TABLE]')
                table_ends = content.count('[/TABLE]')
                
                if table_starts != table_ends:
                    chunks_with_incomplete_tables.append({
                        'chunk_id': chunk_id,
                        'content': content,
                        'metadata': metadata,
                        'table_starts': table_starts,
                        'table_ends': table_ends
                    })
                    print(f"❌ Chunk {i+1}: Incomplete table (starts: {table_starts}, ends: {table_ends})")
                else:
                    chunks_with_complete_tables.append({
                        'chunk_id': chunk_id,
                        'content': content,
                        'metadata': metadata
                    })
                    print(f"✅ Chunk {i+1}: Complete table")
        
        print(f"\n📊 Table Analysis Summary:")
        print(f"  Chunks with complete tables: {len(chunks_with_complete_tables)}")
        print(f"  Chunks with incomplete tables: {len(chunks_with_incomplete_tables)}")
        
        if chunks_with_incomplete_tables:
            print(f"\n⚠️  WARNING: Found {len(chunks_with_incomplete_tables)} chunks with incomplete tables!")
            print(f"   This means tables are being split across multiple chunks.")
            print(f"   This will cause issues with table queries like:")
            print(f"   - 'Provide a full breakdown of each service level'")
            print(f"   - 'Show me the complete table with Service Bundle Ref. column'")
            print(f"   - 'What are all the metrics in the table?'")
            
            return {
                'total_chunks': len(results['ids']),
                'complete_tables': len(chunks_with_complete_tables),
                'incomplete_tables': len(chunks_with_incomplete_tables),
                'needs_fixing': True
            }
        else:
            print(f"\n✅ All tables are complete! No fixing needed.")
            return {
                'total_chunks': len(results['ids']),
                'complete_tables': len(chunks_with_complete_tables),
                'incomplete_tables': 0,
                'needs_fixing': False
            }
        
    except Exception as e:
        print(f"❌ Error analyzing table chunks: {e}")
        return None

def create_table_preservation_guide():
    """Create a guide for implementing table preservation in chunking"""
    
    print(f"\n📋 Table Preservation Implementation Guide:")
    print("=" * 50)
    
    guide = """
## Table Preservation Implementation

### 1. Update should_keep_together() Function

Add table boundary detection to the existing should_keep_together() function in legal_document_rag.py:

```python
def should_keep_together(current_chunk: str, next_paragraph: str) -> bool:
    # Check for incomplete tables first
    current_has_table_start = '[TABLE]' in current_chunk
    current_has_table_end = '[/TABLE]' in current_chunk
    
    # Rule 1: If current chunk has [TABLE] but no [/TABLE], keep together
    if current_has_table_start and not current_has_table_end:
        return True
    
    # Rule 2: If next paragraph has [/TABLE] but no [TABLE], keep together
    if '[/TABLE]' in next_paragraph and '[TABLE]' not in next_paragraph:
        return True
    
    # Rule 3: If we're in the middle of a table, keep together regardless of length
    if current_has_table_start and not current_has_table_end:
        return True
    
    # Apply existing logic for non-table content
    # ... existing should_keep_together logic ...
```

### 2. Update Chunking Logic

Modify the chunking process to respect table boundaries:

```python
def enhance_paragraph_chunking(paragraphs: List[str]) -> List[str]:
    enhanced_chunks = []
    current_chunk = ""
    in_table = False
    
    for i, paragraph in enumerate(paragraphs):
        # Check if we're entering a table
        if '[TABLE]' in paragraph and '[/TABLE]' not in paragraph:
            in_table = True
        
        # Check if we're exiting a table
        if '[/TABLE]' in paragraph:
            in_table = False
        
        # If we're in a table, always keep together
        if in_table:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
        else:
            # Apply normal chunking logic
            if current_chunk and should_start_new_chunk(current_chunk, paragraph):
                if current_chunk.strip():
                    enhanced_chunks.append(current_chunk.strip())
                current_chunk = paragraph
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

### 3. Update Semantic Chunking

Modify semantic_chunking.py to preserve tables:

```python
def _chunk_section(self, section: Section) -> List[Chunk]:
    # Check if section contains tables
    if '[TABLE]' in section.content:
        # Keep entire section as one chunk if it contains tables
        if len(section.content) <= self.max_chunk_size * 2:  # Allow larger chunks for tables
            chunk = Chunk(
                content=section.content,
                chunk_id=f"section_{section.number}_with_table",
                section_number=section.number,
                section_title=section.title,
                chunk_type="complete_section_with_table",
                semantic_theme=self._extract_semantic_theme(section.content),
                list_items=self._extract_list_items(section.content),
                start_position=0,
                end_position=len(section.content)
            )
            return [chunk]
    
    # Apply normal chunking logic for non-table sections
    # ... existing chunking logic ...
```

### 4. Update LangExtract Chunking

Modify langextract_chunking.py to preserve tables:

```python
def _chunk_section(self, section: Dict[str, Any], section_index: int) -> List[LangExtractChunk]:
    # Check if section contains tables
    if '[TABLE]' in section['content']:
        # Keep entire section as one chunk if it contains tables
        if len(section['content']) <= self.max_chunk_size * 2:
            chunk = LangExtractChunk(
                content=section['content'],
                chunk_id=f"langextract_section_{section_index}_with_table",
                section_type=section['type'],
                section_title=section['title'],
                chunk_type="complete_section_with_table",
                semantic_theme=section['type'],
                list_items=self._extract_list_items(section['content']),
                start_position=0,
                end_position=len(section['content']),
                confidence=0.9,
                extraction_method='table_preservation'
            )
            return [chunk]
    
    # Apply normal chunking logic
    # ... existing chunking logic ...
```

### 5. Benefits of Table Preservation

- **Complete Table Queries**: Users can ask for complete table breakdowns
- **Service Level Analysis**: Full service level tables can be retrieved
- **Metric Comparisons**: All metrics in a table can be compared
- **Column Analysis**: Complete columns (like Service Bundle Ref.) can be analyzed
- **Better RAG Performance**: More complete context for table-related queries

### 6. Testing Table Preservation

Test with queries like:
- "Provide a full breakdown of each service level, including the specific requirements and metrics, include the Service Bundle Ref. column from the table"
- "Show me the complete table with all service levels"
- "What are all the metrics listed in the table?"
- "Compare all the service levels in the table"
"""
    
    print(guide)

if __name__ == "__main__":
    # Analyze current table chunking
    analysis_result = fix_table_chunks_in_chromadb()
    
    # Create implementation guide
    create_table_preservation_guide()
    
    print(f"\n🎯 Summary:")
    print("=" * 50)
    if analysis_result:
        if analysis_result['needs_fixing']:
            print(f"❌ Table chunking needs to be fixed!")
            print(f"   - {analysis_result['incomplete_tables']} chunks have incomplete tables")
            print(f"   - This is causing your query issues")
            print(f"   - Follow the implementation guide above to fix")
        else:
            print(f"✅ Table chunking is working correctly!")
            print(f"   - All {analysis_result['complete_tables']} tables are complete")
            print(f"   - No fixing needed")
    else:
        print(f"❌ Could not analyze table chunking")
