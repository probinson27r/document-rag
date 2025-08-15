#!/usr/bin/env python3
"""
Semantic Chunking Module for Document RAG System

This module implements intelligent semantic chunking that preserves complete sections,
lists, and hierarchical structures. It's specifically designed to solve issues with
retrieving complete lists of objectives, items, or other enumerated content.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Section:
    """Represents a document section with its content and metadata"""
    number: str
    title: str
    content: str
    start_line: int
    end_line: int
    subsections: List['Section']
    list_items: List[Dict[str, Any]]

@dataclass
class Chunk:
    """Represents a semantic chunk with metadata"""
    content: str
    chunk_id: str
    section_number: str
    section_title: str
    chunk_type: str
    semantic_theme: str
    list_items: List[Dict[str, Any]]
    start_position: int
    end_position: int

class SemanticChunker:
    """
    Intelligent semantic chunking that preserves complete sections and lists
    """
    
    def __init__(self, 
                 max_chunk_size: int = 2000,
                 min_chunk_size: int = 200,
                 preserve_lists: bool = True,
                 preserve_sections: bool = True):
        
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.preserve_lists = preserve_lists
        self.preserve_sections = preserve_sections
        
        # Patterns for detecting sections and lists
        self.section_patterns = [
            r'^##\s*(\d+\.\d+)\s+(.+)$',  # ## 3.2 Objectives
            r'^(\d+\.\d+)\s+(.+)$',       # 3.2 Objectives
            r'^Section\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',  # Section 3.2: Objectives
            r'^Clause\s+(\d+\.\d+)\s*[:.]?\s*(.+)$',   # Clause 3.2: Objectives
        ]
        
        self.list_patterns = [
            r'^(\d+)\.\s+([A-Za-z].*)',          # 1. First objective (must have text)
            r'^(\d+)\.\s+(\(.*)',                # 1. First objective (must have parentheses)
            r'^(\d+\))\s+([A-Za-z].*)',          # 1) First objective (must have text)
            r'^([a-z])\.\s+([A-Za-z].*)',        # a. Sub-objective (must have text)
            r'^\(([a-z])\)\s+([A-Za-z].*)',      # (a) Sub-objective (must have text)
            r'^([A-Z])\.\s+([A-Za-z].*)',        # A. Major objective (must have text)
            r'^\(([A-Z])\)\s+([A-Za-z].*)',      # (A) Major objective (must have text)
        ]
        
        self.objectives_keywords = [
            'objectives', 'objective', 'goals', 'aims', 'purposes',
            'targets', 'outcomes', 'results', 'deliverables'
        ]
    
    def chunk_document(self, text: str) -> List[Chunk]:
        """
        Chunk document using semantic analysis to preserve complete sections and lists
        
        Args:
            text: Document text to chunk
            
        Returns:
            List of semantic chunks
        """
        logger.info("Starting semantic chunking of document")
        
        # Split text into lines for analysis
        lines = text.split('\n')
        
        # Identify sections and their boundaries
        sections = self._identify_sections(lines)
        logger.info(f"Identified {len(sections)} sections")
        
        # Process each section into chunks
        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)
        
        # If no sections found, use fallback chunking
        if not chunks:
            logger.info("No sections found, using fallback chunking")
            chunks = self._fallback_chunking(text)
        
        logger.info(f"Created {len(chunks)} semantic chunks")
        return chunks
    
    def _identify_sections(self, lines: List[str]) -> List[Section]:
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
                    current_section.content = '\n'.join(current_content)
                    current_section.end_line = i - 1
                    sections.append(current_section)
                
                # Start new section
                section_number, section_title = section_match
                current_section = Section(
                    number=section_number,
                    title=section_title.strip(),
                    content='',
                    start_line=i,
                    end_line=i,
                    subsections=[],
                    list_items=[]
                )
                current_content = []
                current_start_line = i
            else:
                # Add line to current section content
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section:
            current_section.content = '\n'.join(current_content)
            current_section.end_line = len(lines) - 1
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
    
    def _chunk_section(self, section: Section) -> List[Chunk]:
        """
        Chunk a section while preserving table content
        
        Args:
            section: Section to chunk
            
        Returns:
            List of chunks
        """
        # Check if section contains table content
        if self._has_table_content(section.content):
            # Keep entire section as one chunk if it contains tables
            if len(section.content) <= self.max_chunk_size * 2:  # Allow larger chunks for tables
                chunk = Chunk(
                    content=section.content,
                    chunk_id=f"section_{section.number}_with_table",
                    section_number=section.number,
                    section_title=section.title,
                    chunk_type="complete_section_with_table",
                    semantic_theme=self._extract_semantic_theme(section.content),
                    list_items=self._extract_list_items(section.content),
                    start_position=0,
                    end_position=len(section.content)
                )
                return [chunk]
        
        # Apply normal chunking logic for non-table sections
        return self._chunk_section_normal(section)
    
    def _has_table_content(self, content: str) -> bool:
        """
        Check if content contains table-like data
        
        Args:
            content: Content to check
            
        Returns:
            True if content contains table indicators
        """
        # Check for table indicators
        table_indicators = [
            'service level',  # Service level content
            'kpi',  # Key performance indicators
            'metric',  # Metrics
            'requirement',  # Requirements
            'bundle',  # Service bundle references
            'availability',  # Availability metrics
            'uptime',  # Uptime metrics
            'performance',  # Performance metrics
            'report',  # Reporting requirements
            'frequency',  # Measurement frequency
            'mechanism',  # Measurement mechanism
            'ref.',  # Reference numbers
            '%',  # Percentage metrics
            'hours',  # Time-based metrics
            'days'  # Time-based metrics
        ]
        return any(indicator in content.lower() for indicator in table_indicators)
    
    def _chunk_section_normal(self, section: Section) -> List[Chunk]:
        """
        Normal chunking logic for non-table sections
        
        Args:
            section: Section to chunk
            
        Returns:
            List of chunks
        """
        chunks = []
        
        # Check if this is an objectives section
        is_objectives_section = self._is_objectives_section(section)
        
        if is_objectives_section:
            logger.info(f"Processing objectives section: {section.number}")
            return self._chunk_objectives_section(section)
        
        # Check if section is small enough to keep as one chunk
        if len(section.content) <= self.max_chunk_size:
            chunk = Chunk(
                content=f"## {section.number} {section.title}\n\n{section.content}",
                chunk_id=f"section_{section.number}",
                section_number=section.number,
                section_title=section.title,
                chunk_type="complete_section",
                semantic_theme=self._extract_semantic_theme(section.content),
                list_items=self._extract_list_items(section.content),
                start_position=0,
                end_position=len(section.content)
            )
            chunks.append(chunk)
        else:
            # Split large section into smaller chunks
            sub_chunks = self._chunk_large_section(section)
            chunks.extend(sub_chunks)
        
        return chunks
    
    def _is_objectives_section(self, section: Section) -> bool:
        """
        Check if a section is an objectives section
        
        Args:
            section: Section to check
            
        Returns:
            True if this is an objectives section
        """
        # Check section title
        title_lower = section.title.lower()
        for keyword in self.objectives_keywords:
            if keyword in title_lower:
                return True
        
        # Check section content for objectives patterns
        content_lower = section.content.lower()
        objectives_patterns = [
            r'\bobjectives?\b',
            r'\bgoals?\b',
            r'\baims?\b',
            r'\bpurposes?\b'
        ]
        
        for pattern in objectives_patterns:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def _chunk_objectives_section(self, section: Section) -> List[Chunk]:
        """
        Special handling for objectives sections to preserve complete numbered lists
        """
        # Extract all list items from the section
        list_items = self._extract_list_items(section.content)
        
        if not list_items:
            # No list items found, use regular section chunking
            if len(section.content) <= self.max_chunk_size:
                chunk = Chunk(
                    content=f"## {section.number} {section.title}\n\n{section.content}",
                    chunk_id=f"section_{section.number}",
                    section_number=section.number,
                    section_title=section.title,
                    chunk_type="complete_section",
                    semantic_theme=self._extract_semantic_theme(section.content),
                    list_items=self._extract_list_items(section.content),
                    start_position=0,
                    end_position=len(section.content)
                )
                return [chunk]
            else:
                # Use regular chunking for large sections without lists
                return self._chunk_large_section(section)
        
        # For objectives sections with lists, ensure the entire list is preserved
        # Check if the content fits in a single chunk
        full_content = f"## {section.number} {section.title}\n\n{section.content}"
        
        if len(full_content) <= self.max_chunk_size:
            # Keep entire objectives section in one chunk
            chunk = Chunk(
                content=full_content,
                chunk_id=f"section_{section.number}_complete",
                section_number=section.number,
                section_title=section.title,
                chunk_type="complete_objectives_section",
                semantic_theme="objectives",
                list_items=list_items,
                start_position=0,
                end_position=len(section.content)
            )
            return [chunk]
        else:
            # If the objectives section is too large, try to split intelligently
            # Look for natural break points that don't break the numbered list
            return self._chunk_large_objectives_section(section, list_items)
    
    def _chunk_large_objectives_section(self, section: Section, list_items: List[str]) -> List[Chunk]:
        """
        Handle large objectives sections by finding natural break points
        that don't break numbered lists
        """
        chunks = []
        lines = section.content.split('\n')
        current_chunk_lines = []
        current_chunk_size = 0
        
        # Add section header
        header = f"## {section.number} {section.title}\n\n"
        current_chunk_lines.append(header)
        current_chunk_size += len(header)
        
        in_numbered_list = False
        list_start_line = -1
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            # Check if this line starts a numbered list
            if self._is_numbered_list_start(line):
                if not in_numbered_list:
                    in_numbered_list = True
                    list_start_line = i
                # Continue with current chunk to keep list together
            
            # Check if this line ends a numbered list
            elif in_numbered_list and not self._is_numbered_list_continuation(line):
                in_numbered_list = False
                # Add the complete list to current chunk
                for j in range(list_start_line, i + 1):
                    current_chunk_lines.append(lines[j])
                    current_chunk_size += len(lines[j]) + 1
                list_start_line = -1
            
            # If we're in a numbered list, keep adding to current chunk
            elif in_numbered_list:
                current_chunk_lines.append(line)
                current_chunk_size += line_size
                continue
            
            # Regular line processing
            if current_chunk_size + line_size > self.max_chunk_size and current_chunk_lines:
                # Create chunk and start new one
                chunk_content = '\n'.join(current_chunk_lines)
                chunk = Chunk(
                    content=chunk_content,
                    chunk_id=f"section_{section.number}_part_{len(chunks)}",
                    section_number=section.number,
                    section_title=section.title,
                    chunk_type="objectives_section_part",
                    semantic_theme="objectives",
                    list_items=self._extract_list_items(chunk_content),
                    start_position=0,
                    end_position=len(chunk_content)
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_lines = [header]
                current_chunk_size = len(header)
            
            current_chunk_lines.append(line)
            current_chunk_size += line_size
        
        # Add final chunk
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            chunk = Chunk(
                content=chunk_content,
                chunk_id=f"section_{section.number}_part_{len(chunks)}",
                section_number=section.number,
                section_title=section.title,
                chunk_type="objectives_section_part",
                semantic_theme="objectives",
                list_items=self._extract_list_items(chunk_content),
                start_position=0,
                end_position=len(chunk_content)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_list_items(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract list items from content
        
        Args:
            content: Content to extract list items from
            
        Returns:
            List of list items with metadata
        """
        items = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for list patterns
            for pattern in self.list_patterns:
                match = re.match(pattern, line)
                if match:
                    number, text = match.groups()
                    items.append({
                        'number': number,
                        'text': text.strip(),
                        'line_number': i,
                        'pattern': pattern,
                        'hierarchy_level': self._get_hierarchy_level(number)
                    })
                    break
        
        return items
    
    def _get_hierarchy_level(self, number: str) -> int:
        """
        Determine hierarchy level of a list item
        
        Args:
            number: List item number/marker
            
        Returns:
            Hierarchy level (1 = top level, 2 = sub-level, etc.)
        """
        if number.isdigit():
            return 1
        elif number.isupper():
            return 2
        elif number.islower():
            return 3
        else:
            return 1
    
    def _group_list_items_by_hierarchy(self, items: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group list items by their hierarchy level
        
        Args:
            items: List items to group
            
        Returns:
            Groups of related list items
        """
        if not items:
            return []
        
        groups = []
        current_group = []
        current_level = items[0]['hierarchy_level']
        
        for item in items:
            # If this is a top-level item and we have a current group, start new group
            if item['hierarchy_level'] == 1 and current_group:
                groups.append(current_group)
                current_group = []
            
            current_group.append(item)
            current_level = item['hierarchy_level']
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _format_list_group(self, group: List[Dict[str, Any]]) -> str:
        """
        Format a group of list items as text
        
        Args:
            group: Group of list items
            
        Returns:
            Formatted text
        """
        formatted_items = []
        
        for item in group:
            number = item['number']
            text = item['text']
            
            # Format based on hierarchy level
            if item['hierarchy_level'] == 1:
                formatted_items.append(f"{number}. {text}")
            elif item['hierarchy_level'] == 2:
                formatted_items.append(f"  {number}. {text}")
            elif item['hierarchy_level'] == 3:
                formatted_items.append(f"    {number}. {text}")
            else:
                formatted_items.append(f"{number}. {text}")
        
        return '\n'.join(formatted_items)
    
    def _extract_semantic_theme(self, content: str) -> str:
        """
        Extract semantic theme from content
        
        Args:
            content: Content to analyze
            
        Returns:
            Semantic theme
        """
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in self.objectives_keywords):
            return "objectives"
        elif 'scope' in content_lower:
            return "scope"
        elif 'definitions' in content_lower or 'terms' in content_lower:
            return "definitions"
        elif 'obligations' in content_lower or 'responsibilities' in content_lower:
            return "obligations"
        else:
            return "general"
    
    def _chunk_large_section(self, section: Section) -> List[Chunk]:
        """
        Split a large section into smaller chunks
        
        Args:
            section: Section to split
            
        Returns:
            List of chunks
        """
        chunks = []
        content = section.content
        lines = content.split('\n')
        
        current_chunk = f"## {section.number} {section.title}\n\n"
        current_start = 0
        
        for i, line in enumerate(lines):
            # Check if adding this line would exceed chunk size
            if len(current_chunk) + len(line) > self.max_chunk_size and current_chunk.strip():
                # Create chunk
                chunk = Chunk(
                    content=current_chunk.strip(),
                    chunk_id=f"section_{section.number}_part_{len(chunks)}",
                    section_number=section.number,
                    section_title=section.title,
                    chunk_type="section_part",
                    semantic_theme=self._extract_semantic_theme(current_chunk),
                    list_items=self._extract_list_items(current_chunk),
                    start_position=current_start,
                    end_position=len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = f"## {section.number} {section.title} (continued)\n\n"
                current_start = len(current_chunk)
            
            current_chunk += line + '\n'
        
        # Add final chunk
        if current_chunk.strip():
            chunk = Chunk(
                content=current_chunk.strip(),
                chunk_id=f"section_{section.number}_part_{len(chunks)}",
                section_number=section.number,
                section_title=section.title,
                chunk_type="section_part",
                semantic_theme=self._extract_semantic_theme(current_chunk),
                list_items=self._extract_list_items(current_chunk),
                start_position=current_start,
                end_position=len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _fallback_chunking(self, text: str) -> List[Chunk]:
        """
        Fallback chunking when no sections are detected
        
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
            chunk = Chunk(
                content=chunk_content,
                chunk_id=f"fallback_chunk_{i+1}",
                section_number="",
                section_title="",
                chunk_type="fallback",
                semantic_theme=self._extract_semantic_theme(chunk_content),
                list_items=self._extract_list_items(chunk_content),
                start_position=text.find(chunk_content),
                end_position=text.find(chunk_content) + len(chunk_content)
            )
            chunks.append(chunk)
        
        return chunks

    def _is_numbered_list_start(self, line: str) -> bool:
        """
        Check if a line starts a numbered list
        """
        line = line.strip()
        # Match patterns like "i.", "ii.", "iii.", "1.", "2.", "3.", etc.
        patterns = [
            r'^[ivx]+\.',  # Roman numerals
            r'^[0-9]+\.',  # Arabic numerals
            r'^\([ivx]+\)',  # Roman numerals in parentheses
            r'^\([0-9]+\)',  # Arabic numerals in parentheses
            r'^[a-z]\)',    # Lowercase letters
            r'^[A-Z]\)',    # Uppercase letters
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _is_numbered_list_continuation(self, line: str) -> bool:
        """
        Check if a line continues a numbered list (indented content)
        """
        line = line.strip()
        # Empty lines don't break lists
        if not line:
            return True
        
        # If it starts with a number/letter pattern, it's a new list item
        if self._is_numbered_list_start(line):
            return True
        
        # If it's indented or starts with common list continuation patterns
        if line.startswith(' ') or line.startswith('\t'):
            return True
        
        # If it's a continuation line (doesn't start with a new list item)
        return not self._is_numbered_list_start(line)

# Example usage and testing
if __name__ == "__main__":
    # Test the semantic chunker
    chunker = SemanticChunker()
    
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
    
    print("Semantic Chunking Results:")
    print("=" * 50)
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk.chunk_id}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Section: {chunk.section_number} - {chunk.section_title}")
        print(f"List Items: {len(chunk.list_items)}")
        print(f"Content Preview: {chunk.content[:100]}...")
        
        if chunk.list_items:
            print("List Items Found:")
            for item in chunk.list_items:
                print(f"  {item['number']}. {item['text'][:50]}...")
