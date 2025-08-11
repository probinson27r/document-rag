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
            r'^(\d+)\.\s+(.+)$',          # 1. First objective
            r'^\((\d+)\)\s+(.+)$',        # (1) First objective
            r'^(\d+\))\s+(.+)$',          # 1) First objective
            r'^([a-z])\.\s+(.+)$',        # a. Sub-objective
            r'^\(([a-z])\)\s+(.+)$',      # (a) Sub-objective
            r'^([A-Z])\.\s+(.+)$',        # A. Major objective
            r'^\(([A-Z])\)\s+(.+)$',      # (A) Major objective
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
        Chunk a section while preserving its structure
        
        Args:
            section: Section to chunk
            
        Returns:
            List of chunks for this section
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
            sub_chunks = self._split_large_section(section)
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
        Special chunking for objectives sections to preserve complete lists
        
        Args:
            section: Objectives section to chunk
            
        Returns:
            List of chunks preserving complete objectives
        """
        chunks = []
        
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
                # Split large section into smaller chunks
                return self._split_large_section(section)
        
        logger.info(f"Found {len(list_items)} list items in objectives section")
        
        # Group list items by their hierarchy level
        grouped_items = self._group_list_items_by_hierarchy(list_items)
        
        # Create chunks that preserve complete groups
        current_chunk_content = f"## {section.number} {section.title}\n\n"
        current_items = []
        
        for group in grouped_items:
            group_content = self._format_list_group(group)
            
            # Check if adding this group would exceed chunk size
            if len(current_chunk_content) + len(group_content) > self.max_chunk_size and current_items:
                # Create chunk with current items
                chunk = Chunk(
                    content=current_chunk_content.strip(),
                    chunk_id=f"objectives_{section.number}_{len(chunks)}",
                    section_number=section.number,
                    section_title=section.title,
                    chunk_type="objectives_list",
                    semantic_theme="objectives",
                    list_items=current_items,
                    start_position=0,
                    end_position=len(current_chunk_content)
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_content = f"## {section.number} {section.title} (continued)\n\n"
                current_items = []
            
            # Add group to current chunk
            current_chunk_content += group_content + "\n\n"
            current_items.extend(group)
        
        # Add final chunk if there's content
        if current_items:
            chunk = Chunk(
                content=current_chunk_content.strip(),
                chunk_id=f"objectives_{section.number}_{len(chunks)}",
                section_number=section.number,
                section_title=section.title,
                chunk_type="objectives_list",
                semantic_theme="objectives",
                list_items=current_items,
                start_position=0,
                end_position=len(current_chunk_content)
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
    
    def _split_large_section(self, section: Section) -> List[Chunk]:
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
