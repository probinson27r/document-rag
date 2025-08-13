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
            import os
            
            # Try to get API key from AWS Secrets Manager first, then fallback to environment
            api_key = None
            try:
                from aws_secrets import get_google_api_key
                api_key = get_google_api_key()
                if api_key:
                    logger.info("Google API key retrieved from AWS Secrets Manager")
                else:
                    logger.warning("Google API key not found in AWS Secrets Manager, trying environment variables")
            except Exception as aws_error:
                logger.warning(f"Failed to retrieve Google API key from AWS Secrets Manager: {aws_error}")
                logger.info("Falling back to environment variables")
            
            # Fallback to environment variables if AWS Secrets Manager fails
            if not api_key:
                try:
                    from dotenv import load_dotenv
                    load_dotenv('.env.local')
                except ImportError:
                    pass  # dotenv not available
                
                api_key = os.getenv('GOOGLE_API_KEY')
                if api_key:
                    logger.info("Google API key retrieved from environment variables")
            
            if not api_key:
                logger.error("Google API key not found in AWS Secrets Manager or environment variables")
                logger.error("Please either:")
                logger.error("1. Store the key in AWS Secrets Manager as 'legal-rag/google-api-key'")
                logger.error("2. Set GOOGLE_API_KEY in .env.local or environment variables")
                raise ValueError("Google API key is required for LangExtract API mode")
            
            # Initialize Google Generative AI
            genai = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.1,  # Low temperature for consistent extraction
                max_output_tokens=8192  # Increased for larger documents
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

            # Get response from LangExtract API
            full_prompt = f"{system_prompt}\n\nDocument to analyze:\n{text}\n\nExtract all sections, lists, and key information while preserving the document's semantic structure."
            
            logger.info("Calling Google GenAI API for document structure extraction...")
            response = genai.invoke(full_prompt)
            
            # Parse the response
            try:
                # Extract content from response (handle different response formats)
                response_text = response if isinstance(response, str) else str(response)
                logger.info(f"Received response from Google GenAI: {len(response_text)} characters")
                
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # If no JSON found, try to parse the entire response
                    result = json.loads(response_text)
                
                # Merge any split lists to preserve complete objective lists
                components = result.get('extracted_components', [])
                merged_components = self._merge_split_lists(components)
                logger.info(f"Original components: {len(components)}, After list merging: {len(merged_components)}")
                
                # Convert to LangExtractChunk objects
                chunks = []
                for i, component in enumerate(merged_components):
                    # Handle content that might be a list or string
                    raw_content = component.get('content', '')
                    if isinstance(raw_content, list):
                        content = '\n'.join(str(item) for item in raw_content if item).strip()
                    else:
                        content = str(raw_content).strip()
                    
                    if not content:
                        continue
                    
                    # Check if this is a complete list
                    is_complete_list = self._contains_multiple_list_items(content)
                    
                    chunk = LangExtractChunk(
                        content=content,
                        chunk_id=f"langextract_{i+1}",
                        section_type=component.get('section_type', 'general'),
                        section_title=component.get('section_title', ''),
                        chunk_type="complete_list" if is_complete_list else component.get('chunk_type', 'extracted'),
                        semantic_theme=component.get('semantic_theme', 'general'),
                        list_items=self._extract_list_items(content) if is_complete_list else component.get('list_items', []),
                        start_position=component.get('start_position', 0),
                        end_position=component.get('end_position', len(content)),
                        confidence=component.get('confidence', 0.8),
                        extraction_method='langextract_api'
                    )
                    chunks.append(chunk)
                
                logger.info(f"LangExtract API extracted {len(chunks)} final chunks")
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
        Extract list items from content with nested list support
        
        Args:
            content: Content to extract list items from
            
        Returns:
            List of list items with metadata including nested structure
        """
        items = []
        lines = content.split('\n')
        
        # First pass: identify all list items with their indentation
        raw_items = []
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
                    
                    # Special handling for bullet points - check if this is a bullet point pattern
                    if pattern in [r'^[-*•]\s+(.+)$', r'^\s+[-*•]\s+(.+)$']:
                        # For bullet point patterns, the first group is the text, not the bullet
                        # We need to extract the bullet character from the original line
                        bullet_char = line.strip()[0]  # Get the first character
                        number = bullet_char
                        text = groups[0]  # The text is in the first group
                    
                    # Clean up the text
                    text = text.strip()
                    if text:
                        indentation = len(original_line) - len(original_line.lstrip())
                        raw_items.append({
                            'number': number,
                            'text': text,
                            'line_number': i,
                            'pattern': pattern,
                            'original_line': original_line,
                            'indentation': indentation,
                            'list_type': self._determine_list_type(number),
                            'parent_id': None,
                            'children': []
                        })
                    break
        
        # Second pass: build nested structure based on indentation
        items = self._build_nested_structure(raw_items)
        
        return items
    
    def _determine_list_type(self, number: str) -> str:
        """
        Determine if a list item is ordered or unordered
        
        Args:
            number: List item number/marker
            
        Returns:
            'ordered' or 'unordered'
        """
        # Unordered list markers
        if number in ['-', '*', '•']:
            return 'unordered'
        
        # Ordered list markers
        if (number.isdigit() or 
            number.isalpha() or 
            number in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x'] or
            number in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'] or
            '.' in number or
            ')' in number):
            return 'ordered'
        
        return 'ordered'  # Default to ordered
    
    def _build_nested_structure(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build nested list structure based on indentation levels and semantic relationships
        
        Args:
            raw_items: List of raw list items with indentation info
            
        Returns:
            List of items with nested structure
        """
        if not raw_items:
            return []
        
        # Sort by line number to maintain document order
        raw_items.sort(key=lambda x: x['line_number'])
        
        # Build hierarchy based on indentation and semantic relationships
        root_items = []
        item_stack = []  # Stack to track current hierarchy
        
        for i, item in enumerate(raw_items):
            current_level = item['indentation']
            
            # Check for semantic nesting (lettered items under numbered items)
            if (i > 0 and current_level == 0 and 
                self._should_nest_semantically(item, raw_items[i-1])):
                # This item should be nested under the previous item
                previous_item = raw_items[i-1]
                
                # Find the appropriate parent for semantic nesting
                parent_item = self._find_semantic_parent(item, raw_items, i, item_stack)
                
                if parent_item:
                    # Add as child of the semantic parent
                    item['parent_id'] = f"{parent_item['line_number']}_{parent_item['indentation']}"
                    parent_item['children'].append(item)
                    item['hierarchy_level'] = parent_item['hierarchy_level'] + 1
                    item['nesting_depth'] = parent_item['nesting_depth'] + 1
                    item['is_nested'] = True
                    parent_item['has_children'] = True
                else:
                    # Fallback: add as root item
                    item['parent_id'] = None
                    root_items.append(item)
                    item['hierarchy_level'] = 1
                    item['nesting_depth'] = 0
                    item['is_nested'] = False
            else:
                # Standard indentation-based nesting
                # Find the appropriate parent based on indentation
                while item_stack and item_stack[-1]['indentation'] >= current_level:
                    item_stack.pop()
                
                # Set parent and add to hierarchy
                if item_stack:
                    parent = item_stack[-1]
                    item['parent_id'] = f"{parent['line_number']}_{parent['indentation']}"
                    parent['children'].append(item)
                    item['hierarchy_level'] = parent['hierarchy_level'] + 1
                    item['nesting_depth'] = parent['nesting_depth'] + 1
                    item['is_nested'] = True
                    parent['has_children'] = True
                else:
                    item['parent_id'] = None
                    root_items.append(item)
                    item['hierarchy_level'] = 1
                    item['nesting_depth'] = 0
                    item['is_nested'] = False
                
                item_stack.append(item)
            
            # Add nested structure info
            item['has_children'] = len(item.get('children', [])) > 0
        
        return root_items
    
    def _should_nest_semantically(self, current_item: Dict[str, Any], previous_item: Dict[str, Any]) -> bool:
        """
        Determine if current item should be nested under previous item based on semantic rules
        
        Args:
            current_item: Current item to check
            previous_item: Previous item to check against
            
        Returns:
            True if current item should be nested under previous item
        """
        current_number = current_item['number']
        previous_number = previous_item['number']
        
        # Get hierarchy levels for comparison
        current_level = self._get_hierarchy_level(current_number)
        previous_level = self._get_hierarchy_level(previous_number)
        
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
        roman_lower = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
        if (current_number.lower() in roman_lower and 
            previous_number.isalpha() and previous_number.islower()):
            return True
        
        # Uppercase letters (A, B, C) should be nested under Roman numerals
        if (current_number.isalpha() and current_number.isupper() and 
            previous_number.lower() in roman_lower):
            return True
        
        # Bullet points should be nested under previous items
        if current_number in ['-', '*', '•']:
            return True
        
        return False
    
    def _find_semantic_parent(self, item: Dict[str, Any], raw_items: List[Dict[str, Any]], 
                             current_index: int, item_stack: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the appropriate semantic parent for an item based on hierarchy levels
        
        Args:
            item: Current item to find parent for
            raw_items: All raw items
            current_index: Current item index
            item_stack: Current item stack
            
        Returns:
            Parent item or None
        """
        current_number = item['number']
        current_level = self._get_hierarchy_level(current_number)
        
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
        
        # If no suitable parent found, look for the most recent item at the same level
        # This handles cases where we need to find a sibling's parent
        for j in range(current_index - 1, -1, -1):
            previous_item = raw_items[j]
            previous_level = self._get_hierarchy_level(previous_item['number'])
            
            if previous_level == current_level:
                # Find the parent of this sibling
                for stack_item in reversed(item_stack):
                    if (stack_item['line_number'] == previous_item['line_number'] and 
                        stack_item['indentation'] == previous_item['indentation']):
                        # Find the parent of this stack item
                        for parent_stack_item in reversed(item_stack):
                            if parent_stack_item.get('children') and stack_item in parent_stack_item['children']:
                                return parent_stack_item
                        break
                break
        
        return None
    
    
    
    def _flatten_nested_items(self, items: List[Dict[str, Any]], level: int = 0) -> List[Dict[str, Any]]:
        """
        Flatten nested list structure into a linear list with hierarchy info
        
        Args:
            items: List of nested items
            level: Current nesting level
            
        Returns:
            Flattened list with hierarchy information
        """
        flattened = []
        
        for item in items:
            # Add current level info
            item_copy = item.copy()
            item_copy['display_level'] = level
            item_copy['indent_prefix'] = '  ' * level
            flattened.append(item_copy)
            
            # Recursively add children
            if item.get('children'):
                child_items = self._flatten_nested_items(item['children'], level + 1)
                flattened.extend(child_items)
        
        return flattened
    
    def _visualize_nested_structure(self, items: List[Dict[str, Any]], level: int = 0) -> str:
        """
        Create a visual representation of the nested list structure
        
        Args:
            items: List of nested items
            level: Current nesting level
            
        Returns:
            String representation of the nested structure
        """
        result = []
        
        for item in items:
            indent = '  ' * level
            list_type = item.get('list_type', 'ordered')
            
            # Handle bullet points properly
            if list_type == 'unordered':
                marker = item['number']  # Use the actual bullet character
            else:
                marker = item['number']
            
            line = f"{indent}{marker} {item['text']}"
            if item.get('has_children'):
                line += f" ({len(item['children'])} children)"
            
            result.append(line)
            
            # Recursively add children
            if item.get('children'):
                child_lines = self._visualize_nested_structure(item['children'], level + 1)
                result.extend(child_lines)
        
        return '\n'.join(result)
    
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
        
        # Handle bullet points - they can be at any level, so we'll treat them as flexible
        if number in ['-', '*', '•']:
            return 2  # Default to second level, but will be adjusted by semantic rules
        
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
    
    def _merge_split_lists(self, components: List[Dict]) -> List[Dict]:
        """
        Merge components that were incorrectly split from complete lists
        
        Args:
            components: List of extracted components
            
        Returns:
            Merged components with complete lists preserved
        """
        if not components:
            return components
        
        merged = []
        current_list_items = []
        list_title = ""
        list_type = ""
        
        # Roman numeral pattern for detecting list items
        roman_pattern = re.compile(r'^\s*\(([ivx]+)\)', re.IGNORECASE)
        number_pattern = re.compile(r'^\s*\((\d+)\)')
        letter_pattern = re.compile(r'^\s*\(([a-z])\)', re.IGNORECASE)
        
        for component in components:
            content = component.get('content', '').strip()
            
            # Check if this component is a list item
            is_list_item = (roman_pattern.match(content) or 
                          number_pattern.match(content) or 
                          letter_pattern.match(content))
            
            if is_list_item:
                # This is a list item, add to current list
                current_list_items.append(component)
                if not list_title:
                    list_title = component.get('title', 'List Items')
                if not list_type:
                    if roman_pattern.match(content):
                        list_type = "roman_objectives"
                    elif number_pattern.match(content):
                        list_type = "numbered_list"
                    else:
                        list_type = "lettered_list"
            else:
                # Not a list item - if we have accumulated list items, merge them
                if current_list_items:
                    merged_list = self._create_merged_list_component(current_list_items, list_title, list_type)
                    merged.append(merged_list)
                    current_list_items = []
                    list_title = ""
                    list_type = ""
                
                # Add the non-list component
                merged.append(component)
        
        # Handle any remaining list items
        if current_list_items:
            merged_list = self._create_merged_list_component(current_list_items, list_title, list_type)
            merged.append(merged_list)
        
        return merged
    
    def _create_merged_list_component(self, list_components: List[Dict], title: str, list_type: str) -> Dict:
        """
        Create a single merged component from multiple list item components
        
        Args:
            list_components: List of individual list item components
            title: Title for the merged list
            list_type: Type of list (roman_objectives, numbered_list, etc.)
            
        Returns:
            Single merged component containing the complete list
        """
        if not list_components:
            return {}
        
        # Combine all content, preserving formatting
        combined_content = []
        for component in list_components:
            content = component.get('content', '').strip()
            if content:
                combined_content.append(content)
        
        # Create merged component
        merged_component = {
            'content': ';\n'.join(combined_content) + '.',  # Join with semicolons for readability
            'type': 'complete_list',
            'section_type': list_type,
            'section_title': title,
            'list_type': list_type,
            'confidence': max(comp.get('confidence', 0.7) for comp in list_components),
            'list_items_count': len(list_components),
            'semantic_theme': 'objectives' if 'objective' in list_type else 'list_content'
        }
        
        return merged_component
    
    def _contains_multiple_list_items(self, content: str) -> bool:
        """
        Check if content contains multiple list items (indicating a complete list)
        
        Args:
            content: Text content to check
            
        Returns:
            True if content contains multiple list items
        """
        # Count Roman numeral list items
        roman_items = len(re.findall(r'\([ivx]+\)', content, re.IGNORECASE))
        if roman_items >= 2:
            return True
        
        # Count numbered list items  
        number_items = len(re.findall(r'\(\d+\)', content))
        if number_items >= 2:
            return True
            
        # Count lettered list items
        letter_items = len(re.findall(r'\([a-z]\)', content, re.IGNORECASE))
        if letter_items >= 2:
            return True
            
        return False
    
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
    
    def enhance_text_extraction(self, text: str, file_type: str) -> Dict[str, Any]:
        """
        Use Google GenAI to enhance text extraction quality
        
        Args:
            text: Document text to enhance
            file_type: Type of file being processed (.pdf, .txt, etc.)
            
        Returns:
            Dictionary with enhanced text and metadata
        """
        if not self.langextract_available or not self.use_langextract_api:
            logger.warning("LangExtract API not available, returning original text")
            return {
                'enhanced_text': text,
                'quality_score': 0.7,
                'processing_notes': 'LangExtract API not available',
                'extraction_method': 'fallback'
            }
        
        try:
            # Import Google GenAI components
            from langchain_google_genai import GoogleGenerativeAI
            import os
            
            # Get API key
            api_key = self._get_google_api_key()
            if not api_key:
                raise ValueError("Google API key not available")
            
            # Initialize Google Generative AI
            genai = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.1,
                max_output_tokens=8192
            )
            
            # Create enhancement prompt
            enhancement_prompt = f"""You are an expert text extraction enhancer. Analyze the following document text and improve its quality by:

1. **Correcting OCR errors** and text extraction artifacts
2. **Preserving document structure** including sections, lists, and formatting
3. **Standardizing formatting** while maintaining semantic meaning
4. **Extracting metadata** about the document (title, author, date, type, purpose)

Original text to enhance:
{text}

Return a JSON response with this structure:
{{
  "enhanced_text": "cleaned and improved text with proper formatting",
  "quality_score": 0.95,
  "processing_notes": "description of improvements made",
  "extracted_metadata": {{
    "title": "document title",
    "author": "author if available",
    "date": "date if available", 
    "document_type": "type of document",
    "purpose": "document purpose/summary",
    "sections": ["list", "of", "section", "titles"],
    "tables": ["list of tables found"],
    "lists": ["list of numbered/bulleted lists found"]
  }}
}}"""

            logger.info("Calling Google GenAI API for text enhancement...")
            response = genai.invoke(enhancement_prompt)
            
            # Parse response
            response_text = response if isinstance(response, str) else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Validate and return result
            enhanced_result = {
                'enhanced_text': result.get('enhanced_text', text),
                'quality_score': result.get('quality_score', 0.8),
                'processing_notes': result.get('processing_notes', 'LangExtract text enhancement completed'),
                'extracted_metadata': result.get('extracted_metadata', {}),
                'extraction_method': 'langextract_enhancement'
            }
            
            logger.info(f"LangExtract text enhancement completed (quality: {enhanced_result['quality_score']})")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"LangExtract text enhancement error: {e}")
            return {
                'enhanced_text': text,
                'quality_score': 0.7,
                'processing_notes': f'LangExtract enhancement failed: {str(e)}',
                'extraction_method': 'fallback'
            }
    
    def extract_structured_data(self, text: str, data_types: List[str]) -> Dict[str, Any]:
        """
        Extract specific structured data types using Google GenAI
        
        Args:
            text: Document text to analyze
            data_types: List of data types to extract (e.g., ['dates', 'names', 'amounts'])
            
        Returns:
            Dictionary with extracted structured data
        """
        if not self.langextract_available or not self.use_langextract_api:
            logger.warning("LangExtract API not available for structured data extraction")
            return {
                'extracted_data': {data_type: [] for data_type in data_types},
                'confidence_scores': {data_type: 0.5 for data_type in data_types},
                'processing_summary': 'LangExtract API not available'
            }
        
        try:
            # Import Google GenAI components
            from langchain_google_genai import GoogleGenerativeAI
            
            # Get API key
            api_key = self._get_google_api_key()
            if not api_key:
                raise ValueError("Google API key not available")
            
            # Initialize Google Generative AI
            genai = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.1,
                max_output_tokens=4096
            )
            
            # Create structured extraction prompt
            data_types_str = "', '".join(data_types)
            extraction_prompt = f"""You are an expert data extraction specialist. Analyze the following document and extract specific types of structured data.

Data types to extract: [{data_types_str}]

For each data type, find all relevant instances in the document and provide confidence scores.

Document text:
{text}

Return a JSON response with this structure:
{{
  "extracted_data": {{
    "dates": ["2024-01-15", "March 2024"],
    "names": ["John Smith", "ABC Corporation"],
    "amounts": ["$1,000", "50%", "100 units"],
    "key_terms": ["important term 1", "key concept 2"],
    "locations": ["New York", "Building A"],
    "emails": ["contact@example.com"],
    "phone_numbers": ["+1-555-0123"]
  }},
  "confidence_scores": {{
    "dates": 0.95,
    "names": 0.90,
    "amounts": 0.85,
    "key_terms": 0.80,
    "locations": 0.75,
    "emails": 0.95,
    "phone_numbers": 0.90
  }},
  "processing_summary": "Found X dates, Y names, Z amounts in the document"
}}

Only include data types that were requested: [{data_types_str}]"""

            logger.info(f"Calling Google GenAI API for structured data extraction: {data_types}")
            response = genai.invoke(extraction_prompt)
            
            # Parse response
            response_text = response if isinstance(response, str) else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Filter to only requested data types
            filtered_data = {}
            filtered_scores = {}
            
            for data_type in data_types:
                filtered_data[data_type] = result.get('extracted_data', {}).get(data_type, [])
                filtered_scores[data_type] = result.get('confidence_scores', {}).get(data_type, 0.7)
            
            extraction_result = {
                'extracted_data': filtered_data,
                'confidence_scores': filtered_scores,
                'processing_summary': result.get('processing_summary', f'Extracted {len(data_types)} data types using LangExtract')
            }
            
            logger.info(f"LangExtract structured data extraction completed for: {data_types}")
            return extraction_result
            
        except Exception as e:
            logger.error(f"LangExtract structured data extraction error: {e}")
            return {
                'extracted_data': {data_type: [] for data_type in data_types},
                'confidence_scores': {data_type: 0.5 for data_type in data_types},
                'processing_summary': f'LangExtract extraction failed: {str(e)}'
            }
    
    def generate_document_summary(self, text: str, summary_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate document summaries using Google GenAI
        
        Args:
            text: Document text to summarize
            summary_type: Type of summary (comprehensive, brief, executive, technical)
            
        Returns:
            Dictionary with document summary
        """
        if not self.langextract_available or not self.use_langextract_api:
            logger.warning("LangExtract API not available for document summarization")
            return {
                'summary': 'LangExtract API not available for summarization',
                'key_points': [],
                'summary_type': summary_type,
                'confidence': 0.5
            }
        
        try:
            # Import Google GenAI components
            from langchain_google_genai import GoogleGenerativeAI
            
            # Get API key
            api_key = self._get_google_api_key()
            if not api_key:
                raise ValueError("Google API key not available")
            
            # Initialize Google Generative AI
            genai = GoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.2,
                max_output_tokens=2048
            )
            
            # Create summary prompt based on type
            if summary_type == "brief":
                summary_instruction = "Create a brief 2-3 sentence summary highlighting the main purpose and key points."
            elif summary_type == "executive":
                summary_instruction = "Create an executive summary suitable for business stakeholders, focusing on decisions, outcomes, and implications."
            elif summary_type == "technical":
                summary_instruction = "Create a technical summary focusing on specifications, methodologies, and technical details."
            else:  # comprehensive
                summary_instruction = "Create a comprehensive summary covering all major topics, sections, and important details."
            
            summary_prompt = f"""You are an expert document analyzer. {summary_instruction}

Document text:
{text}

Return a JSON response with this structure:
{{
  "summary": "comprehensive summary text",
  "key_points": [
    "key point 1",
    "key point 2", 
    "key point 3"
  ],
  "summary_type": "{summary_type}",
  "confidence": 0.95,
  "word_count": 150,
  "main_topics": ["topic 1", "topic 2", "topic 3"]
}}"""

            logger.info(f"Calling Google GenAI API for document summarization: {summary_type}")
            response = genai.invoke(summary_prompt)
            
            # Parse response
            response_text = response if isinstance(response, str) else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            summary_result = {
                'summary': result.get('summary', 'Summary generation failed'),
                'key_points': result.get('key_points', []),
                'summary_type': summary_type,
                'confidence': result.get('confidence', 0.8),
                'word_count': result.get('word_count', len(result.get('summary', '').split())),
                'main_topics': result.get('main_topics', [])
            }
            
            logger.info(f"LangExtract document summarization completed: {summary_type}")
            return summary_result
            
        except Exception as e:
            logger.error(f"LangExtract document summarization error: {e}")
            return {
                'summary': f'Summarization failed: {str(e)}',
                'key_points': [],
                'summary_type': summary_type,
                'confidence': 0.5
            }
    
    def _get_google_api_key(self) -> Optional[str]:
        """
        Get Google API key from AWS Secrets Manager or environment variables
        
        Returns:
            Google API key or None if not found
        """
        # Try AWS Secrets Manager first
        try:
            from aws_secrets import get_google_api_key
            api_key = get_google_api_key()
            if api_key:
                return api_key
        except Exception:
            pass
        
        # Fallback to environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv('.env.local')
        except ImportError:
            pass
        
        import os
        return os.getenv('GOOGLE_API_KEY')

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
