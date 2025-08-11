#!/usr/bin/env python3
"""
LangExtract Chunking Module for Document RAG System

This module implements Google's LangExtract as an alternative chunking technology
that provides intelligent document structure extraction and chunking.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LangExtractChunk:
    """Represents a LangExtract chunk with metadata"""
    content: str
    chunk_id: str
    section_type: str
    section_title: str
    chunk_type: str
    semantic_theme: str
    list_items: List[Dict[str, Any]]
    start_position: int
    end_position: int
    confidence: float
    extraction_method: str

class LangExtractChunker:
    """
    LangExtract-based chunking that uses Google's LangExtract for intelligent
    document structure extraction and chunking
    """
    
    def __init__(self, 
                 max_chunk_size: int = 2000,
                 min_chunk_size: int = 200,
                 preserve_lists: bool = True,
                 preserve_sections: bool = True,
                 use_langextract_api: bool = True,
                 enable_roman_numerals: bool = True,
                 enable_bullet_points: bool = True,
                 enable_indented_lists: bool = True,
                 enable_legal_patterns: bool = True,
                 enable_multi_level: bool = True,
                 custom_list_patterns: List[str] = None):
        
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.preserve_lists = preserve_lists
        self.preserve_sections = preserve_sections
        self.use_langextract_api = use_langextract_api
        self.enable_roman_numerals = enable_roman_numerals
        self.enable_bullet_points = enable_bullet_points
        self.enable_indented_lists = enable_indented_lists
        self.enable_legal_patterns = enable_legal_patterns
        self.enable_multi_level = enable_multi_level
        self.custom_list_patterns = custom_list_patterns or []
        
        # Initialize LangExtract if available
        self.langextract_available = False
        if self.use_langextract_api:
            try:
                # Try to import LangExtract
                import langchain_google_genai
                from langchain_google_genai import GoogleGenerativeAI
                self.langextract_available = True
                logger.info("LangExtract API available")
            except ImportError:
                logger.warning("LangExtract API not available, using fallback methods")
                self.langextract_available = False
        
        # Patterns for detecting sections and lists (fallback)
        self.section_patterns = [
            r'^##\s*(\d+\.\d+)\s+(.+)$',  # ## 3.2 Objectives
            r'^(\d+\.\d+)\s+(.+)$',       # 3.2 Objectives
            r'^Section\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',  # Section 3.2: Objectives
            r'^Clause\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',   # Clause 3.2: Objectives
        ]
        
        # Build list patterns dynamically based on configuration
        self.list_patterns = self._build_list_patterns()
        
        self.objectives_keywords = [
            'objectives', 'objective', 'goals', 'aims', 'purposes',
            'targets', 'outcomes', 'results', 'deliverables'
        ]
    
    def _build_list_patterns(self) -> List[str]:
        """
        Build list patterns dynamically based on configuration
        
        Returns:
            List of regex patterns for list detection
        """
        patterns = []
        
        # Always include basic numbered and letter patterns
        patterns.extend([
            # Numbered lists
            r'^(\d+)\.\s+(.+)$',          # 1. First objective
            r'^\((\d+)\)\s+(.+)$',        # (1) First objective
            r'^(\d+\))\s+(.+)$',          # 1) First objective
            
            # Letter lists
            r'^([a-z])\.\s+(.+)$',        # a. Sub-objective
            r'^\(([a-z])\)\s+(.+)$',      # (a) Sub-objective
            r'^([a-z])\)\s+(.+)$',        # a) Sub-objective
            r'^([A-Z])\.\s+(.+)$',        # A. Major objective
            r'^\(([A-Z])\)\s+(.+)$',      # (A) Major objective
            r'^([A-Z])\)\s+(.+)$',        # A) Major objective
        ])
        
        # Add Roman numerals if enabled
        if self.enable_roman_numerals:
            patterns.extend([
                r'^(i|ii|iii|iv|v|vi|vii|viii|ix|x)\.\s+(.+)$',  # i. First item
                r'^\((i|ii|iii|iv|v|vi|vii|viii|ix|x)\)\s+(.+)$',  # (i) First item
                r'^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s+(.+)$',  # I. First item
                r'^\((I|II|III|IV|V|VI|VII|VIII|IX|X)\)\s+(.+)$',  # (I) First item
            ])
        
        # Add bullet points if enabled
        if self.enable_bullet_points:
            patterns.extend([
                r'^[-*•]\s+(.+)$',        # - Bullet point
                r'^[•]\s+(.+)$',          # • Bullet point
                r'^[*]\s+(.+)$',          # * Bullet point
            ])
        
        # Add indented lists if enabled
        if self.enable_indented_lists:
            patterns.extend([
                r'^\s+(\d+)\.\s+(.+)$',   #   1. Indented item
                r'^\s+([a-z])\.\s+(.+)$', #   a. Indented item
                r'^\s+([A-Z])\.\s+(.+)$', #   A. Indented item
                r'^\s+[-*•]\s+(.+)$',     #   - Indented bullet
            ])
        
        # Add legal patterns if enabled
        if self.enable_legal_patterns:
            patterns.extend([
                r'^(\d+\.\d+)\s+(.+)$',       # 1.1 Subsection
                r'^(\d+\.\d+\.\d+)\s+(.+)$',  # 1.1.1 Sub-subsection
                r'^\((\d+\.\d+)\)\s+(.+)$',   # (1.1) Subsection
                r'^\((\d+\.\d+\.\d+)\)\s+(.+)$', # (1.1.1) Sub-subsection
                
                # Contract-specific patterns
                r'^Clause\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',  # Clause 1.1: Description
                r'^Section\s+(\d+\.\d+)\s*[:.]?\s*(.+)$', # Section 1.1: Description
                r'^Article\s+(\d+\.\d+)\s*[:.]?\s*(.+)$', # Article 1.1: Description
            ])
        
        # Add multi-level patterns if enabled
        if self.enable_multi_level:
            patterns.extend([
                r'^(\d+)\)\s+([a-z])\.\s+(.+)$',  # 1) a. Sub-item
                r'^(\d+)\)\s+(\d+)\.\s+(.+)$',    # 1) 1. Sub-item
            ])
        
        # Add custom patterns
        patterns.extend(self.custom_list_patterns)
        
        return patterns
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """
        Get information about the current configuration
        
        Returns:
            Dictionary with configuration details
        """
        return {
            'max_chunk_size': self.max_chunk_size,
            'min_chunk_size': self.min_chunk_size,
            'preserve_lists': self.preserve_lists,
            'preserve_sections': self.preserve_sections,
            'use_langextract_api': self.use_langextract_api,
            'enable_roman_numerals': self.enable_roman_numerals,
            'enable_bullet_points': self.enable_bullet_points,
            'enable_indented_lists': self.enable_indented_lists,
            'enable_legal_patterns': self.enable_legal_patterns,
            'enable_multi_level': self.enable_multi_level,
            'custom_list_patterns': self.custom_list_patterns,
            'total_list_patterns': len(self.list_patterns),
            'list_patterns': self.list_patterns
        }
    
    def chunk_document(self, text: str) -> List[LangExtractChunk]:
        """
        Chunk document using LangExtract for intelligent structure extraction
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of LangExtract chunks
        """
        logger.info("Starting LangExtract chunking of document")
        
        if self.langextract_available and self.use_langextract_api:
            try:
                return self._chunk_with_langextract_api(text)
            except Exception as e:
                logger.error(f"LangExtract API failed: {e}")
                return self._fallback_chunking(text)
        else:
            return self._fallback_chunking(text)
    
    def _chunk_with_langextract_api(self, text: str) -> List[LangExtractChunk]:
        """
        Use LangExtract API for intelligent document structure extraction
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of LangExtract chunks
        """
        try:
            # Import LangExtract components
            from langchain_google_genai import GoogleGenerativeAI
            from langchain.schema import HumanMessage, SystemMessage
            
            # Initialize Google Generative AI
            genai = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )
            
            # Create LangExtract prompt for document structure extraction
            system_prompt = """You are an expert document structure analyzer using LangExtract principles. 
            
Your task is to analyze the provided document and extract its structural components in a JSON format that includes:

1. **Sections**: Identify main sections, subsections, and their hierarchical relationships
2. **Lists**: Extract numbered and bulleted lists with their items
3. **Key Information**: Identify objectives, definitions, obligations, and other important content
4. **Semantic Themes**: Categorize content by semantic meaning

For each extracted component, provide:
- content: The actual text content
- section_type: The type of section (e.g., "objectives", "definitions", "obligations")
- section_title: The title or heading
- semantic_theme: The semantic category
- confidence: Confidence score (0.0-1.0)
- list_items: Array of list items if applicable

Return the result as a valid JSON object with the structure:
{
  "extracted_components": [
    {
      "content": "text content",
      "section_type": "type",
      "section_title": "title",
      "semantic_theme": "theme",
      "confidence": 0.95,
      "list_items": [],
      "start_position": 0,
      "end_position": 100
    }
  ]
}"""

            # Create the extraction prompt
            extraction_prompt = f"""Please analyze the following document and extract its structural components using LangExtract principles:

{text}

Extract all sections, lists, and key information while preserving the document's semantic structure."""

            # Get response from LangExtract
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=extraction_prompt)
            ]
            
            response = genai.invoke(messages)
            
            # Parse the response
            try:
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # If no JSON found, try to parse the entire response
                    result = json.loads(response.content)
                
                # Convert to LangExtractChunk objects
                chunks = []
                for i, component in enumerate(result.get('extracted_components', [])):
                    chunk = LangExtractChunk(
                        content=component.get('content', ''),
                        chunk_id=f"langextract_{i+1}",
                        section_type=component.get('section_type', 'general'),
                        section_title=component.get('section_title', ''),
                        chunk_type=component.get('chunk_type', 'extracted'),
                        semantic_theme=component.get('semantic_theme', 'general'),
                        list_items=component.get('list_items', []),
                        start_position=component.get('start_position', 0),
                        end_position=component.get('end_position', len(component.get('content', ''))),
                        confidence=component.get('confidence', 0.8),
                        extraction_method='langextract_api'
                    )
                    chunks.append(chunk)
                
                logger.info(f"LangExtract API extracted {len(chunks)} components")
                return chunks
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LangExtract response as JSON: {e}")
                return self._fallback_chunking(text)
                
        except Exception as e:
            logger.error(f"LangExtract API error: {e}")
            return self._fallback_chunking(text)
    
    def _fallback_chunking(self, text: str) -> List[LangExtractChunk]:
        """
        Fallback chunking when LangExtract API is not available
        
        Args:
            text: Text to chunk
            
        Returns:
            List of LangExtract chunks
        """
        logger.info("Using fallback chunking method")
        
        # Split text into lines for analysis
        lines = text.split('\n')
        
        # Identify sections and their boundaries
        sections = self._identify_sections(lines)
        logger.info(f"Identified {len(sections)} sections")
        
        # Process each section into chunks
        chunks = []
        for i, section in enumerate(sections):
            section_chunks = self._chunk_section(section, i)
            chunks.extend(section_chunks)
        
        # If no sections found, use basic chunking
        if not chunks:
            logger.info("No sections found, using basic chunking")
            chunks = self._basic_chunking(text)
        
        logger.info(f"Created {len(chunks)} LangExtract chunks")
        return chunks
    
    def _identify_sections(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Identify sections in the document
        
        Args:
            lines: Document lines
            
        Returns:
            List of identified sections
        """
        sections = []
        current_section = None
        current_content = []
        current_start_line = 0
        
        for i, line in enumerate(lines):
            # Check if this line is a section header
            section_match = self._match_section_header(line)
            
            if section_match:
                # Save previous section if exists
                if current_section:
                    current_section['content'] = '\n'.join(current_content)
                    current_section['end_line'] = i - 1
                    sections.append(current_section)
                
                # Start new section
                section_number, section_title = section_match
                current_section = {
                    'number': section_number,
                    'title': section_title.strip(),
                    'content': '',
                    'start_line': i,
                    'end_line': i,
                    'type': self._determine_section_type(section_title)
                }
                current_content = []
                current_start_line = i
            else:
                # Add line to current section content
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section:
            current_section['content'] = '\n'.join(current_content)
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _match_section_header(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Check if a line matches a section header pattern
        
        Args:
            line: Line to check
            
        Returns:
            Tuple of (section_number, section_title) if match, None otherwise
        """
        line = line.strip()
        
        for pattern in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.groups()
        
        return None
    
    def _determine_section_type(self, title: str) -> str:
        """
        Determine the type of section based on its title
        
        Args:
            title: Section title
            
        Returns:
            Section type
        """
        title_lower = title.lower()
        
        if any(keyword in title_lower for keyword in self.objectives_keywords):
            return "objectives"
        elif 'scope' in title_lower:
            return "scope"
        elif 'definitions' in title_lower or 'terms' in title_lower:
            return "definitions"
        elif 'obligations' in title_lower or 'responsibilities' in title_lower:
            return "obligations"
        elif 'payment' in title_lower or 'compensation' in title_lower:
            return "payment"
        elif 'termination' in title_lower:
            return "termination"
        else:
            return "general"
    
    def _chunk_section(self, section: Dict[str, Any], section_index: int) -> List[LangExtractChunk]:
        """
        Chunk a section while preserving its structure
        
        Args:
            section: Section to chunk
            section_index: Index of the section
            
        Returns:
            List of chunks for this section
        """
        chunks = []
        
        # Check if section is small enough to keep as one chunk
        if len(section['content']) <= self.max_chunk_size:
            chunk = LangExtractChunk(
                content=f"## {section['number']} {section['title']}\n\n{section['content']}",
                chunk_id=f"langextract_section_{section_index}",
                section_type=section['type'],
                section_title=section['title'],
                chunk_type="complete_section",
                semantic_theme=section['type'],
                list_items=self._extract_list_items(section['content']),
                start_position=0,
                end_position=len(section['content']),
                confidence=0.9,
                extraction_method='fallback_pattern'
            )
            chunks.append(chunk)
        else:
            # Split large section into smaller chunks
            sub_chunks = self._chunk_large_section(section, section_index)
            chunks.extend(sub_chunks)
        
        return chunks
    
    def _extract_list_items(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract list items from content with enhanced pattern matching
        
        Args:
            content: Content to extract list items from
            
        Returns:
            List of list items with metadata
        """
        items = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            # Check for list patterns
            for pattern in self.list_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    
                    # Handle different pattern types
                    if len(groups) == 2:
                        number, text = groups
                    elif len(groups) == 3:
                        # Multi-level patterns like "1) a. text"
                        number = f"{groups[0]}) {groups[1]}."
                        text = groups[2]
                    else:
                        # For bullet points, the first group might be the bullet character
                        number = groups[0] if groups[0] in ['-', '*', '•'] else groups[0]
                        text = groups[1] if len(groups) > 1 else line[len(number):].strip()
                    
                    # Clean up the text
                    text = text.strip()
                    if text:
                        items.append({
                            'number': number,
                            'text': text,
                            'line_number': i,
                            'pattern': pattern,
                            'hierarchy_level': self._get_hierarchy_level(number),
                            'original_line': original_line,
                            'indentation': len(original_line) - len(original_line.lstrip())
                        })
                    break
        
        # Sort items by line number and indentation
        items.sort(key=lambda x: (x['line_number'], x['indentation']))
        
        return items
    
    def _get_hierarchy_level(self, number: str) -> int:
        """
        Determine hierarchy level of a list item
        
        Args:
            number: List item number/marker
            
        Returns:
            Hierarchy level (1 = top level, 2 = sub-level, etc.)
        """
        # Handle multi-level patterns like "1) a."
        if ')' in number and '.' in number:
            return 2
        
        # Handle Roman numerals
        roman_lower = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
        roman_upper = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
        
        if number.lower() in roman_lower:
            return 2
        elif number in roman_upper:
            return 2
        
        # Handle bullet points
        if number in ['-', '*', '•']:
            return 1
        
        # Handle numbered patterns
        if number.isdigit():
            return 1
        
        # Handle letter patterns
        if number.isupper():
            return 2
        elif number.islower():
            return 3
        
        # Handle decimal patterns like "1.1", "1.1.1"
        if '.' in number and number.replace('.', '').isdigit():
            return len(number.split('.'))
        
        # Default to level 1
        return 1
    
    def _chunk_large_section(self, section: Dict[str, Any], section_index: int) -> List[LangExtractChunk]:
        """
        Split a large section into smaller chunks
        
        Args:
            section: Section to split
            section_index: Index of the section
            
        Returns:
            List of chunks
        """
        chunks = []
        content = section['content']
        lines = content.split('\n')
        
        current_chunk = f"## {section['number']} {section['title']}\n\n"
        current_start = 0
        
        for i, line in enumerate(lines):
            # Check if adding this line would exceed chunk size
            if len(current_chunk) + len(line) > self.max_chunk_size and current_chunk.strip():
                # Create chunk
                chunk = LangExtractChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"langextract_section_{section_index}_part_{len(chunks)}",
                    section_type=section['type'],
                    section_title=section['title'],
                    chunk_type="section_part",
                    semantic_theme=section['type'],
                    list_items=self._extract_list_items(current_chunk),
                    start_position=current_start,
                    end_position=len(current_chunk),
                    confidence=0.8,
                    extraction_method='fallback_pattern'
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = f"## {section['number']} {section['title']} (continued)\n\n"
                current_start = len(current_chunk)
            
            current_chunk += line + '\n'
        
        # Add final chunk
        if current_chunk.strip():
            chunk = LangExtractChunk(
                content=current_chunk.strip(),
                chunk_id=f"langextract_section_{section_index}_part_{len(chunks)}",
                section_type=section['type'],
                section_title=section['title'],
                chunk_type="section_part",
                semantic_theme=section['type'],
                list_items=self._extract_list_items(current_chunk),
                start_position=current_start,
                end_position=len(current_chunk),
                confidence=0.8,
                extraction_method='fallback_pattern'
            )
            chunks.append(chunk)
        
        return chunks
    
    def _basic_chunking(self, text: str) -> List[LangExtractChunk]:
        """
        Basic chunking when no sections are detected
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.max_chunk_size // 4,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        raw_chunks = text_splitter.split_text(text)
        chunks = []
        
        for i, chunk_content in enumerate(raw_chunks):
            chunk = LangExtractChunk(
                content=chunk_content,
                chunk_id=f"langextract_basic_{i+1}",
                section_type="general",
                section_title="",
                chunk_type="basic",
                semantic_theme="general",
                list_items=self._extract_list_items(chunk_content),
                start_position=text.find(chunk_content),
                end_position=text.find(chunk_content) + len(chunk_content),
                confidence=0.7,
                extraction_method='basic_splitter'
            )
            chunks.append(chunk)
        
        return chunks

# Example usage and testing
if __name__ == "__main__":
    # Test the LangExtract chunker
    chunker = LangExtractChunker()
    
    # Sample document text
    test_text = """
## 3.2 Objectives

The objectives of this agreement are:

1. Collaboration: Build a collaborative relationship between the Customer and the Contractor to achieve shared outcomes.

2. Value for Money: Deliver services in a manner that provides measurable value for money for the Customer.

3. Continuous Improvement: Ensure ongoing enhancements in the quality, efficiency, and effectiveness of the services.

4. Innovation: Encourage innovation to meet evolving requirements and challenges faced by the Customer.

5. Risk Management: Proactively manage risks to minimize disruptions and ensure service continuity.

6. Compliance: Adhere to all applicable laws, regulations, and policies governing the services.

7. Performance Transparency: Maintain clear and measurable service delivery performance levels, supported by timely reporting.

8. Customer Satisfaction: Deliver services in a manner that optimally meets the needs of end-users and stakeholders.

9. Sustainability: Support environmentally and socially sustainable practices in the delivery of services.

## 3.3 Achievement of Objectives

The Contractor must continuously seek ways to improve services to better achieve these objectives.
"""
    
    chunks = chunker.chunk_document(test_text)
    
    print("LangExtract Chunking Results:")
    print("=" * 50)
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.chunk_id}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Section: {chunk.section_type} - {chunk.section_title}")
        print(f"Confidence: {chunk.confidence}")
        print(f"Extraction Method: {chunk.extraction_method}")
        print(f"List Items: {len(chunk.list_items)}")
        print(f"Content Preview: {chunk.content[:100]}...")
        
        if chunk.list_items:
            print("List Items Found:")
            for item in chunk.list_items:
                print(f"  {item['number']}. {item['text'][:50]}...")
