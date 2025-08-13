#!/usr/bin/env python3
"""
GPT-4 Intelligent Chunking Module

This module provides GPT-4 powered document chunking that:
1. Intelligently splits documents based on semantic meaning
2. Preserves document structure and relationships
3. Optimizes chunk sizes for RAG performance
4. Maintains context across chunk boundaries
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import openai
import anthropic
import requests
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT4Chunker:
    """GPT-4 powered intelligent document chunking"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 private_gpt4_url: Optional[str] = None,
                 private_gpt4_key: Optional[str] = None,
                 default_chunk_size: int = 1000,
                 max_chunk_size: int = 2000,
                 min_chunk_size: int = 200):
        
        self.openai_client = None
        self.claude_client = None
        self.private_gpt4_url = private_gpt4_url
        self.private_gpt4_key = private_gpt4_key
        self.default_chunk_size = default_chunk_size
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        # Initialize OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
            logger.info("OpenAI GPT-4 chunking client initialized")
        
        # Initialize Claude client
        if anthropic_api_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("Claude chunking client initialized")
        
        if private_gpt4_url and private_gpt4_key:
            logger.info("Private GPT-4 chunking client configured")
        
        if not any([self.openai_client, self.claude_client, private_gpt4_url]):
            logger.warning("No GPT-4 clients available - chunking will use fallback methods")
    
    def chunk_document_with_gpt4(self, 
                                text: str, 
                                document_type: str = "general",
                                preserve_structure: bool = True,
                                 model: str = "gpt-5",
                                prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """Chunk document using GPT-4 with intelligent semantic splitting"""
        try:
            # Prioritize Private GPT-4 if available and preferred
            if prefer_private_gpt4 and self.private_gpt4_url and self.private_gpt4_key:
                logger.info("Using Private GPT-4 for chunking")
                return self._chunk_with_private_gpt4(text, document_type, preserve_structure, model)
            elif model.startswith("gpt-") and self.openai_client:
                return self._chunk_with_openai(text, document_type, preserve_structure, model)
            elif model.startswith("claude") and self.claude_client:
                return self._chunk_with_claude(text, document_type, preserve_structure, model)
            elif self.private_gpt4_url and self.private_gpt4_key:
                # Fallback to Private GPT-4 if other providers fail
                logger.info("Falling back to Private GPT-4 for chunking")
                return self._chunk_with_private_gpt4(text, document_type, preserve_structure, model)
            else:
                logger.warning(f"Model {model} not available, using fallback chunking")
                return self._fallback_chunking(text, document_type)
                
        except Exception as e:
            logger.error(f"Error in GPT-4 chunking: {e}")
            return self._fallback_chunking(text, document_type)
    
    def _chunk_with_openai(self, text: str, document_type: str, preserve_structure: bool, model: str) -> Dict[str, Any]:
        """Chunk using OpenAI GPT-4"""
        try:
            chunking_prompt = self._create_chunking_prompt(text, document_type, preserve_structure)
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": """You are an expert document structure analyzer using LangExtract principles. 
            
Extract the complete text from this contract document while preserving the exact hierarchical structure and numbering system. Maintain all:

1. Section numbers (e.g., 1, 2, 3...)
2. Subsection numbers (e.g., 1.1, 1.2, 1.3...)
3. Alphabetical subdivisions (e.g., (a), (b), (c)...)
4. Roman numeral subdivisions (e.g., (i), (ii), (iii)...)
5. Any mixed numbering schemes

Requirements:
- Preserve exact spacing and indentation
- Maintain all punctuation marks
- Keep original paragraph breaks
- Include all headers, subheaders, and section titles
- Preserve any special formatting indicators (bold, italics markers)
- Maintain cross-references exactly as written
- Include all footnotes and their reference markers

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
}"""},
                    {"role": "user", "content": chunking_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            return self._parse_chunking_result(result, text)
                
        except Exception as e:
            logger.error(f"OpenAI chunking error: {e}")
            return self._fallback_chunking(text, document_type)
    
    def _chunk_with_claude(self, text: str, document_type: str, preserve_structure: bool, model: str) -> Dict[str, Any]:
        """Chunk using Claude"""
        try:
            chunking_prompt = self._create_chunking_prompt(text, document_type, preserve_structure)
            
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": f"{chunking_prompt}\n\nPlease return the chunking result in JSON format."}
                ]
            )
            
            result = response.content[0].text
            return self._parse_chunking_result(result, text)
                
        except Exception as e:
            logger.error(f"Claude chunking error: {e}")
            return self._fallback_chunking(text, document_type)
    
    def _chunk_with_private_gpt4(self, text: str, document_type: str, preserve_structure: bool, model: str) -> Dict[str, Any]:
        """Chunk using Private GPT-4"""
        try:
            chunking_prompt = self._create_chunking_prompt(text, document_type, preserve_structure)
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.private_gpt4_key
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": "You are an expert document chunking specialist. Split documents into optimal chunks for RAG systems while preserving semantic meaning and document structure."},
                    {"role": "user", "content": chunking_prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.1
            }
            
            response = requests.post(self.private_gpt4_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            return self._parse_chunking_result(content, text)
                
        except Exception as e:
            logger.error(f"Private GPT-4 chunking error: {e}")
            return self._fallback_chunking(text, document_type)
    
    def _create_chunking_prompt(self, text: str, document_type: str, preserve_structure: bool) -> str:
        """Create a specialized chunking prompt based on document type"""
        
        # Calculate text length and suggest appropriate number of chunks
        text_length = len(text)
        suggested_chunks = max(2, min(8, text_length // self.default_chunk_size + 1))
        
        type_instructions = {
            "legal": """
            LEGAL DOCUMENT CHUNKING RULES:
            - Preserve complete legal clauses and sections
            - Keep related subsections together
            - Maintain cross-references within chunks
            - Preserve numbered lists and hierarchical structure
            - Split by sections, subsections, or logical boundaries
            """,
            "technical": """
            TECHNICAL DOCUMENT CHUNKING RULES:
            - Keep code blocks and examples together
            - Preserve technical specifications
            - Maintain step-by-step procedures
            - Split by topics, procedures, or technical sections
            """,
            "general": """
            GENERAL DOCUMENT CHUNKING RULES:
            - Keep complete sentences and paragraphs
            - Preserve logical flow and context
            - Maintain document structure
            - Split by topics, paragraphs, or natural boundaries
            """
        }
        
        chunking_rules = type_instructions.get(document_type, type_instructions["general"])
        
        prompt = f"""You are an expert document chunking specialist. Analyze the following text and split it into {suggested_chunks} coherent, semantically meaningful chunks for RAG (Retrieval-Augmented Generation) systems.

        {chunking_rules}
        
        CHUNKING REQUIREMENTS:
        - Text length: {text_length} characters
        - Target chunk size: {self.default_chunk_size} characters
        - Maximum chunk size: {self.max_chunk_size} characters  
        - Minimum chunk size: {self.min_chunk_size} characters
        - Create approximately {suggested_chunks} chunks
        - Preserve structure: {preserve_structure}
        - Each chunk should be self-contained and coherent
        - Avoid cutting sentences or important information mid-way
        - Maintain logical flow between chunks
        
        DOCUMENT TEXT TO CHUNK:
        {text}
        
        Analyze the text and create {suggested_chunks} optimal chunks. Return the result as valid JSON:

        {{
            "chunks": [
                {{
                    "chunk_id": "chunk_1",
                    "content": "First chunk content with complete sentences and context",
                    "start_position": 0,
                    "end_position": 300,
                    "chunk_type": "header|section|paragraph|list|definition",
                    "section_number": "1",
                    "section_title": "Section Title if applicable",
                    "semantic_theme": "main topic or theme of this chunk",
                    "quality_score": 0.9
                }},
                {{
                    "chunk_id": "chunk_2", 
                    "content": "Second chunk content with complete sentences and context",
                    "start_position": 300,
                    "end_position": 600,
                    "chunk_type": "section|paragraph|list",
                    "section_number": "2",
                    "section_title": "Section Title if applicable",
                    "semantic_theme": "main topic or theme of this chunk",
                    "quality_score": 0.9
                }}
            ],
            "summary": {{
                "total_chunks": {suggested_chunks},
                "average_chunk_size": 500,
                "semantic_coherence_score": 0.92,
                "structure_preservation_score": 0.88
            }}
        }}
        
        CRITICAL INSTRUCTIONS:
        1. Return ONLY valid JSON - no markdown, no code blocks, no additional text
        2. Start response with {{ and end with }}
        3. Ensure each chunk has meaningful, complete content
        4. Make sure chunk content includes full sentences
        5. Create exactly {suggested_chunks} chunks or more if text requires it
        6. Never return empty chunks
        """
        
        return prompt
    
    def _parse_chunking_result(self, result: str, original_text: str) -> Dict[str, Any]:
        """Parse the GPT-4 chunking result with enhanced validation"""
        # Clean the result to handle markdown formatting
        cleaned_result = self._clean_json_response(result)
        
        try:
            parsed_result = json.loads(cleaned_result)
            chunks = parsed_result.get('chunks', [])
            
            if not chunks:
                logger.warning("No chunks found in GPT-4 response, using fallback")
                return self._fallback_chunking(original_text, "general")
            
            validated_chunks = []
            
            for i, chunk in enumerate(chunks):
                # Validate chunk content
                content = chunk.get('content', '').strip()
                if not content:
                    logger.warning(f"Empty content in chunk {i+1}, skipping")
                    continue
                
                # Ensure content is meaningful (at least 10 characters)
                if len(content) < 10:
                    logger.warning(f"Chunk {i+1} too short ({len(content)} chars), skipping")
                    continue
                
                validated_chunk = {
                    'chunk_id': chunk.get('chunk_id', f'chunk_{i+1}'),
                    'content': content,
                    'start_position': chunk.get('start_position', 0),
                    'end_position': chunk.get('end_position', len(content)),
                    'chunk_type': chunk.get('chunk_type', 'paragraph'),
                    'section_number': str(chunk.get('section_number', '')),
                    'section_title': str(chunk.get('section_title', '')),
                    'semantic_theme': str(chunk.get('semantic_theme', '')),
                    'quality_score': float(chunk.get('quality_score', 0.8)),
                    'gpt4_chunked': True
                }
                
                validated_chunks.append(validated_chunk)
            
            # Ensure we have at least some valid chunks
            if not validated_chunks:
                logger.warning("No valid chunks after validation, using fallback")
                return self._fallback_chunking(original_text, "general")
            
            # If we have less than 2 chunks for a reasonably long text, try to improve
            if len(validated_chunks) < 2 and len(original_text) > self.default_chunk_size:
                logger.info(f"Only {len(validated_chunks)} chunks generated for {len(original_text)} chars text, enhancing...")
                enhanced_chunks = self._enhance_chunk_count(validated_chunks, original_text)
                if enhanced_chunks:
                    validated_chunks = enhanced_chunks
            
            summary = parsed_result.get('summary', {})
            summary['total_chunks'] = len(validated_chunks)
            summary['gpt4_chunking_used'] = True
            summary['validation_passed'] = True
            
            logger.info(f"Successfully parsed {len(validated_chunks)} valid chunks from GPT-4 response")
            
            return {
                'success': True,
                'chunks': validated_chunks,
                'summary': summary,
                'chunking_method': 'gpt4_intelligent'
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GPT-4 chunking result as JSON: {e}")
            logger.debug(f"Raw result: {result[:200]}...")
            logger.debug(f"Cleaned result: {cleaned_result[:200]}...")
            return self._fallback_chunking(original_text, "general")
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response to handle markdown formatting"""
        import re
        
        # Remove markdown code block formatting
        # Handle ```json ... ``` or ``` ... ```
        json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_block_pattern, response, re.DOTALL)
        
        if matches:
            # Use the first JSON block found
            cleaned = matches[0].strip()
            logger.debug("Extracted JSON from markdown code block")
            return cleaned
        
        # Check if response starts with ```json and ends with ```
        if response.strip().startswith('```json') and response.strip().endswith('```'):
            # Extract content between ```json and ```
            content = response.strip()
            start_idx = content.find('```json') + 7
            end_idx = content.rfind('```')
            if start_idx < end_idx:
                cleaned = content[start_idx:end_idx].strip()
                logger.debug("Extracted JSON from ```json code block")
                return cleaned
        
        # Check if response starts with ``` and ends with ```
        if response.strip().startswith('```') and response.strip().endswith('```'):
            # Extract content between ``` and ```
            content = response.strip()
            start_idx = content.find('```') + 3
            end_idx = content.rfind('```')
            if start_idx < end_idx:
                cleaned = content[start_idx:end_idx].strip()
                logger.debug("Extracted JSON from code block")
                return cleaned
        
        # If no markdown blocks, try to extract JSON object
        json_object_pattern = r'\{.*\}'
        matches = re.findall(json_object_pattern, response, re.DOTALL)
        
        if matches:
            # Use the largest JSON object found
            largest_match = max(matches, key=len)
            logger.debug("Extracted JSON object from response")
            return largest_match
        
        # If no JSON found, return the original response
        logger.debug("No JSON formatting detected, using original response")
        return response.strip()
    
    def _enhance_chunk_count(self, existing_chunks: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
        """Enhance chunk count by splitting large chunks when too few chunks are generated"""
        if not existing_chunks:
            return existing_chunks
        
        enhanced_chunks = []
        
        for chunk in existing_chunks:
            content = chunk['content']
            
            # If chunk is very large, try to split it
            if len(content) > self.max_chunk_size:
                # Split by natural boundaries
                split_chunks = self._split_large_chunk(content, chunk)
                enhanced_chunks.extend(split_chunks)
            else:
                enhanced_chunks.append(chunk)
        
        # If we still have too few chunks for long text, use fallback splitting
        if len(enhanced_chunks) < 2 and len(original_text) > self.default_chunk_size * 2:
            logger.info("Still too few chunks, using hybrid approach")
            return self._hybrid_chunking(original_text, enhanced_chunks)
        
        return enhanced_chunks
    
    def _split_large_chunk(self, content: str, original_chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a large chunk into smaller, more manageable chunks"""
        # Try to split by natural boundaries: paragraphs, sentences, etc.
        boundaries = ["\n\n", "\n", ". ", "! ", "? "]
        
        for boundary in boundaries:
            if boundary in content:
                parts = content.split(boundary)
                if len(parts) > 1:
                    chunks = []
                    current_chunk = ""
                    chunk_count = 0
                    
                    for part in parts:
                        if not part.strip():
                            continue
                            
                        potential_chunk = current_chunk + part + boundary
                        
                        if len(potential_chunk) > self.max_chunk_size and current_chunk:
                            # Save current chunk
                            chunk_count += 1
                            chunks.append({
                                **original_chunk,
                                'chunk_id': f"{original_chunk['chunk_id']}_split_{chunk_count}",
                                'content': current_chunk.strip(),
                                'start_position': 0,  # Would need proper calculation
                                'end_position': len(current_chunk.strip())
                            })
                            current_chunk = part + boundary
                        else:
                            current_chunk = potential_chunk
                    
                    # Add remaining content
                    if current_chunk.strip():
                        chunk_count += 1
                        chunks.append({
                            **original_chunk,
                            'chunk_id': f"{original_chunk['chunk_id']}_split_{chunk_count}",
                            'content': current_chunk.strip(),
                            'start_position': 0,
                            'end_position': len(current_chunk.strip())
                        })
                    
                    if len(chunks) > 1:
                        return chunks
        
        # If no good split found, return original chunk
        return [original_chunk]
    
    def _hybrid_chunking(self, text: str, gpt4_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine GPT-4 chunks with fallback chunking when needed"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Use traditional chunking as backup
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.default_chunk_size,
            chunk_overlap=self.default_chunk_size // 4,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        fallback_chunks = text_splitter.split_text(text)
        
        # If GPT-4 provided good metadata, try to preserve it
        if gpt4_chunks and len(fallback_chunks) > 1:
            hybrid_chunks = []
            gpt4_metadata = gpt4_chunks[0] if gpt4_chunks else {}
            
            for i, chunk_content in enumerate(fallback_chunks):
                hybrid_chunk = {
                    'chunk_id': f'hybrid_chunk_{i+1}',
                    'content': chunk_content,
                    'start_position': 0,
                    'end_position': len(chunk_content),
                    'chunk_type': gpt4_metadata.get('chunk_type', 'paragraph'),
                    'section_number': gpt4_metadata.get('section_number', ''),
                    'section_title': gpt4_metadata.get('section_title', ''),
                    'semantic_theme': gpt4_metadata.get('semantic_theme', ''),
                    'quality_score': 0.7,  # Lower score for hybrid approach
                    'gpt4_chunked': True  # Partially GPT-4 enhanced
                }
                hybrid_chunks.append(hybrid_chunk)
            
            return hybrid_chunks
        
        return gpt4_chunks
    
    def _fallback_chunking(self, text: str, document_type: str) -> Dict[str, Any]:
        """Fallback chunking method when GPT-4 is not available"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.default_chunk_size,
            chunk_overlap=self.default_chunk_size // 4,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_text(text)
        
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            formatted_chunk = {
                'chunk_id': f'chunk_{i+1}',
                'content': chunk,
                'start_position': text.find(chunk),
                'end_position': text.find(chunk) + len(chunk),
                'chunk_type': 'paragraph',
                'section_number': '',
                'section_title': '',
                'semantic_theme': '',
                'quality_score': 0.6,
                'gpt4_chunked': False
            }
            formatted_chunks.append(formatted_chunk)
        
        summary = {
            'total_chunks': len(formatted_chunks),
            'average_chunk_size': sum(len(c['content']) for c in formatted_chunks) // len(formatted_chunks) if formatted_chunks else 0,
            'semantic_coherence_score': 0.6,
            'structure_preservation_score': 0.5,
            'gpt4_chunking_used': False
        }
        
        return {
            'success': True,
            'chunks': formatted_chunks,
            'summary': summary,
            'chunking_method': 'fallback_recursive'
        }
    
    def optimize_chunks_for_rag(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-process chunks to optimize them for RAG performance"""
        optimized_chunks = []
        
        for chunk in chunks:
            optimized_chunk = chunk.copy()
            
            # Clean up content
            optimized_chunk['content'] = self._clean_chunk_content(chunk['content'])
            
            # Enhance semantic information
            if not chunk.get('semantic_theme'):
                optimized_chunk['semantic_theme'] = self._extract_semantic_theme(chunk['content'])
            
            # Detect entities if not already present
            if not chunk.get('key_entities'):
                optimized_chunk['key_entities'] = self._extract_entities(chunk['content'])
            
            # Detect cross-references
            if not chunk.get('cross_references'):
                optimized_chunk['cross_references'] = self._detect_cross_references(chunk['content'])
            
            optimized_chunks.append(optimized_chunk)
        
        return optimized_chunks
    
    def _clean_chunk_content(self, content: str) -> str:
        """Clean and normalize chunk content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        # Normalize line breaks
        content = content.strip()
        
        return content
    
    def _extract_semantic_theme(self, content: str) -> str:
        """Extract the main semantic theme of a chunk"""
        # Simple keyword-based theme extraction
        themes = {
            'legal': ['contract', 'agreement', 'clause', 'section', 'party', 'obligation'],
            'technical': ['implementation', 'system', 'technology', 'code', 'function'],
            'financial': ['payment', 'amount', 'cost', 'budget', 'financial'],
            'procedural': ['process', 'procedure', 'step', 'method', 'approach']
        }
        
        content_lower = content.lower()
        theme_scores = {}
        
        for theme, keywords in themes.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            theme_scores[theme] = score
        
        if theme_scores:
            return max(theme_scores, key=theme_scores.get)
        
        return 'general'
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract key entities from chunk content"""
        entities = []
        
        # Extract names (capitalized words)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        entities.extend(names[:3])  # Limit to first 3 names
        
        # Extract numbers and amounts
        amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', content)
        entities.extend(amounts)
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content)
        entities.extend(dates)
        
        return entities[:5]  # Limit to 5 entities
    
    def _detect_cross_references(self, content: str) -> List[str]:
        """Detect cross-references in chunk content"""
        # Common cross-reference patterns
        patterns = [
            r'section\s+\d+(?:\.\d+)*',
            r'clause\s+\d+(?:\.\d+)*',
            r'paragraph\s+\d+(?:\.\d+)*',
            r'see\s+(?:section|clause|paragraph)\s+\d+(?:\.\d+)*',
            r'as\s+defined\s+in\s+section\s+\d+(?:\.\d+)*'
        ]
        
        cross_refs = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            cross_refs.extend(matches)
        
        return list(set(cross_refs))  # Remove duplicates

if __name__ == "__main__":
    chunker = GPT4Chunker(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
        private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
    )
    
    sample_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation.
    
    Section 1: Definitions
    1.1 "Vendor" means ABC Company
    1.2 "Client" means XYZ Corporation
    
    Section 2: Services
    2.1 The Vendor shall provide IT consulting services
    2.2 Services shall commence on January 1, 2024
    """
    
    result = chunker.chunk_document_with_gpt4(sample_text, "legal", True)
    print("Chunking result:", json.dumps(result, indent=2)) 