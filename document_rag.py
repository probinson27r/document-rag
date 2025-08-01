import os
import json
import requests
from typing import List, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime

# Document processing
import PyPDF2
import docx
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import pdfplumber
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

# GPT-4 extraction
try:
    from gpt4_extraction import GPT4Extractor
    GPT4_EXTRACTION_AVAILABLE = True
except ImportError:
    GPT4_EXTRACTION_AVAILABLE = False

# GPT-4 chunking
try:
    from gpt4_chunking import GPT4Chunker
    GPT4_CHUNKING_AVAILABLE = True
except ImportError:
    GPT4_CHUNKING_AVAILABLE = False

# Donut dependencies
try:
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    from pdf2image import convert_from_path
    from PIL import Image
    DONUT_AVAILABLE = True
except ImportError:
    DONUT_AVAILABLE = False

try:
    from llama_index.readers.file import PDFReader
    LLAMA_INDEX_AVAILABLE = True
    print("LLAMA_INDEX_AVAILABLE:TRUE")
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    print("LLAMA_INDEX_AVAILABLE:FALSE")

import traceback

class DocumentProcessor:
    """Handles document ingestion and text extraction"""
    
    def __init__(self, use_gpt4_enhancement: bool = True, use_gpt4_chunking: bool = True):
        self.supported_formats = ['.pdf', '.docx', '.txt', '.csv', '.json']
        self.use_gpt4_enhancement = use_gpt4_enhancement and GPT4_EXTRACTION_AVAILABLE
        self.use_gpt4_chunking = use_gpt4_chunking and GPT4_CHUNKING_AVAILABLE
        
        # Initialize GPT-4 extractor if available
        self.gpt4_extractor = None
        if self.use_gpt4_enhancement:
            try:
                self.gpt4_extractor = GPT4Extractor(
                    openai_api_key=os.getenv('OPENAI_API_KEY'),
                    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
                    private_gpt4_url=os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'),
                    private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
                )
                print("[GPT-4] GPT-4 extraction enabled")
            except Exception as e:
                print(f"[GPT-4] Failed to initialize GPT-4 extractor: {e}")
                self.use_gpt4_enhancement = False
        
        # Initialize GPT-4 chunker if available
        self.gpt4_chunker = None
        if self.use_gpt4_chunking:
            try:
                self.gpt4_chunker = GPT4Chunker(
                    openai_api_key=os.getenv('OPENAI_API_KEY'),
                    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
                    private_gpt4_url=os.getenv('PRIVATE_GPT4_URL', 'https://doe-srt-sensai-nprd-apim.azure-api.net/doe-srt-sensai-nprd-oai/openai/deployments/gpt-4o/chat/completions?api-version=2025-03-01-preview'),
                    private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
                )
                print("[GPT-4] GPT-4 chunking enabled")
            except Exception as e:
                print(f"[GPT-4] Failed to initialize GPT-4 chunker: {e}")
                self.use_gpt4_chunking = False
    
    def join_headings_with_content(self, text: str) -> str:
        """Join headings (short, title-like lines) with their following content."""
        lines = text.splitlines()
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Heuristic: heading if short, not ending with a period, and title-like
            is_heading = (
                0 < len(line) < 80 and
                not line.endswith('.') and
                (line.isupper() or line.istitle()) and
                not re.match(r'^\d+(\.|\))', line)  # not just a numbered list
            )
            if is_heading and i + 1 < len(lines):
                # Join with next non-empty line(s)
                content = line
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                if j < len(lines):
                    content += ' ' + lines[j].strip()
                    new_lines.append(content)
                    i = j + 1
                    continue
            new_lines.append(line)
            i += 1
        return '\n'.join(new_lines)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF by running OCR first, then marker-pdf, then unstructured.io (skipping ToC), then pdfplumber, then PyPDF2. Preserves structure and annotates headings."""
        import sys, traceback, re, os
        print(f"[DEBUG] extract_text_from_pdf called with: {file_path}")
        sys.stdout.flush()
        text = ""
        ocr_temp_pdf = None
        # Step 1: OCR (Tesseract via pdf2image)
        try:
            from pdf2image import convert_from_path
            import pytesseract
            from fpdf import FPDF
            import requests
            FONT_PATH = "DejaVuSans.ttf"
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
                    self.set_font("DejaVu", size=12)
            print("[OCR] Converting PDF pages to images...")
            images = convert_from_path(file_path)
            print(f"[OCR] {len(images)} pages converted. Running OCR...")
            ocr_texts = [pytesseract.image_to_string(img) for img in images]
            print("[OCR] OCR extraction complete. Rebuilding PDF from OCR text with Unicode support...")
            ocr_temp_pdf = file_path + ".ocr.pdf"
            pdf = UnicodePDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            for page_text in ocr_texts:
                pdf.add_page()
                for line in page_text.splitlines():
                    pdf.cell(0, 10, txt=line, ln=1)
            pdf.output(ocr_temp_pdf)
            print(f"[OCR] OCR-based PDF created: {ocr_temp_pdf}")
            sys.stdout.flush()
        except Exception as e:
            print(f"[OCR] Extraction failed: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            ocr_temp_pdf = None
        # Step 2: marker-pdf on OCR-based PDF
        if ocr_temp_pdf and os.path.exists(ocr_temp_pdf):
            try:
                from marker.pdf import parse_pdf
                print("[marker-pdf] Parsing OCR-based PDF...")
                doc = parse_pdf(ocr_temp_pdf)
                lines = []
                for block in doc:
                    if block['type'] == 'heading':
                        lines.append(f"## {block['text']}")
                    elif block['type'] == 'list-item':
                        indent = '    ' * (block.get('level', 1))
                        lines.append(f"{indent}{block['text']}")
                    elif block['type'] == 'table':
                        lines.append(f"[TABLE]\n{block['text']}\n[/TABLE]")
                    else:
                        lines.append(block['text'])
                text = '\n'.join(lines)
                print("[marker-pdf] Extraction complete.")
                sys.stdout.flush()
            except Exception as e:
                print(f"[marker-pdf] Extraction failed: {e}")
                traceback.print_exc()
                sys.stdout.flush()
            finally:
                try:
                    os.remove(ocr_temp_pdf)
                except Exception:
                    pass
        # Step 3: unstructured.io, skipping Table of Contents
        if not text.strip():
            try:
                from unstructured.partition.pdf import partition_pdf
                print("[unstructured] Partitioning PDF...")
                elements = partition_pdf(file_path)
                lines = []
                skipping_toc = False
                for el in elements:
                    cat = getattr(el, 'category', None)
                    el_text = getattr(el, 'text', '').strip()
                    if not el_text:
                        continue
                    # Start skipping if we hit a ToC heading
                    if not skipping_toc and re.match(r"^(table of contents|contents)$", el_text, re.IGNORECASE):
                        skipping_toc = True
                        continue
                    # Stop skipping when we hit the next major heading (heuristic: SectionHeader or Title after ToC)
                    if skipping_toc and cat in ('Title', 'SectionHeader') and not re.match(r"^(table of contents|contents)$", el_text, re.IGNORECASE):
                        skipping_toc = False
                    if skipping_toc:
                        continue
                    if cat in ('Title', 'SectionHeader', 'Header', 'Footer'):
                        lines.append(f"## {el_text}")
                    elif cat == 'ListItem':
                        level = getattr(el, 'metadata', {}).get('text_as_html', '').count('<li>')
                        indent = '    ' * (level if level else 1)
                        lines.append(f"{indent}{el_text}")
                    elif cat == 'Table':
                        lines.append(f"[TABLE]\n{el_text}\n[/TABLE]")
                    else:
                        lines.append(el_text)
                text = '\n'.join(lines)
                print("[unstructured] Extraction complete.")
                sys.stdout.flush()
            except Exception as e:
                print(f"[unstructured] Extraction failed: {e}")
                traceback.print_exc()
                sys.stdout.flush()
        # Step 4: pdfplumber with layout/heading
        if not text.strip():
            try:
                import pdfplumber
                lines = []
                heading_min_size = 14
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        if hasattr(page, 'extract_words') and hasattr(page, 'extract_text_lines'):
                            word_info = {}
                            for word in page.extract_words(extra_attrs=["size", "fontname"]):
                                key = (round(word['x0']), round(word['top']))
                                word_info[key] = (float(word['size']), word['fontname'], word['text'])
                            for line in page.extract_text_lines():
                                x0 = line.get('x0', 0)
                                top = round(line.get('top', 0))
                                raw = line.get('text', '')
                                indent = int(max(0, (x0 - 30) // 10))
                                is_heading = False
                                for word in raw.split():
                                    for (wx0, wtop), (size, font, wtext) in word_info.items():
                                        if wtext == word and abs(wx0 - round(x0)) < 5 and abs(wtop - top) < 5:
                                            if size >= heading_min_size or 'Bold' in font:
                                                is_heading = True
                                            break
                                    if re.match(r'^(Section|Article|[0-9]+\.|[A-Z][A-Z ]{3,})', word):
                                        is_heading = True
                                if is_heading:
                                    lines.append('## ' + raw)
                                elif re.match(r"^\d+\. ", raw):
                                    lines.append(' ' * indent + raw)
                                elif re.match(r"^\([a-zA-Z]\)", raw, re.IGNORECASE):
                                    lines.append(' ' * (indent + 4) + raw)
                                elif re.match(r"^\([ivxlcdmIVXLCDM]+\)", raw):
                                    lines.append(' ' * (indent + 8) + raw)
                                else:
                                    lines.append(' ' * indent + raw)
                        else:
                            page_text = page.extract_text() or ''
                            lines.extend(page_text.splitlines())
                text = '\n'.join(lines)
                print("[pdfplumber] Layout-based extraction with heading detection complete.")
                sys.stdout.flush()
            except Exception as e:
                print(f"[pdfplumber] Extraction failed: {e}")
                traceback.print_exc()
                sys.stdout.flush()
        # Step 5: PyPDF2
        if not text.strip():
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                print("[PyPDF2] Extraction complete.")
                sys.stdout.flush()
            except Exception as e:
                print(f"[PyPDF2] Extraction failed: {e}")
                traceback.print_exc()
                sys.stdout.flush()
                return ""
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from Word documents"""
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from plain text files"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def extract_text_from_csv(self, file_path: str) -> str:
        """Convert CSV to text representation"""
        df = pd.read_csv(file_path)
        return df.to_string()
    
    def extract_text_from_json(self, file_path: str) -> str:
        """Convert JSON to text representation"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return json.dumps(data, indent=2)
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a single document and return metadata + text"""
        path = Path(file_path)
        file_extension = path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            # Extract text based on file type
            if file_extension == '.pdf':
                text = self.extract_text_from_pdf(file_path)
            elif file_extension == '.docx':
                text = self.extract_text_from_docx(file_path)
            elif file_extension == '.txt':
                text = self.extract_text_from_txt(file_path)
            elif file_extension == '.csv':
                text = self.extract_text_from_csv(file_path)
            elif file_extension == '.json':
                text = self.extract_text_from_json(file_path)
            
            # Validate that we extracted meaningful text
            if not text or len(text.strip()) < 10:
                raise ValueError("Document appears to be empty or contains no extractable text")
            
            # Enhance text using GPT-4 if available
            enhanced_data = None
            if self.use_gpt4_enhancement and self.gpt4_extractor:
                enhanced_data = self.enhance_text_with_gpt4(text, file_extension, prefer_private_gpt4=True)
                text = enhanced_data["enhanced_text"]
                print(f"[GPT-4] Enhanced text length: {len(text)}")
            
            # Extract structured data using GPT-4 if available
            structured_data = None
            if self.use_gpt4_enhancement and self.gpt4_extractor:
                # Extract common data types
                data_types = ["dates", "names", "amounts", "key_terms"]
                if file_extension == '.pdf':
                    data_types.extend(["contracts", "references"])
                
                structured_data = self.extract_structured_data_with_gpt4(text, data_types, prefer_private_gpt4=True)
                print(f"[GPT-4] Extracted structured data: {len(structured_data.get('extracted_data', {}))} data types")
            
            # Generate document metadata
            file_stats = path.stat()
            doc_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # Build metadata
            metadata = {
                'filename': path.name,
                'filepath': str(path),
                'file_size': file_stats.st_size,
                'modified_time': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'file_type': file_extension,
                'text': text,
                'text_length': len(text),
                'doc_hash': doc_hash,
                'processed_time': datetime.now().isoformat(),
                'extraction_method': self._get_extraction_method(file_extension)
            }
            
            # Add GPT-4 enhancement metadata
            if enhanced_data:
                metadata['gpt4_enhancement'] = {
                    'quality_score': enhanced_data.get('quality_score', 0.5),
                    'processing_notes': enhanced_data.get('processing_notes', ''),
                    'extracted_metadata': enhanced_data.get('metadata', {})
                }
            
            # Add structured data
            if structured_data:
                metadata['structured_data'] = structured_data
            
            return metadata
            
        except Exception as e:
            # Return error information for debugging
            return {
                'filename': path.name,
                'filepath': str(path),
                'file_type': file_extension,
                'error': str(e),
                'processed_time': datetime.now().isoformat(),
                'success': False
            }
    
    def _get_extraction_method(self, file_extension: str) -> str:
        """Return the extraction method used for the file type"""
        methods = {
            '.pdf': 'unstructured/pdfplumber/Tesseract OCR/PyPDF2',
            '.docx': 'python-docx',
            '.txt': 'direct read',
            '.csv': 'pandas',
            '.json': 'json module'
        }
        return methods.get(file_extension, 'unknown')
    
    def enhance_text_with_gpt4(self, raw_text: str, file_type: str, prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Enhance extracted text using GPT-4
        
        Args:
            raw_text: Raw extracted text
            file_type: Type of file (.pdf, .docx, etc.)
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Dictionary with enhanced text and metadata
        """
        if not self.use_gpt4_enhancement or not self.gpt4_extractor:
            return {
                "enhanced_text": raw_text,
                "metadata": {},
                "quality_score": 0.5,
                "processing_notes": "GPT-4 enhancement not available"
            }
        
        try:
            print(f"[GPT-4] Enhancing {file_type} text extraction (prefer_private_gpt4: {prefer_private_gpt4})...")
            result = self.gpt4_extractor.enhance_text_extraction(raw_text, file_type, prefer_private_gpt4=prefer_private_gpt4)
            
            if result.get("success"):
                enhanced_data = result.get("extracted_data", {})
                enhanced_text = enhanced_data.get("enhanced_text", raw_text)
                metadata = enhanced_data.get("metadata", {})
                quality_score = enhanced_data.get("quality_score", 0.5)
                
                print(f"[GPT-4] Text enhancement completed (quality: {quality_score})")
                return {
                    "enhanced_text": enhanced_text,
                    "metadata": metadata,
                    "quality_score": quality_score,
                    "processing_notes": "GPT-4 enhanced extraction"
                }
            else:
                print(f"[GPT-4] Enhancement failed: {result.get('error', 'Unknown error')}")
                return {
                    "enhanced_text": raw_text,
                    "metadata": {},
                    "quality_score": 0.5,
                    "processing_notes": f"GPT-4 enhancement failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"[GPT-4] Enhancement error: {e}")
            return {
                "enhanced_text": raw_text,
                "metadata": {},
                "quality_score": 0.5,
                "processing_notes": f"GPT-4 enhancement error: {str(e)}"
            }
    
    def extract_structured_data_with_gpt4(self, text: str, data_types: List[str], prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Extract structured data using GPT-4
        
        Args:
            text: Document text
            data_types: List of data types to extract
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Extracted structured data
        """
        if not self.use_gpt4_enhancement or not self.gpt4_extractor:
            return {
                "extracted_data": {},
                "confidence_scores": {},
                "processing_summary": "GPT-4 extraction not available"
            }
        
        try:
            print(f"[GPT-4] Extracting structured data: {data_types} (prefer_private_gpt4: {prefer_private_gpt4})")
            result = self.gpt4_extractor.extract_structured_data(text, data_types, prefer_private_gpt4=prefer_private_gpt4)
            
            if result.get("success"):
                return result.get("extracted_data", {})
            else:
                print(f"[GPT-4] Structured data extraction failed: {result.get('error', 'Unknown error')}")
                return {
                    "extracted_data": {},
                    "confidence_scores": {},
                    "processing_summary": f"GPT-4 extraction failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            print(f"[GPT-4] Structured data extraction error: {e}")
            return {
                "extracted_data": {},
                "confidence_scores": {},
                "processing_summary": f"GPT-4 extraction error: {str(e)}"
            }
    
    def chunk_text_with_gpt4(self, text: str, document_type: str = "general", preserve_structure: bool = True, prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Chunk text using GPT-4 intelligent chunking
        
        Args:
            text: Document text to chunk
            document_type: Type of document (legal, technical, general, etc.)
            preserve_structure: Whether to preserve document structure
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Chunking results with optimized chunks
        """
        if not self.use_gpt4_chunking or not self.gpt4_chunker:
            return {"error": "GPT-4 chunking not available", "chunks": []}
        
        try:
            print(f"[GPT-4] Chunking document with type: {document_type} (prefer_private_gpt4: {prefer_private_gpt4})")
            result = self.gpt4_chunker.chunk_document_with_gpt4(text, document_type, preserve_structure, prefer_private_gpt4=prefer_private_gpt4)
            
            # Optimize chunks for RAG if successful
            if result.get('success') and result.get('chunks'):
                print(f"[GPT-4] Optimizing {len(result['chunks'])} chunks for RAG")
                optimized_chunks = self.gpt4_chunker.optimize_chunks_for_rag(result['chunks'])
                result['chunks'] = optimized_chunks
            
            return result
        except Exception as e:
            print(f"[GPT-4] Error in GPT-4 chunking: {e}")
            return {"error": str(e), "chunks": []}

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):  # Should be localhost:11434
        self.base_url = base_url
        self.session = requests.Session()
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        response = self.session.get(f"{self.base_url}/api/tags")
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    
    def generate(self, model: str, prompt: str, system_prompt: str = None) -> str:
        """Generate response from Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = self.session.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            raise Exception(f"Error generating response: {response.text}")

class DocumentRAG:
    """Main RAG system for document processing and querying"""
    
    def __init__(self, 
                 model_name: str = "llama3.1:8b",  # Use this proven model
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 512,  # 512 characters per chunk
                 chunk_overlap: int = 128,  # 128 character overlap
                 chroma_db_path: str = "./chroma_db"):
        
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.ollama_client = OllamaClient()
        # Use SentenceTransformer for embeddings
        from sentence_transformers import SentenceTransformer
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chroma_db_path = chroma_db_path

        # Character-based chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Default system prompt - can be customized
        self.system_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 

CORE INSTRUCTIONS:
- Use only the information from the provided context to answer questions
- If you cannot find the answer in the provided context, say so clearly
- Be concise but thorough in your responses
- Always cite which document or section your answer comes from when possible
- Maintain a professional and helpful tone

RESPONSE FORMAT:
- Provide direct answers based on the document content
- Include specific details and examples when available
- If multiple documents contain relevant information, synthesize them coherently
- End with a brief statement about which documents were referenced"""
    
    def update_system_prompt(self, new_prompt: str) -> bool:
        """Update the system prompt for AI responses"""
        try:
            self.system_prompt = new_prompt.strip()
            return True
        except Exception as e:
            print(f"Error updating system prompt: {e}")
            return False
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt"""
        return self.system_prompt
    
    def reset_system_prompt(self) -> str:
        """Reset to default system prompt"""
        default_prompt = """You are a helpful AI assistant that answers questions based on provided documents. 

CORE INSTRUCTIONS:
- Use only the information from the provided context to answer questions
- If you cannot find the answer in the provided context, say so clearly
- Be concise but thorough in your responses
- Always cite which document or section your answer comes from when possible
- Maintain a professional and helpful tone

RESPONSE FORMAT:
- Provide direct answers based on the document content
- Include specific details and examples when available
- If multiple documents contain relevant information, synthesize them coherently
- End with a brief statement about which documents were referenced"""
        
        self.system_prompt = default_prompt
        return self.system_prompt
    
    def check_setup(self) -> Dict[str, bool]:
        """Check if all components are working"""
        return {
            "ollama_available": self.ollama_client.is_available(),
            "model_available": self.model_name in self.ollama_client.list_models(),
            "embedding_model_loaded": self.embedding_model is not None,
            "chroma_db_initialized": self.collection is not None
        }
    
    def ingest_document(self, file_path: str) -> str:
        """Ingest a single document into the system"""
        import sys, traceback
        print(f"[DEBUG] ingest_document called with: {file_path}")
        sys.stdout.flush()
        try:
            # Process document
            print("[DEBUG] Processing document...")
            doc_data = self.document_processor.process_document(file_path)
            print(f"[DEBUG] doc_data: {doc_data}")
            sys.stdout.flush()
            # Check if processing failed
            if 'error' in doc_data:
                print(f"[DEBUG] Error in doc_data: {doc_data['error']}")
                sys.stdout.flush()
                return f"Error processing {doc_data['filename']}: {doc_data['error']}"
            
            # Generate unique document identifier (consistent with PDF processing)
            import hashlib
            import time
            filename = doc_data['filename']
            file_stats = os.stat(file_path)
            doc_hash = hashlib.md5(f"{filename}_{file_stats.st_size}_{file_stats.st_mtime}".encode()).hexdigest()[:8]
            timestamp = int(time.time())
            doc_id = f"{filename}_{doc_hash}_{timestamp}"
            
            # Check if document already exists (using new document ID system)
            print("[DEBUG] Checking for existing docs...")
            existing_docs = self.collection.get(
                where={"document_id": doc_id}
            )
            print(f"[DEBUG] existing_docs: {existing_docs}")
            sys.stdout.flush()
            if existing_docs['ids']:
                print("[DEBUG] Document already exists in DB")
                sys.stdout.flush()
                return f"Document {doc_data['filename']} already exists in the database"
            
            # Validate text content
            if len(doc_data['text'].strip()) < 50:
                print("[DEBUG] Insufficient text content")
                sys.stdout.flush()
                return f"Document {doc_data['filename']} contains insufficient text content (less than 50 characters)"
            
            # Split text into chunks using GPT-4 if available, otherwise fallback to traditional chunking
            print("[DEBUG] Splitting text into chunks...")
            
            # Try GPT-4 chunking first if available
            gpt4_chunking_result = None
            if self.document_processor.use_gpt4_chunking and self.document_processor.gpt4_chunker:
                try:
                    print("[DEBUG] Attempting GPT-4 chunking...")
                    # Determine document type based on file extension
                    file_ext = os.path.splitext(doc_data['filename'])[1].lower()
                    document_type = "legal" if file_ext == '.pdf' else "general"
                    
                    gpt4_chunking_result = self.document_processor.chunk_text_with_gpt4(
                        doc_data['text'], 
                        document_type=document_type, 
                        preserve_structure=True,
                        prefer_private_gpt4=True
                    )
                    
                    if gpt4_chunking_result.get('success') and gpt4_chunking_result.get('chunks'):
                        print(f"[DEBUG] GPT-4 chunking successful: {len(gpt4_chunking_result['chunks'])} chunks")
                        chunks = [chunk['content'] for chunk in gpt4_chunking_result['chunks']]
                        chunking_method = "gpt4_intelligent"
                    else:
                        print(f"[DEBUG] GPT-4 chunking failed: {gpt4_chunking_result.get('error', 'Unknown error')}")
                        # Fallback to traditional chunking
                        chunks = self.text_splitter.split_text(doc_data['text'])
                        chunking_method = "traditional_fallback"
                        
                except Exception as e:
                    print(f"[DEBUG] GPT-4 chunking error: {e}")
                    # Fallback to traditional chunking
                    chunks = self.text_splitter.split_text(doc_data['text'])
                    chunking_method = "traditional_fallback"
            else:
                # Use traditional chunking
                chunks = self.text_splitter.split_text(doc_data['text'])
                chunking_method = "traditional"
            
            print(f"[DEBUG] Number of chunks: {len(chunks)} (method: {chunking_method})")
            sys.stdout.flush()
            if not chunks:
                print("[DEBUG] No chunks generated")
                sys.stdout.flush()
                return f"Document {doc_data['filename']} could not be split into chunks"
            
            # Generate embeddings
            try:
                print("[DEBUG] Generating embeddings...")
                embeddings = self.embedding_model.encode(chunks).tolist()
                print("[DEBUG] Embeddings generated")
                sys.stdout.flush()
            except Exception as e:
                print(f"[DEBUG] Error generating embeddings: {e}")
                traceback.print_exc()
                sys.stdout.flush()
                return f"Error generating embeddings for {doc_data['filename']}: {str(e)}"
            
            # Prepare data for ChromaDB with new document ID system
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "filename": doc_data['filename'],
                    "filepath": doc_data['filepath'],
                    "file_type": doc_data['file_type'],
                    "doc_hash": doc_data['doc_hash'],
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "text_length": doc_data['text_length'],
                    "extraction_method": doc_data['extraction_method'],
                    "processed_time": doc_data['processed_time'],
                    "document_id": doc_id,
                    "upload_timestamp": str(timestamp),
                    "chunking_method": chunking_method
                }
                
                # Add GPT-4 chunking metadata if available
                if gpt4_chunking_result and gpt4_chunking_result.get('success') and i < len(gpt4_chunking_result.get('chunks', [])):
                    gpt4_chunk = gpt4_chunking_result['chunks'][i]
                    metadata.update({
                        "gpt4_chunked": True,
                        "chunk_type": gpt4_chunk.get('chunk_type', 'paragraph'),
                        "section_number": gpt4_chunk.get('section_number', ''),
                        "section_title": gpt4_chunk.get('section_title', ''),
                        "semantic_theme": gpt4_chunk.get('semantic_theme', ''),
                        "quality_score": gpt4_chunk.get('quality_score', 0.8)
                    })
                else:
                    metadata["gpt4_chunked"] = False
                
                metadatas.append(metadata)
            
            # Add to ChromaDB
            try:
                print("[DEBUG] Adding to ChromaDB...")
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                print("[DEBUG] Added to ChromaDB")
                sys.stdout.flush()
            except Exception as e:
                print(f"[DEBUG] Error storing in database: {e}")
                traceback.print_exc()
                sys.stdout.flush()
                return f"Error storing {doc_data['filename']} in database: {str(e)}"
            
            print("[DEBUG] Successfully ingested document")
            sys.stdout.flush()
            return f"Successfully ingested {doc_data['filename']} with {len(chunks)} chunks ({doc_data['text_length']} characters)"
        except Exception as e:
            print(f"[ERROR] Exception in ingest_document: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            sys.stderr.flush()
            return f"Unexpected error ingesting document: {str(e)}"
    
    def ingest_directory(self, directory_path: str) -> List[str]:
        """Ingest all supported documents from a directory"""
        results = []
        directory = Path(directory_path)
        
        if not directory.exists():
            return [f"Directory {directory_path} does not exist"]
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.document_processor.supported_formats:
                result = self.ingest_document(str(file_path))
                results.append(f"{file_path.name}: {result}")
        
        return results
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant document chunks"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return search_results
    
    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the document collection and generate an answer"""
        # Search for relevant chunks
        search_results = self.search_documents(question, n_results)
        
        if not search_results:
            return {
                'answer': "I couldn't find any relevant information in the documents.",
                'sources': [],
                'context_used': []
            }
        
        # Prepare context for the LLM
        context_parts = []
        sources = set()
        
        for result in search_results:
            context_parts.append(f"From {result['metadata']['filename']}:\n{result['document']}")
            sources.add(result['metadata']['filename'])
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Create the prompt
        prompt = f"""Context from documents:
{context}

Question: {question}

Please answer the question based on the provided context."""
        
        # Generate answer using Ollama
        try:
            answer = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            return {
                'answer': answer,
                'sources': list(sources),
                'context_used': [r['document'][:200] + "..." for r in search_results[:3]],
                'search_results': search_results
            }
            
        except Exception as e:
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': [],
                'context_used': []
            }
    
    def list_documents(self) -> List[Dict]:
        """List all documents in the database"""
        all_docs = self.collection.get()
        
        # Group by document
        docs_by_hash = {}
        for i, metadata in enumerate(all_docs['metadatas']):
            doc_hash = metadata['doc_hash']
            if doc_hash not in docs_by_hash:
                docs_by_hash[doc_hash] = {
                    'filename': metadata['filename'],
                    'filepath': metadata['filepath'],
                    'file_type': metadata['file_type'],
                    'processed_time': metadata['processed_time'],
                    'total_chunks': metadata['total_chunks']
                }
        
        return list(docs_by_hash.values())
    
    def delete_document(self, filename: str) -> str:
        """Delete a document from the database"""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"filename": filename}
            )
            
            if not results['ids']:
                return f"Document {filename} not found"
            
            # Delete all chunks
            self.collection.delete(ids=results['ids'])
            
            return f"Successfully deleted {filename} ({len(results['ids'])} chunks)"
            
        except Exception as e:
            return f"Error deleting document: {str(e)}"

# Example usage and setup
def main():
    """Example usage of the DocumentRAG system"""
    
    # Initialize the RAG system
    rag = DocumentRAG()
    
    # Check setup
    setup_status = rag.check_setup()
    print("Setup Status:")
    for component, status in setup_status.items():
        print(f"  {component}: {'✓' if status else '✗'}")
    
    if not setup_status['ollama_available']:
        print("\nOllama is not available. Make sure it's running with:")
        print("docker run -d -v ~/.ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama")
        return
    
    if not setup_status['model_available']:
        print(f"\nModel {rag.model_name} not found. Pull it with:")
        print(f"docker exec -it ollama ollama pull {rag.model_name}")
        return
    
    # Example usage
    print("\n=== Document RAG System Ready ===")
    print("Example commands:")
    print("1. rag.ingest_document('/path/to/document.pdf')")
    print("2. rag.ingest_directory('/path/to/documents/')")
    print("3. rag.query('What is the main topic of the document?')")
    print("4. rag.list_documents()")
    print("5. rag.delete_document('filename.pdf')")

if __name__ == "__main__":
    main()