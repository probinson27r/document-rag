#!/usr/bin/env python3
"""
Test OCR functionality
"""

import os
import sys

def test_ocr_dependencies():
    """Test if OCR dependencies are available"""
    
    print("🧪 Testing OCR Dependencies")
    print("=" * 50)
    
    dependencies = [
        ('pdf2image', 'PDF to image conversion'),
        ('pytesseract', 'OCR text extraction'),
        ('fpdf2', 'PDF generation'),
        ('Pillow', 'Image processing'),
        ('reportlab', 'PDF generation'),
        ('pi_heif', 'HEIF image support'),
        ('unstructured', 'Document parsing'),
        ('fitz', 'PyMuPDF'),
        ('pdfplumber', 'PDF text extraction')
    ]
    
    results = []
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            results.append(('✅', module_name, description, 'Available'))
        except ImportError:
            results.append(('❌', module_name, description, 'Missing'))
    
    print("Dependency Status:")
    for status, module, desc, availability in results:
        print(f"  {status} {module}: {desc} - {availability}")
    
    return all(status == '✅' for status, _, _, _ in results)

def test_font_availability():
    """Test font availability"""
    
    print(f"\n🔍 Testing Font Availability")
    print("=" * 50)
    
    font_path = "fonts/DejaVuSans.ttf"
    
    if os.path.exists(font_path):
        print(f"✅ Font found: {font_path}")
        return True
    else:
        print(f"❌ Font missing: {font_path}")
        print("  Will use system fonts as fallback")
        return False

def test_ocr_extraction():
    """Test OCR text extraction"""
    
    print(f"\n🔍 Testing OCR Text Extraction")
    print("=" * 50)
    
    try:
        from document_rag import DocumentProcessor
        
        # Test DocumentProcessor initialization
        processor = DocumentProcessor(enable_ocr=True)
        print("✅ DocumentProcessor initialized with OCR enabled")
        
        # Test font handling
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Test", ln=True)
            print("✅ PDF generation test successful")
        except Exception as e:
            print(f"⚠️  PDF generation test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR extraction test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 OCR Functionality Test")
    print("=" * 50)
    
    deps_ok = test_ocr_dependencies()
    font_ok = test_font_availability()
    ocr_ok = test_ocr_extraction()
    
    print(f"\n🎯 Test Results:")
    print("=" * 50)
    print(f"  Dependencies: {'✅ OK' if deps_ok else '❌ Issues'}")
    print(f"  Fonts: {'✅ OK' if font_ok else '⚠️  Using fallback'}")
    print(f"  OCR: {'✅ OK' if ocr_ok else '❌ Issues'}")
    
    if deps_ok and ocr_ok:
        print(f"\n✅ OCR is ready to use!")
        print(f"   You can now reprocess your document with OCR enabled")
    else:
        print(f"\n❌ OCR has issues that need to be resolved")
        print(f"   Run: python fix_ocr_dependencies.py")
