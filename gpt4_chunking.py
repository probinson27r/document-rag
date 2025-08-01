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
                                model: str = "gpt-4o",
                                prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """Chunk document using GPT-4 with intelligent semantic splitting"""
        try:
            # Prioritize Private GPT-4 if available and preferred
            if prefer_private_gpt4 and self.private_gpt4_url and self.private_gpt4_key:
                logger.info("Using Private GPT-4 for chunking")
                return self._chunk_with_private_gpt4(text, document_type, preserve_structure, model)
            elif model.startswith("gpt-4") and self.openai_client:
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
                    {"role": "system", "content": "You are an expert document chunking specialist. Split documents into optimal chunks for RAG systems while preserving semantic meaning and document structure."},
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
        
        type_instructions = {
            "legal": """
            LEGAL DOCUMENT CHUNKING RULES:
            - Preserve complete legal clauses and sections
            - Keep related subsections together
            - Maintain cross-references within chunks
            - Preserve numbered lists and hierarchical structure
            """,
            "technical": """
            TECHNICAL DOCUMENT CHUNKING RULES:
            - Keep code blocks and examples together
            - Preserve technical specifications
            - Maintain step-by-step procedures
            """,
            "general": """
            GENERAL DOCUMENT CHUNKING RULES:
            - Keep complete sentences and paragraphs
            - Preserve logical flow and context
            - Maintain document structure
            """
        }
        
        chunking_rules = type_instructions.get(document_type, type_instructions["general"])
        
        prompt = f"""
        {chunking_rules}
        
        CHUNKING REQUIREMENTS:
        - Target chunk size: {self.default_chunk_size} characters
        - Maximum chunk size: {self.max_chunk_size} characters
        - Minimum chunk size: {self.min_chunk_size} characters
        - Preserve structure: {preserve_structure}
        
        DOCUMENT TEXT TO CHUNK:
        {text}
        
        Return the result as JSON with the following structure:
        {{
            "chunks": [
                {{
                    "chunk_id": "chunk_1",
                    "content": "chunk content here",
                    "start_position": 0,
                    "end_position": 500,
                    "chunk_type": "section|paragraph|list|definition",
                    "section_number": "1.1",
                    "section_title": "Section Title",
                    "semantic_theme": "main topic of this chunk",
                    "quality_score": 0.95
                }}
            ],
            "summary": {{
                "total_chunks": 5,
                "average_chunk_size": 850,
                "semantic_coherence_score": 0.92,
                "structure_preservation_score": 0.88
            }}
        }}
        
        CRITICAL: Return ONLY valid JSON without any markdown formatting, code blocks, or additional text. Start with {{ and end with }}.
        """
        
        return prompt
    
    def _parse_chunking_result(self, result: str, original_text: str) -> Dict[str, Any]:
        """Parse the GPT-4 chunking result"""
        # Clean the result to handle markdown formatting
        cleaned_result = self._clean_json_response(result)
        
        try:
            parsed_result = json.loads(cleaned_result)
            chunks = parsed_result.get('chunks', [])
            validated_chunks = []
            
            for i, chunk in enumerate(chunks):
                validated_chunk = {
                    'chunk_id': chunk.get('chunk_id', f'chunk_{i+1}'),
                    'content': chunk.get('content', ''),
                    'start_position': chunk.get('start_position', 0),
                    'end_position': chunk.get('end_position', 0),
                    'chunk_type': chunk.get('chunk_type', 'paragraph'),
                    'section_number': chunk.get('section_number', ''),
                    'section_title': chunk.get('section_title', ''),
                    'semantic_theme': chunk.get('semantic_theme', ''),
                    'quality_score': chunk.get('quality_score', 0.8),
                    'gpt4_chunked': True
                }
                
                validated_chunks.append(validated_chunk)
            
            summary = parsed_result.get('summary', {})
            summary['total_chunks'] = len(validated_chunks)
            summary['gpt4_chunking_used'] = True
            
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