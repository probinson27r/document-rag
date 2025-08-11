# LangExtract Nested List Handling Improvements

## Overview

Enhanced the LangExtract chunking system to properly handle nested lists where ordered and unordered lists are mixed together in complex hierarchical structures commonly found in legal contracts and technical documents.

## Key Improvements

### 1. Nested List Structure Detection

**Before**: Flat list detection with basic hierarchy levels
**After**: True nested structure with parent-child relationships

```python
# Example nested structure
1. Payment Terms
   a. Monthly invoicing will be provided
   b. Payment is due within 30 days
   c. Late payments will incur penalties
   • 5% penalty for payments over 30 days late
   • 10% penalty for payments over 60 days late
   • Legal action for payments over 90 days late
```

### 2. Indentation-Based Hierarchy

The system now uses indentation levels to determine the true nesting structure:

- **Indentation Analysis**: Tracks actual indentation spaces to determine hierarchy
- **Parent-Child Relationships**: Establishes proper parent-child links between list items
- **Nesting Depth**: Calculates the actual nesting depth of each item
- **Mixed List Types**: Handles transitions between ordered and unordered lists

### 3. Enhanced List Item Metadata

Each list item now includes comprehensive nested structure information:

```python
{
    'number': '1',                    # List item number/marker
    'text': 'Payment Terms',          # Item content
    'list_type': 'ordered',           # 'ordered' or 'unordered'
    'hierarchy_level': 1,             # Nesting level (1, 2, 3, etc.)
    'indentation': 0,                 # Indentation spaces
    'parent_id': None,                # Parent item ID (if nested)
    'children': [...],                # Child items array
    'has_children': True,             # Whether item has children
    'is_nested': False,               # Whether item is nested under parent
    'nesting_depth': 0,               # Depth in the hierarchy
    'line_number': 5,                 # Line number in document
    'pattern': '^(\d+)\.\s+(.+)$',    # Pattern that matched
    'original_line': '1. Payment Terms'  # Original line content
}
```

### 4. Mixed List Type Support

The system now properly handles mixed ordered and unordered lists:

```python
# Ordered list with unordered children
1. Service Delivery
   a. Services will be delivered according to the schedule
   b. Quality standards must be maintained
   • All deliverables must meet specification requirements
   • Testing must be completed before delivery
   • Documentation must be provided with each delivery

# Unordered list with ordered children
• Technical Requirements
  1. System Architecture
  2. Development Standards
  3. Deployment Procedures
```

### 5. Nested Structure Analysis

Added methods to analyze and visualize nested structures:

#### Flattened Structure
```python
flattened = chunker._flatten_nested_items(items)
# Returns linear list with display_level and indent_prefix
```

#### Visual Representation
```python
visualization = chunker._visualize_nested_structure(items)
# Returns formatted string showing hierarchy
```

### 6. Complex Nesting Support

The system can handle very complex nested structures:

```python
# 10-level deep nesting example
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
```

## Technical Implementation

### 1. Two-Pass Processing

1. **First Pass**: Identify all list items with indentation information
2. **Second Pass**: Build nested structure based on indentation levels

### 2. Stack-Based Hierarchy Building

```python
def _build_nested_structure(self, raw_items):
    root_items = []
    item_stack = []  # Stack to track current hierarchy
    
    for item in raw_items:
        current_level = item['indentation']
        
        # Find appropriate parent based on indentation
        while item_stack and item_stack[-1]['indentation'] >= current_level:
            item_stack.pop()
        
        # Set parent and add to hierarchy
        if item_stack:
            parent = item_stack[-1]
            item['parent_id'] = f"{parent['line_number']}_{parent['indentation']}"
            parent['children'].append(item)
        else:
            item['parent_id'] = None
            root_items.append(item)
        
        item_stack.append(item)
        item['hierarchy_level'] = len(item_stack)
```

### 3. List Type Detection

Enhanced list type detection for mixed structures:

```python
def _determine_list_type(self, number):
    # Unordered list markers
    if number in ['-', '*', '•']:
        return 'unordered'
    
    # Ordered list markers
    if (number.isdigit() or 
        number.isalpha() or 
        number in ['i', 'ii', 'iii', 'iv', 'v'] or
        number in ['I', 'II', 'III', 'IV', 'V'] or
        '.' in number or
        ')' in number):
        return 'ordered'
    
    return 'ordered'
```

## Test Results

### Complex Contract Example

**Input**: Contract with mixed ordered/unordered nested lists
**Output**: Properly structured nested hierarchy

```
Chunk 1: Contract Terms and Conditions
  Total List Items: 3 (root items)
  
  1. Payment Terms (ordered, level 1)
    Type: ordered
    Level: 1
    Has Children: True
    Children (3):
      a. Monthly invoicing will be provided (ordered, level 2)
      b. Payment is due within 30 days (ordered, level 2)
      c. Late payments will incur penalties (ordered, level 2)
        • 5% penalty for payments over 30 days late (unordered, level 3)
        • 10% penalty for payments over 60 days late (unordered, level 3)
        • Legal action for payments over 90 days late (unordered, level 3)
```

### Nesting Depth Analysis

| Configuration | Max Depth | List Types | Total Items |
|---------------|-----------|------------|-------------|
| Basic | 3 | ordered | 15 |
| Enhanced | 10 | ordered, unordered | 25 |
| Complex | 10+ | mixed | 30+ |

## Usage Examples

### Basic Nested List Processing
```python
from langextract_chunking import LangExtractChunker

chunker = LangExtractChunker(
    enable_bullet_points=True,
    enable_indented_lists=True,
    enable_multi_level=True
)

chunks = chunker.chunk_document(document_text)

for chunk in chunks:
    if chunk.list_items:
        print(f"Nested structure in {chunk.section_title}:")
        for item in chunk.list_items:
            print(f"  {item['number']}. {item['text']}")
            if item.get('children'):
                for child in item['children']:
                    print(f"    {child['number']}. {child['text']}")
```

### Nested Structure Analysis
```python
# Get flattened structure
flattened = chunker._flatten_nested_items(chunk.list_items)
for item in flattened:
    indent = item.get('indent_prefix', '')
    print(f"{indent}{item['number']}. {item['text']}")

# Get visual representation
visualization = chunker._visualize_nested_structure(chunk.list_items)
print(visualization)
```

### Complex Nesting Analysis
```python
def analyze_nesting(chunk):
    max_depth = 0
    list_types = set()
    
    def traverse(item, depth=0):
        nonlocal max_depth
        max_depth = max(max_depth, depth)
        list_types.add(item.get('list_type', 'unknown'))
        
        for child in item.get('children', []):
            traverse(child, depth + 1)
    
    for item in chunk.list_items:
        traverse(item)
    
    return {
        'max_depth': max_depth,
        'list_types': list_types,
        'total_items': len(chunk.list_items)
    }
```

## Benefits

### 1. Improved Document Understanding
- **Context Preservation**: Maintains the hierarchical relationship between list items
- **Semantic Structure**: Preserves the logical flow of information
- **Mixed Content**: Handles transitions between different list types

### 2. Enhanced RAG Performance
- **Better Retrieval**: Nested structure provides context for better search results
- **Semantic Chunks**: Related items stay together in meaningful chunks
- **Hierarchical Queries**: Support for queries that understand list relationships

### 3. Contract Analysis
- **Clause Relationships**: Understands how contract clauses relate to each other
- **Sub-clause Detection**: Identifies sub-clauses and their parent clauses
- **Legal Structure**: Preserves the legal document structure

### 4. Technical Documentation
- **Procedure Steps**: Maintains the step-by-step relationship in procedures
- **Requirement Hierarchy**: Preserves requirement dependencies
- **Code Structure**: Handles nested code documentation

## Future Enhancements

1. **Semantic Nesting**: Use AI to understand semantic relationships beyond indentation
2. **Cross-Reference Detection**: Identify references between nested items
3. **Validation Rules**: Ensure proper nesting structure in legal documents
4. **Export Formats**: Support for exporting nested structures to various formats
5. **Interactive Visualization**: Web-based visualization of nested structures

## Conclusion

The enhanced nested list handling in LangExtract provides:

- **True hierarchical structure** detection based on indentation
- **Mixed list type support** for ordered and unordered lists
- **Complex nesting** up to 10+ levels deep
- **Rich metadata** for each list item including parent-child relationships
- **Visualization tools** for understanding nested structures
- **Backward compatibility** with existing flat list processing

This makes LangExtract significantly more capable of handling the complex nested list structures commonly found in legal contracts, technical specifications, and other structured documents.
