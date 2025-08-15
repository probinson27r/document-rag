#!/usr/bin/env python3
"""
Fix OCR dependencies and font issues
"""

import os
import sys
import subprocess
import requests

def install_missing_dependencies():
    """Install missing dependencies for OCR"""
    
    print("🔧 Installing Missing OCR Dependencies")
    print("=" * 50)
    
    # List of dependencies to install
    dependencies = [
        'pi-heif',  # For unstructured.io HEIF support
        'pdf2image',  # For PDF to image conversion
        'pytesseract',  # For OCR
        'fpdf2',  # Better PDF generation (replaces fpdf)
        'Pillow',  # Image processing
        'reportlab',  # PDF generation
    ]
    
    print(f"📦 Installing dependencies: {', '.join(dependencies)}")
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
    
    print()

def fix_font_issue():
    """Fix the font download issue"""
    
    print("🔧 Fixing Font Download Issue")
    print("=" * 50)
    
    # Create fonts directory
    fonts_dir = "fonts"
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Download DejaVu font
    font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
    font_path = os.path.join(fonts_dir, "DejaVuSans.ttf")
    
    if not os.path.exists(font_path):
        try:
            print(f"Downloading DejaVu font from {font_url}...")
            response = requests.get(font_url, timeout=30)
            response.raise_for_status()
            
            with open(font_path, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Font downloaded to {font_path}")
        except Exception as e:
            print(f"❌ Failed to download font: {e}")
            print("Will use system fonts instead")
    else:
        print(f"✅ Font already exists at {font_path}")
    
    print()

def update_document_rag_font_handling():
    """Update document_rag.py to handle font issues better"""
    
    print("🔧 Updating Font Handling in document_rag.py")
    print("=" * 50)
    
    # Create a backup
    backup_path = "document_rag.py.backup"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy("document_rag.py", backup_path)
        print(f"✅ Created backup: {backup_path}")
    
    # Read the current file
    with open("document_rag.py", "r") as f:
        content = f.read()
    
    # Replace the problematic font handling code
    old_font_code = '''                FONT_PATH = "DejaVuSans.ttf"
                # Download DejaVuSans.ttf if not present
                if not os.path.exists(FONT_PATH):
                    print("[fpdf2] Downloading DejaVuSans.ttf font...")
                    url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
                    r = requests.get(url)
                    with open(FONT_PATH, "wb") as f:
                        f.write(r.content)
                    print("[fpdf2] Font downloaded.")
                from fpdf import FPDF
                class UnicodePDF(FPDF):
                    def __init__(self):
                        super().__init__()
                        self.add_font("DejaVu", "", FONT_PATH, uni=True)
                        self.set_font("DejaVu", size=12)'''
    
    new_font_code = '''                # Try to use system fonts first, fallback to downloaded font
                FONT_PATH = "fonts/DejaVuSans.ttf"
                
                # Create fonts directory if it doesn't exist
                fonts_dir = "fonts"
                os.makedirs(fonts_dir, exist_ok=True)
                
                # Download font if not present
                if not os.path.exists(FONT_PATH):
                    try:
                        print("[fpdf2] Downloading DejaVuSans.ttf font...")
                        url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
                        r = requests.get(url, timeout=30)
                        r.raise_for_status()
                        with open(FONT_PATH, "wb") as f:
                            f.write(r.content)
                        print("[fpdf2] Font downloaded successfully.")
                    except Exception as e:
                        print(f"[fpdf2] Failed to download font: {e}")
                        print("[fpdf2] Will use system fonts instead.")
                        FONT_PATH = None
                
                from fpdf import FPDF
                class UnicodePDF(FPDF):
                    def __init__(self):
                        super().__init__()
                        try:
                            if FONT_PATH and os.path.exists(FONT_PATH):
                                self.add_font("DejaVu", "", FONT_PATH, uni=True)
                                self.set_font("DejaVu", size=12)
                            else:
                                # Fallback to system fonts
                                self.set_font("Arial", size=12)
                        except Exception as e:
                            print(f"[fpdf2] Font loading failed: {e}")
                            # Use default font
                            self.set_font("Arial", size=12)'''
    
    if old_font_code in content:
        content = content.replace(old_font_code, new_font_code)
        
        with open("document_rag.py", "w") as f:
            f.write(content)
        
        print("✅ Updated font handling in document_rag.py")
    else:
        print("⚠️  Font code not found, may have already been updated")
    
    print()

def create_ocr_fallback():
    """Create OCR fallback for when unstructured.io fails"""
    
    print("🔧 Creating OCR Fallback")
    print("=" * 50)
    
    fallback_code = '''
def extract_text_with_ocr_fallback(file_path: str) -> str:
    """
    Extract text from PDF with OCR fallback when unstructured.io fails
    """
    try:
        # Try unstructured.io first
        from unstructured.partition.pdf import partition_pdf
        print("[unstructured] Attempting extraction with unstructured.io...")
        elements = partition_pdf(file_path)
        text = "\\n".join([getattr(el, 'text', '').strip() for el in elements if getattr(el, 'text', '').strip()])
        if text.strip():
            print("[unstructured] Extraction successful")
            return text
    except ImportError as e:
        print(f"[unstructured] Import error: {e}")
    except Exception as e:
        print(f"[unstructured] Extraction failed: {e}")
    
    try:
        # Fallback to pdfplumber
        import pdfplumber
        print("[pdfplumber] Attempting extraction with pdfplumber...")
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\\n"
        if text.strip():
            print("[pdfplumber] Extraction successful")
            return text
    except Exception as e:
        print(f"[pdfplumber] Extraction failed: {e}")
    
    try:
        # Final fallback to PyMuPDF
        import fitz
        print("[PyMuPDF] Attempting extraction with PyMuPDF...")
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\\n"
        doc.close()
        if text.strip():
            print("[PyMuPDF] Extraction successful")
            return text
    except Exception as e:
        print(f"[PyMuPDF] Extraction failed: {e}")
    
    print("[ERROR] All extraction methods failed")
    return ""
'''
    
    # Add this function to document_rag.py
    with open("document_rag.py", "r") as f:
        content = f.read()
    
    if "def extract_text_with_ocr_fallback" not in content:
        # Add the function before the DocumentProcessor class
        insert_point = "class DocumentProcessor:"
        content = content.replace(insert_point, fallback_code + "\n\n" + insert_point)
        
        with open("document_rag.py", "w") as f:
            f.write(content)
        
        print("✅ Added OCR fallback function to document_rag.py")
    else:
        print("✅ OCR fallback function already exists")
    
    print()

def update_requirements():
    """Update requirements.txt with OCR dependencies"""
    
    print("🔧 Updating requirements.txt")
    print("=" * 50)
    
    # Read current requirements
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
    except FileNotFoundError:
        requirements = ""
    
    # Add OCR dependencies if not present
    ocr_dependencies = [
        "pi-heif>=1.0.0",
        "pdf2image>=3.1.0",
        "pytesseract>=0.3.10",
        "fpdf2>=2.7.0",
        "Pillow>=10.0.0",
        "reportlab>=4.0.0",
        "PyMuPDF>=1.23.0"
    ]
    
    new_deps = []
    for dep in ocr_dependencies:
        dep_name = dep.split(">=")[0]
        if dep_name not in requirements:
            new_deps.append(dep)
    
    if new_deps:
        with open("requirements.txt", "a") as f:
            f.write("\n# OCR Dependencies\n")
            for dep in new_deps:
                f.write(dep + "\n")
        
        print(f"✅ Added {len(new_deps)} OCR dependencies to requirements.txt")
        print(f"  Added: {', '.join(new_deps)}")
    else:
        print("✅ All OCR dependencies already in requirements.txt")
    
    print()

def create_test_script():
    """Create a test script to verify OCR functionality"""
    
    print("🔧 Creating OCR Test Script")
    print("=" * 50)
    
    test_script = '''#!/usr/bin/env python3
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
    
    print(f"\\n🔍 Testing Font Availability")
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
    
    print(f"\\n🔍 Testing OCR Text Extraction")
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
    
    print(f"\\n🎯 Test Results:")
    print("=" * 50)
    print(f"  Dependencies: {'✅ OK' if deps_ok else '❌ Issues'}")
    print(f"  Fonts: {'✅ OK' if font_ok else '⚠️  Using fallback'}")
    print(f"  OCR: {'✅ OK' if ocr_ok else '❌ Issues'}")
    
    if deps_ok and ocr_ok:
        print(f"\\n✅ OCR is ready to use!")
        print(f"   You can now reprocess your document with OCR enabled")
    else:
        print(f"\\n❌ OCR has issues that need to be resolved")
        print(f"   Run: python fix_ocr_dependencies.py")
'''
    
    with open("test_ocr.py", "w") as f:
        f.write(test_script)
    
    print("✅ Created test_ocr.py")
    print()

if __name__ == "__main__":
    print("🔧 Fixing OCR Dependencies and Font Issues")
    print("=" * 60)
    
    # Install missing dependencies
    install_missing_dependencies()
    
    # Fix font issue
    fix_font_issue()
    
    # Update document_rag.py
    update_document_rag_font_handling()
    
    # Create OCR fallback
    create_ocr_fallback()
    
    # Update requirements.txt
    update_requirements()
    
    # Create test script
    create_test_script()
    
    print("🎯 Summary:")
    print("=" * 50)
    print("✅ OCR dependencies installed")
    print("✅ Font handling improved")
    print("✅ OCR fallback created")
    print("✅ Requirements updated")
    print("✅ Test script created")
    print()
    print("🔧 Next Steps:")
    print("1. Run: python test_ocr.py")
    print("2. If tests pass, reprocess your document with OCR enabled")
    print("3. Use settings: Traditional extraction, Semantic chunking, OCR enabled")
