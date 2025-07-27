import logging
import os
import re
from typing import List, Dict, Tuple
import fitz  # PyMuPDF

def is_ordered_list_item(text: str) -> Tuple[bool, str, int]:
    """
    Check if text starts with an ordered list marker.
    Returns (is_list_item, marker_type, level)
    """
    # Count leading whitespace to determine indentation level
    leading_spaces = len(text) - len(text.lstrip())
    
    # Remove leading whitespace for pattern matching
    stripped = text.lstrip()
    
    # Patterns for different types of ordered lists
    patterns = [
        # Compact hierarchical patterns (3.2(a)(i), 1.1(a)(1), etc.)
        (r'^\d+\.\d+\([a-z]\)\([ivx]+\)', 'compact_hierarchical', 3),  # 3.2(a)(i), 3.2(a)(ii), etc.
        (r'^\d+\.\d+\([a-z]\)', 'compact_hierarchical', 2),           # 3.2(a), 3.2(b), etc.
        (r'^\d+\.\d+\([A-Z]\)', 'compact_hierarchical', 2),           # 3.2(A), 3.2(B), etc.
        
        # Hierarchical numeric patterns (1.1, 1.2, 1.1.1, 1.1.2, etc.)
        (r'^\d+\.\d+\.\d+\.\s+', 'hierarchical_numeric', 3),  # 1.1.1, 1.1.2, etc.
        (r'^\d+\.\d+\.\s+', 'hierarchical_numeric', 2),       # 1.1, 1.2, 2.1, etc.
        
        # Section headings (3 OBJECTIVES, 3.1 List of Objectives, etc.)
        (r'^\d+\s+[A-Z][A-Za-z\s]+$', 'section_heading', 1),     # 3 OBJECTIVES
        (r'^\d+\.\d+\s+[A-Z][A-Za-z\s]+$', 'subsection_heading', 2),  # 3.1 List of Objectives
        
        # Roman numerals (I, II, III, IV, V, VI, VII, VIII, IX, X, etc.)
        (r'^[IVX]+\.\s+', 'roman', 1),
        (r'^[ivx]+\.\s+', 'roman_lower', 1),
        (r'^\([IVX]+\)\s+', 'roman_paren', 1),
        (r'^\([ivx]+\)\s+', 'roman_lower_paren', 1),
        
        # Alphabetic with parentheses (a), (b), (c), (A), (B), (C)
        (r'^\([A-Z]\)\s+', 'alpha_upper_paren', 1),
        (r'^\([a-z]\)\s+', 'alpha_lower_paren', 1),
        
        # Alphabetic with periods (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z)
        (r'^[A-Z]\.\s+', 'alpha_upper', 1),
        (r'^[a-z]\.\s+', 'alpha_lower', 1),
        
        # Numeric (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, etc.)
        (r'^\d+\.\s+', 'numeric', 1),
    ]
    
    for pattern, marker_type, base_level in patterns:
        if re.match(pattern, stripped):
            # For hierarchical patterns, the level is determined by the pattern itself
            if marker_type == 'hierarchical_numeric':
                level = base_level
            else:
                # For other patterns, adjust level based on indentation
                if leading_spaces == 0:
                    level = base_level
                elif leading_spaces <= 3:
                    level = base_level + 1
                else:
                    level = base_level + 2
            return True, marker_type, level
    
    return False, '', 0

def get_list_hierarchy_level(text: str) -> int:
    """
    Determine the hierarchical level of a list item based on its marker type and context.
    This handles mixed hierarchical patterns like "1. A. i."
    """
    is_list, marker_type, base_level = is_ordered_list_item(text)
    
    if not is_list:
        return 0
    
    # Define hierarchy levels for different marker types
    hierarchy_levels = {
        'numeric': 1,           # 1, 2, 3, etc.
        'hierarchical_numeric': base_level,  # 1.1, 1.1.1, etc.
        'compact_hierarchical': base_level,  # 3.2(a), 3.2(a)(i), etc.
        'section_heading': 1,   # 3 OBJECTIVES
        'subsection_heading': 2, # 3.1 List of Objectives
        'alpha_upper': 2,       # A, B, C, etc.
        'alpha_lower': 3,       # a, b, c, etc.
        'alpha_upper_paren': 2, # (A), (B), (C), etc.
        'alpha_lower_paren': 3, # (a), (b), (c), etc.
        'roman': 2,             # I, II, III, etc.
        'roman_lower': 3,       # i, ii, iii, etc.
        'roman_paren': 2,       # (I), (II), (III), etc.
        'roman_lower_paren': 3, # (i), (ii), (iii), etc.
    }
    
    return hierarchy_levels.get(marker_type, base_level)

def split_text_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs, preserving list structure.
    """
    # Split by double newlines to get paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    # Filter out footer content and empty paragraphs
    filtered_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p:
            # Check if the entire paragraph is footer content
            lines = p.split('\n')
            non_footer_lines = []
            for line in lines:
                line = line.strip()
                if line and not is_footer_content(line):
                    non_footer_lines.append(line)
            
            # If we have non-footer content, create a paragraph
            if non_footer_lines:
                filtered_paragraphs.append('\n'.join(non_footer_lines))
    
    return filtered_paragraphs

def is_footer_content(text: str) -> bool:
    """
    Check if text appears to be footer content that should be ignored.
    """
    # Common footer patterns
    footer_patterns = [
        r'^\d+$',  # Just page numbers
        r'^Page \d+$',  # "Page 1", "Page 2", etc.
        r'^Page \d+ of \d+$',  # "Page 1 of 10", etc.
        r'^\d+ of \d+$',  # "1 of 10", etc.
        r'^©\s*\d{4}',  # Copyright notices
        r'^Copyright\s+\d{4}',  # Copyright notices
        r'^All rights reserved',  # Legal notices
        r'^Confidential',  # Confidentiality notices
        r'^Draft',  # Draft notices
        r'^Version \d+',  # Version numbers
        r'^Rev\. \d+',  # Revision numbers
        r'^Date:',  # Date stamps
        r'^\d{1,2}/\d{1,2}/\d{4}',  # Date formats
        r'^\d{4}-\d{2}-\d{2}',  # ISO date formats
        r'^Generated on:',  # Generation timestamps
        r'^Last modified:',  # Modification timestamps
        r'^File:',  # File information
        r'^Document:',  # Document information
        r'^Prepared by:',  # Author information
        r'^Approved by:',  # Approval information
        r'^Signed by:',  # Signature information
        r'^Witnessed by:',  # Witness information
        r'^Notary:',  # Notary information
        r'^Attorney:',  # Attorney information
        r'^Law Firm:',  # Law firm information
        r'^Address:',  # Address information
        r'^Phone:',  # Phone information
        r'^Email:',  # Email information
        r'^Fax:',  # Fax information
        r'^Website:',  # Website information
        r'^www\.',  # Website URLs
        r'^http://',  # HTTP URLs
        r'^https://',  # HTTPS URLs
        r'^[A-Z]{2,}\d{2,}$',  # Document codes like "ED19024"
        r'^[A-Z]{2,}-\d{2,}$',  # Document codes with hyphens
        r'^[A-Z]{2,}_\d{2,}$',  # Document codes with underscores
        r'^PROTECTED',  # Protected document notices
        r'^CONFIDENTIAL',  # Confidential notices
        r'^PRIVILEGED',  # Privileged notices
        r'^ATTORNEY-CLIENT',  # Attorney-client privilege notices
        r'^WORK PRODUCT',  # Work product notices
        r'^DRAFT',  # Draft notices
        r'^FINAL',  # Final notices
        r'^APPROVED',  # Approved notices
        r'^PENDING',  # Pending notices
        r'^REVIEW',  # Review notices
        r'^SIGNED',  # Signed notices
        r'^EXECUTED',  # Executed notices
        r'^EFFECTIVE',  # Effective date notices
        r'^EXPIRES',  # Expiration notices
        r'^TERMINATED',  # Termination notices
        r'^AMENDED',  # Amendment notices
        r'^SUPPLEMENT',  # Supplement notices
        r'^ADDENDUM',  # Addendum notices
        r'^SCHEDULE',  # Schedule notices
        r'^EXHIBIT',  # Exhibit notices
        r'^APPENDIX',  # Appendix notices
        r'^ATTACHMENT',  # Attachment notices
        r'^ENCLOSURE',  # Enclosure notices
        r'^REFERENCE',  # Reference notices
        r'^CROSS-REFERENCE',  # Cross-reference notices
        r'^SEE ALSO',  # See also notices
        r'^SEE ABOVE',  # See above notices
        r'^SEE BELOW',  # See below notices
        r'^CONTINUED',  # Continued notices
        r'^CONTINUES',  # Continues notices
        r'^END OF',  # End of notices
        r'^END OF DOCUMENT',  # End of document notices
        r'^END OF AGREEMENT',  # End of agreement notices
        r'^END OF CONTRACT',  # End of contract notices
        r'^END OF SECTION',  # End of section notices
        r'^END OF CLAUSE',  # End of clause notices
        r'^END OF PARAGRAPH',  # End of paragraph notices
        r'^END OF LIST',  # End of list notices
        r'^END OF TABLE',  # End of table notices
        r'^END OF FIGURE',  # End of figure notices
        r'^END OF CHART',  # End of chart notices
        r'^END OF GRAPH',  # End of graph notices
        r'^END OF DIAGRAM',  # End of diagram notices
        r'^END OF ILLUSTRATION',  # End of illustration notices
        r'^END OF PHOTO',  # End of photo notices
        r'^END OF IMAGE',  # End of image notices
        r'^END OF PICTURE',  # End of picture notices
        r'^END OF DRAWING',  # End of drawing notices
        r'^END OF SKETCH',  # End of sketch notices
        r'^END OF PLAN',  # End of plan notices
        r'^END OF MAP',  # End of map notices
        r'^END OF CHART',  # End of chart notices
        r'^END OF GRAPH',  # End of graph notices
        r'^END OF DIAGRAM',  # End of diagram notices
        r'^END OF ILLUSTRATION',  # End of illustration notices
        r'^END OF PHOTO',  # End of photo notices
        r'^END OF IMAGE',  # End of image notices
        r'^END OF PICTURE',  # End of picture notices
        r'^END OF DRAWING',  # End of drawing notices
        r'^END OF SKETCH',  # End of sketch notices
        r'^END OF PLAN',  # End of plan notices
        r'^END OF MAP',  # End of map notices
    ]
    
    # Exclude specific reference patterns that should be kept (check these first)
    exclude_patterns = [
        r'^Trim Reference:',  # Trim Reference: D20/0342792
        r'^Reference:',  # Reference: D20/0342792
        r'^Doc Ref:',  # Doc Ref: D20/0342792
        r'^Document Reference:',  # Document Reference: D20/0342792
        r'^Ref:',  # Ref: D20/0342792
        r'^Document Ref:',  # Document Ref: D20/0342792
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    # Check if text matches any footer pattern
    for pattern in footer_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Check for very short text that's likely footer content
    if len(text) <= 5 and text.isdigit():
        return True
    
    # Check for text that's all uppercase and very short (likely headers/footers)
    # But exclude section headings like "3 OBJECTIVES"
    if len(text) <= 20 and text.isupper() and not text.isdigit():
        # Don't filter out section headings that contain numbers
        if not re.search(r'\d', text):
            return True
    
    # Check for text that contains only common footer words
    footer_words = {
        'page', 'copyright', 'confidential', 'draft', 'version', 'rev', 'date', 
        'generated', 'modified', 'file', 'document', 'prepared', 'approved', 
        'signed', 'witnessed', 'notary', 'attorney', 'firm', 'address', 'phone', 
        'email', 'fax', 'website', 'protected', 'privileged', 'final', 'pending', 
        'review', 'executed', 'effective', 'expires', 'terminated', 'amended', 
        'supplement', 'addendum', 'schedule', 'exhibit', 'appendix', 'attachment', 
        'enclosure', 'continued', 'continues', 'end'
    }
    
    words = text.lower().split()
    if len(words) <= 3 and all(word in footer_words for word in words):
        return True
    
    return False

def should_keep_together(current_chunk: str, next_paragraph: str) -> bool:
    """
    Determine if the next paragraph should be kept with the current chunk.
    """
    # If current chunk is empty, always add
    if not current_chunk.strip():
        return True
    
    # Check if next paragraph is a continuation of a list
    is_list_item, marker_type, level = is_ordered_list_item(next_paragraph)
    
    # If it's a list item, check if current chunk ends with a list item
    if is_list_item:
        lines = current_chunk.split('\n')
        if lines:
            last_line = lines[-1].strip()
            last_is_list, last_marker_type, last_level = is_ordered_list_item(last_line)
            
            # If last line is also a list item, keep together
            if last_is_list:
                # Same marker type and level - definitely keep together
                if marker_type == last_marker_type and level == last_level:
                    return True
                # Different marker types but same hierarchy level - likely related list
                elif get_list_hierarchy_level(next_paragraph) == get_list_hierarchy_level(last_line):
                    return True
                # Nested list - keep together (child of current item)
                elif get_list_hierarchy_level(next_paragraph) > get_list_hierarchy_level(last_line):
                    return True
                # Hierarchical relationship - check if it's a child of the last item
                elif marker_type == 'hierarchical_numeric' and last_marker_type == 'hierarchical_numeric':
                    if is_hierarchical_child(next_paragraph, last_line):
                        return True
                # Mixed hierarchical relationship - check if it's a logical continuation
                elif is_mixed_hierarchical_related(next_paragraph, last_line):
                    return True
    
    # Check if next paragraph is a continuation of the same list level
    if is_list_item:
        # Look for list items in current chunk
        lines = current_chunk.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line:
                line_is_list, line_marker_type, line_level = is_ordered_list_item(line)
                if line_is_list:
                    # Same level and marker type - keep together
                    if line_level == level and line_marker_type == marker_type:
                        return True
                    # Same hierarchy level but different marker type - still related
                    elif get_list_hierarchy_level(next_paragraph) == get_list_hierarchy_level(line):
                        return True
                    # Hierarchical relationship - check if it's related to this line
                    elif marker_type == 'hierarchical_numeric' and line_marker_type == 'hierarchical_numeric':
                        if is_hierarchical_related(next_paragraph, line):
                            return True
                    # Mixed hierarchical relationship
                    elif is_mixed_hierarchical_related(next_paragraph, line):
                        return True
                    # Found a different list level - stop looking
                    else:
                        break
    
    # Enhanced hierarchical section logic
    if is_list_item:
        # Check if this item belongs to a hierarchical section that's already in the chunk
        if is_part_of_hierarchical_section(current_chunk, next_paragraph):
            # Only keep together if the combined length is reasonable
            combined_length = len(current_chunk) + len(next_paragraph)
            if combined_length < 1500:  # Allow slightly larger chunks for hierarchical sections
                return True
    
    # Break at major section boundaries
    if is_list_item:
        is_section_header = marker_type in ['section_heading', 'subsection_heading']
        if is_section_header:
            # Check if current chunk already has a section header
            lines = current_chunk.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    line_is_list, line_marker_type, _ = is_ordered_list_item(line)
                    if line_is_list and line_marker_type in ['section_heading', 'subsection_heading']:
                        # If we already have a section header, start a new chunk
                        return False
    
    # Check total length - use smaller chunks for better RAG performance
    combined_length = len(current_chunk) + len(next_paragraph)
    return combined_length < 1000  # Reduced limit for better chunking

def is_part_of_hierarchical_section(chunk: str, item: str) -> bool:
    """
    Check if an item is part of a hierarchical section that's already in the chunk.
    This ensures that hierarchical structures like "3.2 -> (a) -> (i)" stay together.
    """
    # Get the hierarchy level of the current item
    item_is_list, item_marker_type, item_level = is_ordered_list_item(item)
    if not item_is_list:
        return False
    
    item_hierarchy_level = get_list_hierarchy_level(item)
    
    # Look for section headers or higher-level items in the chunk
    lines = chunk.split('\n')
    for line in lines:
        line = line.strip()
        if line:
            line_is_list, line_marker_type, line_level = is_ordered_list_item(line)
            if line_is_list:
                line_hierarchy_level = get_list_hierarchy_level(line)
                
                # If the current item is at a lower hierarchy level than something in the chunk,
                # and they're related, keep them together
                if item_hierarchy_level > line_hierarchy_level:
                    # Check if they're in the same hierarchical section
                    if are_in_same_hierarchical_section(line, item):
                        return True
                
                # If they're at the same hierarchy level and related, keep together
                elif item_hierarchy_level == line_hierarchy_level:
                    if are_in_same_hierarchical_section(line, item):
                        return True
    
    # Check if this is a direct continuation of a hierarchical structure
    # Look for the most recent list item in the chunk
    for line in reversed(lines):
        line = line.strip()
        if line:
            line_is_list, line_marker_type, line_level = is_ordered_list_item(line)
            if line_is_list:
                # If this item is a direct child or sibling of the last list item, keep together
                if is_direct_hierarchical_continuation(line, item):
                    return True
                break
    
    return False

def is_direct_hierarchical_continuation(parent: str, child: str) -> bool:
    """
    Check if a child item is a direct continuation of a parent in a hierarchical structure.
    This handles cases like "3.2(a)" -> "(i)" or "3.2(a)(i)" -> "(ii)".
    """
    parent_is_list, parent_marker_type, parent_level = is_ordered_list_item(parent)
    child_is_list, child_marker_type, child_level = is_ordered_list_item(child)
    
    if not parent_is_list or not child_is_list:
        return False
    
    # Check if they're in the same section
    if not are_in_same_hierarchical_section(parent, child):
        return False
    
    # Check if child is a direct continuation (same level or next level down)
    parent_hierarchy = get_list_hierarchy_level(parent)
    child_hierarchy = get_list_hierarchy_level(child)
    
    # Direct child (one level down)
    if child_hierarchy == parent_hierarchy + 1:
        return True
    
    # Same level sibling
    if child_hierarchy == parent_hierarchy:
        return True
    
    return False

def are_in_same_hierarchical_section(item1: str, item2: str) -> bool:
    """
    Check if two items belong to the same hierarchical section.
    This handles patterns like "3.2", "(a)", "(i)" all belonging to section 3.
    """
    # Extract section numbers from hierarchical items
    section1 = extract_section_number(item1)
    section2 = extract_section_number(item2)
    
    if section1 and section2:
        return section1 == section2
    
    # If one has a section number and the other doesn't, they're not in the same section
    if (section1 and not section2) or (section2 and not section1):
        return False
    
    # For non-hierarchical items, check if they're related through mixed hierarchical logic
    # but only if they're at the same hierarchy level or consecutive levels
    if is_mixed_hierarchical_related(item1, item2):
        level1 = get_list_hierarchy_level(item1)
        level2 = get_list_hierarchy_level(item2)
        # Only consider them in the same section if they're at the same level or consecutive
        return abs(level1 - level2) <= 1
    
    return False

def extract_section_number(item: str) -> str:
    """
    Extract the main section number from a hierarchical item.
    Examples:
    - "3.2(a)(i)" -> "3"
    - "3.1 List of Objectives" -> "3"
    - "3 OBJECTIVES" -> "3"
    - "(a) The objectives..." -> None (no section number)
    """
    # Try to extract section number from various patterns
    patterns = [
        r'^(\d+)\.\d+\([a-zA-Z]\)\([ivx]+\)',  # 3.2(a)(i)
        r'^(\d+)\.\d+\([a-zA-Z]\)',            # 3.2(a)
        r'^(\d+)\.\d+\.\d+',                   # 3.2.1
        r'^(\d+)\.\d+',                        # 3.2
        r'^(\d+)\s+[A-Z]',                     # 3 OBJECTIVES
    ]
    
    for pattern in patterns:
        match = re.match(pattern, item.lstrip())
        if match:
            return match.group(1)
    
    return None

def is_hierarchical_child(child_text: str, parent_text: str) -> bool:
    """
    Check if a hierarchical list item is a direct child of another.
    """
    child_match = re.match(r'^(\d+\.\d+(?:\.\d+)?)', child_text.lstrip())
    parent_match = re.match(r'^(\d+(?:\.\d+)?)', parent_text.lstrip())
    
    if not child_match or not parent_match:
        return False
    
    child_num = child_match.group(1)
    parent_num = parent_match.group(1)
    
    # Check if child is a direct descendant (e.g., 1.1.1 is child of 1.1, 1.1 is child of 1)
    return child_num.startswith(parent_num + '.') and len(child_num.split('.')) == len(parent_num.split('.')) + 1

def is_hierarchical_related(text1: str, text2: str) -> bool:
    """
    Check if two hierarchical list items are related (same parent or siblings).
    """
    match1 = re.match(r'^(\d+(?:\.\d+)?)', text1.lstrip())
    match2 = re.match(r'^(\d+(?:\.\d+)?)', text2.lstrip())
    
    if not match1 or not match2:
        return False
    
    num1 = match1.group(1)
    num2 = match2.group(1)
    
    # Same item
    if num1 == num2:
        return True
    
    # Same level siblings (e.g., 1.1 and 1.2, or 1 and 2)
    if len(num1.split('.')) == len(num2.split('.')):
        if len(num1.split('.')) == 1:
            # Top level siblings (1, 2, 3, etc.)
            return True
        else:
            # Nested siblings (1.1, 1.2, etc.)
            parent1 = '.'.join(num1.split('.')[:-1])
            parent2 = '.'.join(num2.split('.')[:-1])
            return parent1 == parent2
    
    # Parent-child relationship
    if len(num1.split('.')) > len(num2.split('.')):
        return num1.startswith(num2 + '.')
    elif len(num2.split('.')) > len(num1.split('.')):
        return num2.startswith(num1 + '.')
    
    return False

def is_mixed_hierarchical_related(text1: str, text2: str) -> bool:
    """
    Check if two list items with different marker types are hierarchically related.
    This handles patterns like "1. A. i." where different numbering types are nested.
    """
    is_list1, marker_type1, _ = is_ordered_list_item(text1)
    is_list2, marker_type2, _ = is_ordered_list_item(text2)
    
    if not is_list1 or not is_list2:
        return False
    
    # Check for compact hierarchical relationships first
    if is_compact_hierarchical_related(text1, text2):
        return True
    
    # Get hierarchy levels
    level1 = get_list_hierarchy_level(text1)
    level2 = get_list_hierarchy_level(text2)
    
    # Same hierarchy level - likely siblings
    if level1 == level2:
        return True
    
    # Consecutive hierarchy levels - likely parent-child
    if abs(level1 - level2) == 1:
        return True
    
    # Check for common patterns in legal documents
    # Pattern: 1. -> A. -> i. (numeric -> alpha_upper -> roman_lower)
    # Pattern: 1. -> (A) -> (a) (numeric -> alpha_upper_paren -> alpha_lower_paren)
    # Pattern: 3 OBJECTIVES -> 3.1 List of Objectives -> (a) -> (i) (section_heading -> subsection_heading -> alpha_lower_paren -> roman_lower_paren)
    if (marker_type1 == 'numeric' and marker_type2 == 'alpha_upper') or \
       (marker_type1 == 'numeric' and marker_type2 == 'alpha_upper_paren') or \
       (marker_type1 == 'section_heading' and marker_type2 == 'subsection_heading') or \
       (marker_type1 == 'subsection_heading' and marker_type2 == 'alpha_lower_paren') or \
       (marker_type1 == 'alpha_upper' and marker_type2 == 'roman_lower') or \
       (marker_type1 == 'alpha_upper' and marker_type2 == 'alpha_lower') or \
       (marker_type1 == 'alpha_upper_paren' and marker_type2 == 'alpha_lower_paren') or \
       (marker_type1 == 'alpha_upper_paren' and marker_type2 == 'roman_lower') or \
       (marker_type1 == 'roman' and marker_type2 == 'roman_lower'):
        return True
    
    return False

def is_compact_hierarchical_related(text1: str, text2: str) -> bool:
    """
    Check if two compact hierarchical list items are related.
    This handles patterns like "3.2(a)" and "3.2(a)(i)".
    """
    # Extract compact hierarchical patterns
    match1 = re.match(r'^(\d+\.\d+)(?:\([a-zA-Z]\))?(?:\([ivx]+\))?', text1.lstrip())
    match2 = re.match(r'^(\d+\.\d+)(?:\([a-zA-Z]\))?(?:\([ivx]+\))?', text2.lstrip())
    
    if not match1 or not match2:
        return False
    
    base1 = match1.group(1)  # e.g., "3.2"
    base2 = match2.group(1)  # e.g., "3.2"
    
    # Same base - definitely related
    if base1 == base2:
        return True
    
    # Check if they share the same parent section
    parent1 = base1.split('.')[0]  # e.g., "3"
    parent2 = base2.split('.')[0]  # e.g., "3"
    
    if parent1 == parent2:
        return True
    
    return False

def identify_document_sections(full_text: str) -> list:
    """
    Identify all sections in the document and their boundaries.
    Returns a list of sections with their content and metadata.
    """
    sections = []
    lines = full_text.split('\n')
    
    current_section = None
    current_content = []
    current_pages = set()
    
    # Extract page numbers from the full text first
    page_numbers = extract_page_numbers_from_text(full_text)
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if this line starts a new section
        section_info = detect_section_start(line)
        
        if section_info:
            # Save previous section if it exists
            if current_section:
                # Estimate page numbers for this section based on line position
                estimated_pages = estimate_pages_for_section(
                    current_section['start_line'], 
                    line_num - 1, 
                    len(lines), 
                    page_numbers
                )
                
                sections.append({
                    'section_number': current_section['number'],
                    'section_title': current_section['title'],
                    'content': '\n'.join(current_content),
                    'pages': estimated_pages,
                    'start_line': current_section['start_line'],
                    'end_line': line_num - 1
                })
            
            # Start new section
            current_section = {
                'number': section_info['number'],
                'title': section_info['title'],
                'start_line': line_num
            }
            current_content = [line]
        else:
            # Continue current section
            if current_section:
                current_content.append(line)
    
    # Add the last section
    if current_section:
        # Estimate page numbers for the last section
        estimated_pages = estimate_pages_for_section(
            current_section['start_line'], 
            len(lines) - 1, 
            len(lines), 
            page_numbers
        )
        
        sections.append({
            'section_number': current_section['number'],
            'section_title': current_section['title'],
            'content': '\n'.join(current_content),
            'pages': estimated_pages,
            'start_line': current_section['start_line'],
            'end_line': len(lines) - 1
        })
    
    return sections

def extract_page_numbers_from_text(text: str) -> list:
    """
    Extract page numbers from the text to help with page estimation.
    """
    page_numbers = []
    
    # Look for page number patterns
    page_patterns = [
        r'Page\s+(\d+)',
        r'^\s*(\d+)\s*$',  # Just a number on a line
        r'^\s*(\d+)\s*of\s*\d+\s*$',  # "1 of 10" format
    ]
    
    lines = text.split('\n')
    for line_num, line in enumerate(lines):
        for pattern in page_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                try:
                    page_num = int(match)
                    page_numbers.append((line_num, page_num))
                except ValueError:
                    continue
    
    return page_numbers

def estimate_pages_for_section(start_line: int, end_line: int, total_lines: int, page_numbers: list) -> list:
    """
    Estimate which pages a section spans based on line positions and known page numbers.
    """
    if not page_numbers:
        return []
    
    # Find the page numbers that fall within this section's line range
    section_pages = set()
    
    for line_num, page_num in page_numbers:
        if start_line <= line_num <= end_line:
            section_pages.add(page_num)
    
    # If no page numbers found in section, estimate based on position
    if not section_pages:
        # Estimate based on line position relative to total lines
        # This is a rough approximation
        if total_lines > 0:
            start_ratio = start_line / total_lines
            end_ratio = end_line / total_lines
            
            # Assume roughly 50 lines per page (very rough estimate)
            estimated_start_page = max(1, int(start_ratio * total_lines / 50))
            estimated_end_page = max(1, int(end_ratio * total_lines / 50))
            
            section_pages = set(range(estimated_start_page, estimated_end_page + 1))
    
    return sorted(list(section_pages))

def detect_section_start(line: str) -> dict:
    """
    Detect if a line starts a new section.
    Returns section info or None if not a section start.
    """
    # Check for section headings using existing logic
    is_list, marker_type, level = is_ordered_list_item(line)
    
    if is_list and marker_type in ['section_heading', 'subsection_heading']:
        section_number = extract_section_number(line)
        if section_number:
            return {
                'number': section_number,
                'title': line,
                'type': marker_type
            }
    
    if is_list and marker_type == 'hierarchical_numeric':
        section_number = extract_section_number(line)
        if section_number:
            return {
                'number': section_number,
                'title': line,
                'type': marker_type
            }
    
    # Check for specific legal document patterns
    # Pattern: "3 OBJECTIVES", "4 SCOPE", etc.
    section_match = re.match(r'^(\d+)\s+([A-Z][A-Za-z\s]+)$', line)
    if section_match:
        return {
            'number': section_match.group(1),
            'title': line,
            'type': 'section_heading'
        }
    
    # Pattern: "3.2 Specific Goals", "3.1 List of Objectives", etc.
    subsection_match = re.match(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)$', line)
    if subsection_match:
        return {
            'number': subsection_match.group(1),
            'title': f"{subsection_match.group(1)} {subsection_match.group(2).strip()}",
            'type': 'subsection_heading'
        }
    
    # Pattern: "1.1 Definitions", "2.1 Interpretation", etc.
    clause_match = re.match(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)', line)
    if clause_match:
        return {
            'number': clause_match.group(1),
            'title': f"{clause_match.group(1)} {clause_match.group(2).strip()}",
            'type': 'clause'
        }
    
    # Additional patterns for legal documents
    # Pattern: "3.2(a)", "3.2 (a)", etc.
    subsection_letter_match = re.match(r'^(\d+\.\d+)\s*\([a-zA-Z]\)', line)
    if subsection_letter_match:
        return {
            'number': subsection_letter_match.group(1),
            'title': line,
            'type': 'subsection_letter'
        }
    
    # Pattern: "3.2.1", "3.2.2", etc.
    subsection_dot_match = re.match(r'^(\d+\.\d+\.\d+)', line)
    if subsection_dot_match:
        return {
            'number': subsection_dot_match.group(1),
            'title': line,
            'type': 'subsection_dot'
        }
    
    # Pattern: "List of Objectives", "Specific Goals", etc. (standalone)
    objectives_match = re.match(r'^(List of Objectives|Specific Goals|Objectives|Goals)', line, re.IGNORECASE)
    if objectives_match:
        return {
            'number': 'objectives',  # Special identifier for objectives sections
            'title': line,
            'type': 'objectives_section'
        }
    
    return None

def split_section_into_chunks(section_content: str, section_number: str, section_title: str, section_pages: list) -> list:
    """
    Split a section into manageable chunks while preserving section context.
    """
    chunks = []
    
    # If section is small enough, keep it as one chunk
    if len(section_content) <= 2000:
        chunks.append({
            'content': section_content,
            'section_number': section_number,
            'section_title': section_title,
            'pages': section_pages
        })
        return chunks
    
    # Split section into paragraphs
    paragraphs = split_text_into_paragraphs(section_content)
    
    current_chunk = ""
    current_chunk_pages = set(section_pages)
    
    for paragraph in paragraphs:
        # Check if adding this paragraph would make the chunk too large
        if current_chunk and len(current_chunk) + len(paragraph) > 2000:
            # Save current chunk
            chunks.append({
                'content': current_chunk.strip(),
                'section_number': section_number,
                'section_title': section_title,
                'pages': list(current_chunk_pages)
            })
            
            # Start new chunk
            current_chunk = paragraph
            current_chunk_pages = set(section_pages)
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append({
            'content': current_chunk.strip(),
            'section_number': section_number,
            'section_title': section_title,
            'pages': list(current_chunk_pages)
        })
    
    return chunks

def extract_section_info_from_chunk(chunk_content: str) -> tuple:
    """
    Extract section number and title from chunk content.
    Returns (section_number, section_title)
    """
    lines = chunk_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headings
        is_list, marker_type, level = is_ordered_list_item(line)
        
        if is_list and marker_type in ['section_heading', 'subsection_heading']:
            # Extract section number
            section_number = extract_section_number(line)
            if section_number:
                return section_number, line
        
        # Check for hierarchical numeric patterns
        if is_list and marker_type == 'hierarchical_numeric':
            section_number = extract_section_number(line)
            if section_number:
                return section_number, line
        
        # Check for specific legal document patterns
        # Pattern: "3 OBJECTIVES", "4 SCOPE", etc.
        section_match = re.match(r'^(\d+)\s+([A-Z][A-Za-z\s]+)$', line)
        if section_match:
            section_number = section_match.group(1)
            section_title = line
            return section_number, section_title
        
        # Pattern: "3.2 Specific Goals", "3.1 List of Objectives", etc.
        subsection_match = re.match(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)$', line)
        if subsection_match:
            section_number = subsection_match.group(1)
            section_title = f"{section_number} {subsection_match.group(2).strip()}"
            return section_number, section_title
        
        # Pattern: "1.1 Definitions", "2.1 Interpretation", etc.
        clause_match = re.match(r'^(\d+\.\d+)\s+([A-Z][A-Za-z\s]+)', line)
        if clause_match:
            section_number = clause_match.group(1)
            section_title = f"{section_number} {clause_match.group(2).strip()}"
            return section_number, section_title
    
    # If no section found, return empty strings
    return '', ''

def detect_cross_references(text: str) -> List[str]:
    """
    Detect cross-references in legal documents.
    Returns a list of cross-reference strings found in the text.
    """
    cross_refs = []
    
    # Common cross-reference patterns in legal documents
    patterns = [
        r'see\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # see section 3.2
        r'refer\s+to\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # refer to section 3.2
        r'as\s+defined\s+in\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # as defined in section 3.2
        r'pursuant\s+to\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # pursuant to section 3.2
        r'in\s+accordance\s+with\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # in accordance with section 3.2
        r'under\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # under section 3.2
        r'per\s+(?:section|clause|article|paragraph)\s+(\d+(?:\.\d+)?)',  # per section 3.2
        r'(\d+(?:\.\d+)?)\s+above',  # 3.2 above
        r'(\d+(?:\.\d+)?)\s+below',  # 3.2 below
        r'(\d+(?:\.\d+)?)\s+herein',  # 3.2 herein
        r'(\d+(?:\.\d+)?)\s+hereof',  # 3.2 hereof
        r'(\d+(?:\.\d+)?)\s+hereafter',  # 3.2 hereafter
        r'(\d+(?:\.\d+)?)\s+herebefore',  # 3.2 herebefore
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            cross_refs.append(match.group(0))
    
    return cross_refs

def enhance_paragraph_chunking(paragraphs: List[str]) -> List[str]:
    """
    Enhanced paragraph chunking that better preserves list structure and logical flow.
    """
    enhanced_chunks = []
    current_chunk = ""
    
    for i, paragraph in enumerate(paragraphs):
        # Check if we should start a new chunk
        if current_chunk and should_start_new_chunk(current_chunk, paragraph):
            if current_chunk.strip():
                enhanced_chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk.strip():
        enhanced_chunks.append(current_chunk.strip())
    
    return enhanced_chunks

def should_start_new_chunk(current_chunk: str, next_paragraph: str) -> bool:
    """
    Determine if a new chunk should be started based on content analysis.
    """
    # Check if next paragraph is a major section header
    is_list, marker_type, level = is_ordered_list_item(next_paragraph)
    
    if is_list and marker_type in ['section_heading', 'subsection_heading']:
        # Check if current chunk already has a section header
        lines = current_chunk.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                line_is_list, line_marker_type, _ = is_ordered_list_item(line)
                if line_is_list and line_marker_type in ['section_heading', 'subsection_heading']:
                    return True
    
    # Check for major topic changes
    if is_major_topic_change(current_chunk, next_paragraph):
        return True
    
    # Check length constraints
    combined_length = len(current_chunk) + len(next_paragraph)
    if combined_length > 1500:  # Optimal chunk size for RAG
        return True
    
    return False

def is_major_topic_change(current_chunk: str, next_paragraph: str) -> bool:
    """
    Detect if there's a major topic change between chunks.
    """
    # Check for document structure indicators
    structure_indicators = [
        'SCHEDULE', 'EXHIBIT', 'APPENDIX', 'ATTACHMENT', 'ENCLOSURE',
        'DEFINITIONS', 'INTERPRETATION', 'GENERAL', 'SPECIFIC',
        'TERMINATION', 'AMENDMENT', 'ASSIGNMENT', 'GOVERNING LAW'
    ]
    
    next_upper = next_paragraph.upper()
    for indicator in structure_indicators:
        if indicator in next_upper:
            return True
    
    # Check for significant formatting changes
    current_lines = current_chunk.split('\n')
    if current_lines:
        last_line = current_lines[-1].strip()
        if last_line and next_paragraph.strip():
            # Check if there's a significant change in formatting
            last_is_list, last_marker_type, _ = is_ordered_list_item(last_line)
            next_is_list, next_marker_type, _ = is_ordered_list_item(next_paragraph)
            
            # If one is a list and the other isn't, it might be a topic change
            if last_is_list != next_is_list:
                return True
            
            # If both are lists but different types, it might be a topic change
            if last_is_list and next_is_list and last_marker_type != next_marker_type:
                # But don't break for hierarchical relationships
                if not is_mixed_hierarchical_related(last_line, next_paragraph):
                    return True
    
    return False

def validate_chunk_quality(chunk: str) -> bool:
    """
    Validate that a chunk meets quality standards for RAG.
    """
    if not chunk or len(chunk.strip()) < 50:
        return False
    
    # Check if chunk is mostly footer content
    lines = chunk.split('\n')
    footer_lines = 0
    total_lines = 0
    
    for line in lines:
        line = line.strip()
        if line:
            total_lines += 1
            if is_footer_content(line):
                footer_lines += 1
    
    # If more than 50% is footer content, reject the chunk
    if total_lines > 0 and footer_lines / total_lines > 0.5:
        return False
    
    # Check for meaningful content (not just numbers or symbols)
    meaningful_chars = sum(1 for c in chunk if c.isalpha())
    if meaningful_chars < 20:  # At least 20 alphabetic characters
        return False
    
    return True

def handle_edge_cases_and_cleanup(chunks: List[dict]) -> List[dict]:
    """
    Handle edge cases and cleanup chunks for better RAG performance.
    """
    cleaned_chunks = []
    
    for chunk in chunks:
        # Validate chunk quality
        if not validate_chunk_quality(chunk['content']):
            continue
        
        # Clean up content
        cleaned_content = cleanup_chunk_content(chunk['content'])
        if not cleaned_content:
            continue
        
        # Detect cross-references
        cross_refs = detect_cross_references(cleaned_content)
        
        # Update chunk with cleaned content and cross-references
        chunk['content'] = cleaned_content
        chunk['cross_references'] = cross_refs
        
        cleaned_chunks.append(chunk)
    
    return cleaned_chunks

def cleanup_chunk_content(content: str) -> str:
    """
    Clean up chunk content for better readability and processing.
    """
    if not content:
        return ""
    
    # Remove excessive whitespace
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Remove excessive internal whitespace
            line = re.sub(r'\s+', ' ', line)
            cleaned_lines.append(line)
    
    # Rejoin with proper spacing
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Remove excessive newlines
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
    
    return cleaned_content.strip()

def optimize_chunk_sizes(chunks: List[dict]) -> List[dict]:
    """
    Optimize chunk sizes for better RAG performance.
    """
    optimized_chunks = []
    
    for chunk in chunks:
        content = chunk['content']
        
        # If chunk is too large, split it further
        if len(content) > 2000:
            sub_chunks = split_large_chunk(content, chunk)
            optimized_chunks.extend(sub_chunks)
        else:
            optimized_chunks.append(chunk)
    
    return optimized_chunks

def split_large_chunk(content: str, original_chunk: dict) -> List[dict]:
    """
    Split a large chunk into smaller, more manageable pieces.
    """
    sub_chunks = []
    
    # Split by paragraphs first
    paragraphs = split_text_into_paragraphs(content)
    
    current_sub_chunk = ""
    chunk_id_suffix = 0
    
    for paragraph in paragraphs:
        # Check if adding this paragraph would make the chunk too large
        if current_sub_chunk and len(current_sub_chunk) + len(paragraph) > 1500:
            # Save current sub-chunk
            if current_sub_chunk.strip():
                sub_chunk = original_chunk.copy()
                sub_chunk['content'] = current_sub_chunk.strip()
                sub_chunk['chunk_id'] = f"{original_chunk['chunk_id']}_sub_{chunk_id_suffix}"
                sub_chunks.append(sub_chunk)
                chunk_id_suffix += 1
            
            # Start new sub-chunk
            current_sub_chunk = paragraph
        else:
            # Add to current sub-chunk
            if current_sub_chunk:
                current_sub_chunk += "\n\n" + paragraph
            else:
                current_sub_chunk = paragraph
    
    # Add the last sub-chunk
    if current_sub_chunk.strip():
        sub_chunk = original_chunk.copy()
        sub_chunk['content'] = current_sub_chunk.strip()
        sub_chunk['chunk_id'] = f"{original_chunk['chunk_id']}_sub_{chunk_id_suffix}"
        sub_chunks.append(sub_chunk)
    
    return sub_chunks

def generate_chunking_summary(chunks: List[dict]) -> dict:
    """
    Generate a comprehensive summary of the chunking results.
    """
    if not chunks:
        return {
            'total_chunks': 0,
            'total_characters': 0,
            'average_chunk_size': 0,
            'sections_found': 0,
            'chunks_with_sections': 0,
            'chunks_with_cross_references': 0,
            'section_distribution': {},
            'size_distribution': {}
        }
    
    total_chunks = len(chunks)
    total_characters = sum(len(chunk['content']) for chunk in chunks)
    average_chunk_size = total_characters / total_chunks if total_chunks > 0 else 0
    
    sections_found = set()
    chunks_with_sections = 0
    chunks_with_cross_references = 0
    section_distribution = {}
    size_distribution = {'small': 0, 'medium': 0, 'large': 0}
    
    for chunk in chunks:
        # Count sections
        section_number = chunk.get('section_number', '')
        if section_number:
            sections_found.add(section_number)
            chunks_with_sections += 1
            section_distribution[section_number] = section_distribution.get(section_number, 0) + 1
        
        # Count cross-references
        cross_refs = chunk.get('cross_references', [])
        if cross_refs:
            chunks_with_cross_references += 1
        
        # Size distribution
        content_length = len(chunk['content'])
        if content_length < 500:
            size_distribution['small'] += 1
        elif content_length < 1500:
            size_distribution['medium'] += 1
        else:
            size_distribution['large'] += 1
    
    return {
        'total_chunks': total_chunks,
        'total_characters': total_characters,
        'average_chunk_size': round(average_chunk_size, 2),
        'sections_found': len(sections_found),
        'chunks_with_sections': chunks_with_sections,
        'chunks_with_cross_references': chunks_with_cross_references,
        'section_distribution': section_distribution,
        'size_distribution': size_distribution
    }

def process_legal_pdf_nemo(pdf_path: str) -> dict:
    """
    Process a legal PDF using PyMuPDF for extraction and chunking.
    Returns a dict with keys: total_chunks, extraction_method, chunks (list of dicts)
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # First pass: Extract all text and identify sections across pages
        all_text = ""
        page_sections = []  # Track sections and their page ranges
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                all_text += text + "\n\n"
        
        # Identify sections across the entire document
        sections = identify_document_sections(all_text)
        
        # Second pass: Create chunks based on sections, not pages
        formatted_chunks = []
        chunk_id = 0
        
        for section in sections:
            section_content = section['content']
            section_number = section['section_number']
            section_title = section['section_title']
            section_pages = section['pages']
            
            # Split section content into manageable chunks
            section_chunks = split_section_into_chunks(section_content, section_number, section_title, section_pages)
            
            for chunk in section_chunks:
                formatted_chunks.append({
                    'chunk_id': f"pymupdf_{os.path.basename(pdf_path)}_{chunk_id}",
                    'content': chunk['content'],
                    'chunk_type': 'pymupdf',
                    'section_number': chunk['section_number'],
                    'section_title': chunk['section_title'],
                    'pages': chunk['pages'],
                    'cross_references': []
                })
                chunk_id += 1
        
        doc.close()
        
        # Handle edge cases and cleanup
        chunks_after_cleanup = handle_edge_cases_and_cleanup(formatted_chunks)
        
        # Optimize chunk sizes
        final_chunks = optimize_chunk_sizes(chunks_after_cleanup)
        
        # Generate summary
        summary = generate_chunking_summary(final_chunks)
        
        return {
            'total_chunks': len(final_chunks),
            'extraction_method': 'pymupdf_enhanced',
            'chunks': final_chunks,
            'summary': summary
        }
        
    except Exception as e:
        logging.error(f"Error processing PDF with PyMuPDF: {e}")
        raise e