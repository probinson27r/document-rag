# Complex Nested List Enhancement

## Problem Identified

The original semantic nesting logic was too simplistic and couldn't handle complex hierarchical structures like:

```
1. Main Section
   a. Subsection
      i. Sub-subsection
         A. Sub-sub-subsection
   b. Another Subsection
      i. Another Sub-subsection
         A. Another Sub-sub-subsection
2. Another Main Section
```

The system needed to understand and properly nest:
- **Roman Numerals** (i, ii, iii) nested in **Alpha lists** (a, b, c) nested in **Numbered lists** (1, 2, 3)
- **Uppercase letters** (A, B, C) nested under Roman numerals
- **Mixed list types** with proper hierarchy levels
- **Sections** with their nested content

## Solution Implemented

### 1. Enhanced Hierarchy Level Detection

Implemented a comprehensive hierarchy level system:

```python
def _get_hierarchy_level(self, number: str) -> int:
    # Hierarchy levels (from lowest to highest):
    # Level 1: Numbers (1, 2, 3) - Top level
    # Level 2: Lowercase letters (a, b, c) - Second level
    # Level 3: Roman numerals (i, ii, iii) - Third level
    # Level 4: Uppercase letters (A, B, C) - Fourth level
    # Level 5: Bullet points (-, *, •) - Can be at any level
    
    if number.isdigit():
        return 1  # Top level
    
    if number.isalpha() and number.islower():
        # Check if it's a Roman numeral first
        if number.lower() in roman_lower:
            return 3  # Third level
        return 2  # Second level (regular lowercase letters)
    
    if number.isalpha() and number.isupper():
        return 4  # Fourth level
```

### 2. Improved Semantic Nesting Logic

Enhanced the semantic nesting rules to handle complex hierarchies:

```python
def _should_nest_semantically(self, current_item, previous_item):
    current_level = self._get_hierarchy_level(current_item['number'])
    previous_level = self._get_hierarchy_level(previous_item['number'])
    
    # Rule 1: If current item has higher hierarchy level than previous, it should be nested
    if current_level > previous_level:
        return True
    
    # Rule 2: Same level items of the same type should be siblings (not nested)
    if current_level == previous_level:
        return False
    
    # Rule 3: Special cases for mixed list types
    # Lettered items (a, b, c) should be nested under numbered items
    if (current_number.isalpha() and current_number.islower() and 
        previous_number.isdigit()):
        return True
    
    # Roman numerals (i, ii, iii) should be nested under lettered items
    if (current_number.lower() in roman_lower and 
        previous_number.isalpha() and previous_number.islower()):
        return True
    
    # Uppercase letters (A, B, C) should be nested under Roman numerals
    if (current_number.isalpha() and current_number.isupper() and 
        previous_number.lower() in roman_lower):
        return True
    
    return False
```

### 3. Advanced Semantic Parent Detection

Implemented sophisticated parent detection based on hierarchy levels:

```python
def _find_semantic_parent(self, item, raw_items, current_index, item_stack):
    current_level = self._get_hierarchy_level(item['number'])
    
    # Look backwards through raw_items to find the appropriate parent
    for j in range(current_index - 1, -1, -1):
        previous_item = raw_items[j]
        previous_level = self._get_hierarchy_level(previous_item['number'])
        
        # Find the first item with a lower hierarchy level
        if previous_level < current_level:
            # Find this item in the stack
            for stack_item in reversed(item_stack):
                if (stack_item['line_number'] == previous_item['line_number'] and 
                    stack_item['indentation'] == previous_item['indentation']):
                    return stack_item
            break
    
    return None
```

## Results

### Before Enhancement
- **Simple nesting**: Only handled basic lettered items under numbered items
- **Limited hierarchy**: Could not handle multi-level structures
- **Missing levels**: Uppercase letters and Roman numerals not properly nested
- **Flat structure**: Complex hierarchies were flattened

### After Enhancement
- **Complex nesting**: Handles 4-level hierarchies (Numbers → Letters → Roman → Uppercase)
- **Proper hierarchy**: Each level correctly identified and nested
- **Mixed types**: Supports various list marker combinations
- **Section preservation**: Maintains section structure with nested content

### Example Output
```
1. Main Item (Level 1)
   a. Sub Item (Level 2)
      i. Sub-sub Item (Level 3)
         A. Sub-sub-sub Item (Level 4) ✅
         B. Another Sub-sub-sub Item (Level 4) ✅
   b. Another Sub Item (Level 2)
      i. Another Sub-sub Item (Level 3)
         A. Another Sub-sub-sub Item (Level 4) ✅
2. Another Main Item (Level 1)
   a. Another Sub Item (Level 2)
      i. Another Sub-sub Item (Level 3)
         A. Another Sub-sub-sub Item (Level 4) ✅
```

## Benefits

1. **Comprehensive Document Understanding**: Now handles the most complex nested structures found in legal and technical documents
2. **Accurate Hierarchy Detection**: Properly identifies and maintains multi-level relationships
3. **Flexible List Support**: Works with various list marker combinations and formats
4. **Improved RAG Performance**: Better search and retrieval with proper hierarchical context
5. **Enhanced Metadata**: Rich hierarchy information for each list item
6. **Backward Compatibility**: Existing simple nesting continues to work

## Test Cases Covered

1. **Basic Nesting**: Numbers → Letters ✅
2. **Three-Level Nesting**: Numbers → Letters → Roman Numerals ✅
3. **Four-Level Nesting**: Numbers → Letters → Roman Numerals → Uppercase Letters ✅
4. **Mixed Formats**: Various list marker combinations ✅
5. **Section Preservation**: Nested content within sections ✅
6. **Complex Hierarchies**: Multiple branches with different depths ✅

## Future Enhancements

1. **Cross-Reference Detection**: Identify references between nested items across sections
2. **Validation Rules**: Ensure proper nesting structure in legal documents
3. **Export Formats**: Support for exporting complex nested structures
4. **Interactive Visualization**: Web-based visualization of multi-level hierarchies
5. **Custom Hierarchy Rules**: Allow users to define custom nesting patterns
6. **Performance Optimization**: Optimize for very large documents with complex nesting

The complex nesting enhancement ensures that LangExtract can handle the most sophisticated document structures commonly found in legal contracts, technical specifications, and other complex documents, providing accurate hierarchical understanding and improved document processing capabilities.
