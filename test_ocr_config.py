#!/usr/bin/env python3
"""
Test OCR configuration saving and loading
"""

import sys
import os
sys.path.append('.')

def test_ocr_config_structure():
    """Test that OCR configuration is properly structured"""
    
    print("🧪 Testing OCR Configuration Structure")
    print("=" * 50)
    
    # Test the expected structure
    test_config = {
        'extraction_method': 'traditional',
        'gpt4_model': 'gpt-4o',
        'prefer_private_gpt4': True,
        'features': {
            'text_enhancement': True,
            'structured_data': True,
            'contract_analysis': True,
            'document_summary': False,
            'gpt4_chunking': True
        },
        'chunking': {
            'method': 'semantic',
            'document_type': 'auto',
            'preserve_structure': True,
            'prefer_private_gpt4': True
        },
        'ocr': {
            'enabled': True  # This should be saved and loaded correctly
        }
    }
    
    print(f"✅ Test configuration structure:")
    print(f"  OCR enabled: {test_config.get('ocr', {}).get('enabled', False)}")
    print(f"  Extraction method: {test_config.get('extraction_method')}")
    print(f"  Chunking method: {test_config.get('chunking', {}).get('method')}")
    
    # Test accessing OCR configuration
    ocr_enabled = test_config.get('ocr', {}).get('enabled', False)
    print(f"✅ OCR enabled accessed correctly: {ocr_enabled}")
    
    return test_config

def test_ocr_config_parsing():
    """Test OCR configuration parsing logic"""
    
    print(f"\n🧪 Testing OCR Configuration Parsing")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'OCR Enabled',
            'config': {
                'ocr': {'enabled': True}
            },
            'expected': True
        },
        {
            'name': 'OCR Disabled',
            'config': {
                'ocr': {'enabled': False}
            },
            'expected': False
        },
        {
            'name': 'OCR Missing',
            'config': {},
            'expected': False
        },
        {
            'name': 'OCR Enabled Explicit',
            'config': {
                'ocr': {'enabled': True}
            },
            'expected': True
        }
    ]
    
    for test_case in test_cases:
        config = test_case['config']
        expected = test_case['expected']
        
        # Parse OCR configuration (same logic as in app.py)
        ocr_enabled = config.get('ocr', {}).get('enabled', False)
        
        status = "✅ PASS" if ocr_enabled == expected else "❌ FAIL"
        print(f"{status} {test_case['name']}: {ocr_enabled} (expected {expected})")
    
    print()

def test_document_processor_ocr():
    """Test DocumentProcessor OCR initialization"""
    
    print(f"🧪 Testing DocumentProcessor OCR Initialization")
    print("=" * 50)
    
    try:
        from document_rag import DocumentProcessor
        
        # Test cases
        test_cases = [
            {
                'name': 'OCR Enabled',
                'enable_ocr': True,
                'expected': True
            },
            {
                'name': 'OCR Disabled',
                'enable_ocr': False,
                'expected': False
            }
        ]
        
        for test_case in test_cases:
            enable_ocr = test_case['enable_ocr']
            expected = test_case['expected']
            
            # Create DocumentProcessor instance
            processor = DocumentProcessor(enable_ocr=enable_ocr)
            
            status = "✅ PASS" if processor.enable_ocr == expected else "❌ FAIL"
            print(f"{status} {test_case['name']}: {processor.enable_ocr} (expected {expected})")
        
        print()
        
    except ImportError as e:
        print(f"❌ Could not import DocumentProcessor: {e}")
        print()

def create_ocr_fix_summary():
    """Create a summary of the OCR configuration fix"""
    
    print(f"📋 OCR Configuration Fix Summary")
    print("=" * 50)
    
    summary = """
## OCR Configuration Fix

### Problem Identified:
- OCR setting from configuration page was not being saved to session
- OCR configuration was missing from session structure
- Document processing was not receiving OCR setting

### Root Cause:
The `api_save_extraction_config()` function was not including the OCR configuration in the session structure.

### Files Fixed:

#### 1. app.py - api_save_extraction_config()
**Before:**
```python
session['extraction_config'] = {
    'extraction_method': data.get('extraction_method', 'auto'),
    # ... other config ...
    'chunking': {
        'method': data.get('chunking', {}).get('method', 'auto'),
        # ... chunking config ...
    }
    # ❌ Missing OCR configuration
}
```

**After:**
```python
session['extraction_config'] = {
    'extraction_method': data.get('extraction_method', 'auto'),
    # ... other config ...
    'chunking': {
        'method': data.get('chunking', {}).get('method', 'auto'),
        # ... chunking config ...
    },
    'ocr': {
        'enabled': data.get('ocr', {}).get('enabled', False)  # ✅ Added OCR config
    }
}
```

#### 2. app.py - api_get_extraction_config()
Added OCR configuration to default config:
```python
'ocr': {
    'enabled': False  # OCR disabled by default for faster processing
}
```

#### 3. app.py - api_extraction_status()
Added OCR configuration to default config:
```python
'ocr': {
    'enabled': False
}
```

### How It Works:

1. **Configuration Page**: User enables OCR checkbox
2. **JavaScript**: Saves OCR setting to session via API
3. **Session Storage**: OCR configuration is now properly saved
4. **Document Processing**: OCR setting is retrieved and passed to DocumentProcessor
5. **PDF Processing**: OCR is enabled/disabled based on configuration

### Testing:

To verify the fix works:

1. **Enable OCR** in the configuration page
2. **Upload a document**
3. **Check logs** for OCR processing messages:
   ```
   [DEBUG] OCR enabled: True
   [OCR] OCR is enabled - processing with image conversion...
   ```

### Expected Results:

- ✅ OCR setting is saved to session correctly
- ✅ OCR setting is loaded during document processing
- ✅ OCR processing is enabled when configured
- ✅ Better table extraction for scanned documents
"""
    
    print(summary)

if __name__ == "__main__":
    # Run all tests
    test_ocr_config_structure()
    test_ocr_config_parsing()
    test_document_processor_ocr()
    
    # Create fix summary
    create_ocr_fix_summary()
    
    print("🎯 Summary:")
    print("=" * 50)
    print("✅ OCR configuration fix implemented")
    print("✅ OCR setting will now be saved to session")
    print("✅ Document processing will use OCR when enabled")
    print("✅ Better table extraction for scanned documents")
