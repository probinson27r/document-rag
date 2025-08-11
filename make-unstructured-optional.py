#!/usr/bin/env python3
"""
Make unstructured imports optional in document_rag.py
This prevents import errors when unstructured packages have dependency conflicts
"""

import re

def make_unstructured_optional():
    """Modify document_rag.py to make unstructured imports optional"""
    
    file_path = "document_rag.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add try/except around unstructured imports at the top
    unstructured_import_pattern = r'(# Donut dependencies.*?)(\ntry:.*?except ImportError:.*?DONUT_AVAILABLE = False)'
    
    if 'unstructured' not in content or 'UNSTRUCTURED_AVAILABLE' in content:
        print("✅ Unstructured imports already optional or not found")
        return
    
    # Add unstructured availability check
    unstructured_check = '''
# Unstructured dependencies (optional)
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
'''
    
    # Find the right place to insert - after the Donut imports
    donut_section = re.search(r'(# Donut dependencies.*?except ImportError:\s+DONUT_AVAILABLE = False)', content, re.DOTALL)
    if donut_section:
        insertion_point = donut_section.end()
        content = content[:insertion_point] + unstructured_check + content[insertion_point:]
    else:
        # If no Donut section found, add after imports
        import_end = content.find('import traceback')
        if import_end != -1:
            insertion_point = content.find('\n', import_end) + 1
            content = content[:insertion_point] + unstructured_check + content[insertion_point:]
    
    # Replace the inline unstructured import with a conditional check
    old_pattern = r'            try:\s+from unstructured\.partition\.pdf import partition_pdf'
    new_pattern = '''            try:
                if not UNSTRUCTURED_AVAILABLE:
                    print("[unstructured] Unstructured library not available, skipping...")
                    raise ImportError("unstructured not available")
                from unstructured.partition.pdf import partition_pdf'''
    
    content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
    
    # Write the modified content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Modified document_rag.py to make unstructured imports optional")
    print("📝 Now unstructured errors will be gracefully handled")

if __name__ == "__main__":
    make_unstructured_optional()
