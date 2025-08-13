#!/usr/bin/env python3
"""
GPT-4 Enhanced Data Extraction Module

This module provides GPT-4 powered data extraction capabilities that can:
1. Extract structured data from documents
2. Improve text extraction quality
3. Identify and extract key information
4. Clean and format extracted text
5. Generate document summaries and metadata
"""

import os
import json
import logging
import time
import asyncio
import concurrent.futures
import tiktoken
from typing import Dict, List, Any, Optional
from pathlib import Path
import openai
import anthropic
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPT4Extractor:
    """GPT-4 powered document extraction and processing"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 private_gpt4_url: Optional[str] = None,
                 private_gpt4_key: Optional[str] = None):
        """
        Initialize GPT-4 extractor with available API keys
        
        Args:
            openai_api_key: OpenAI API key for GPT-4
            anthropic_api_key: Anthropic API key for Claude
            private_gpt4_url: Private GPT-4 endpoint URL
            private_gpt4_key: Private GPT-4 API key
        """
        self.openai_client = None
        self.claude_client = None
        self.private_gpt4_url = private_gpt4_url
        self.private_gpt4_key = private_gpt4_key
        
        # Initialize token encoder for GPT-4
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            # Fallback to cl100k_base encoding used by GPT-4
            self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # Context limits for different models
        self.context_limits = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4o": 128000,
            "gpt-5": 128000,
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-haiku": 200000
        }
        
        # Reserve tokens for system prompt and response
        # Increased margin to prevent context overflow
        self.reserved_tokens = 8000
        
        # Initialize OpenAI client
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
            logger.info("OpenAI GPT-4 client initialized")
        
        # Initialize Claude client
        if anthropic_api_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("Claude client initialized")
        
        # Check if private GPT-4 is available
        if private_gpt4_url and private_gpt4_key:
            logger.info("Private GPT-4 client configured")
        
        if not any([self.openai_client, self.claude_client, private_gpt4_url]):
            logger.warning("No GPT-4 clients available - extraction will use fallback methods")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using the GPT-4 tokenizer"""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using character-based estimation")
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def get_context_limit(self, model: str) -> int:
        """Get context limit for a model"""
        return self.context_limits.get(model, 128000)
    
    def chunk_text_for_model(self, text: str, prompt: str, model: str = "gpt-5") -> List[str]:
        """
        Chunk text to fit within model context limits
        
        Args:
            text: Text to chunk
            prompt: System prompt that will be used
            model: Model name to get context limit
            
        Returns:
            List of text chunks that fit within context limits
        """
        context_limit = self.get_context_limit(model)
        max_text_tokens = context_limit - self.reserved_tokens
        
        # Count tokens in prompt
        prompt_tokens = self.count_tokens(prompt)
        
        # Add extra safety margin for prompt variations and response tokens
        safety_margin = 4000
        available_tokens = max_text_tokens - prompt_tokens - safety_margin
        
        # Ensure we don't go below a reasonable minimum
        if available_tokens < 10000:
            available_tokens = min(10000, context_limit // 2)
            logger.warning(f"Very limited token space available. Using conservative limit: {available_tokens}")
        
        logger.info(f"Model: {model}, Context limit: {context_limit}, Reserved: {self.reserved_tokens}")
        logger.info(f"Prompt tokens: {prompt_tokens}, Safety margin: {safety_margin}")
        logger.info(f"Available for text: {available_tokens}")
        
        # Count tokens in full text
        total_tokens = self.count_tokens(text)
        logger.info(f"Input text tokens: {total_tokens}")
        
        if total_tokens <= available_tokens:
            logger.info("Text fits within context limit, no chunking needed")
            return [text]
        
        # Need to chunk the text
        logger.info(f"Text exceeds context limit, chunking into smaller pieces")
        chunks = []
        
        # Split text into paragraphs first (better for preserving context)
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            # If single paragraph is too large, split by sentences
            if paragraph_tokens > available_tokens:
                # Split large paragraph into sentences
                sentences = paragraph.split('. ')
                for i, sentence in enumerate(sentences):
                    if i < len(sentences) - 1:
                        sentence += '. '  # Re-add period except for last sentence
                    
                    sentence_tokens = self.count_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > available_tokens:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence
                            current_tokens = sentence_tokens
                        else:
                            # Single sentence is too large, truncate it
                            words = sentence.split()
                            truncated_sentence = ""
                            for word in words:
                                test_sentence = truncated_sentence + " " + word if truncated_sentence else word
                                if self.count_tokens(test_sentence) < available_tokens:
                                    truncated_sentence = test_sentence
                                else:
                                    break
                            chunks.append(truncated_sentence.strip())
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                        current_tokens += sentence_tokens
            else:
                # Check if adding this paragraph would exceed limit
                if current_tokens + paragraph_tokens > available_tokens:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph
                        current_tokens = paragraph_tokens
                    else:
                        chunks.append(paragraph)
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                    current_tokens += paragraph_tokens
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Validate all chunks fit within limits
        validated_chunks = []
        for i, chunk in enumerate(chunks):
            tokens = self.count_tokens(chunk)
            
            if tokens > available_tokens:
                logger.warning(f"Chunk {i+1} still too large ({tokens} tokens), attempting further reduction")
                # Force split oversized chunk
                words = chunk.split()
                reduced_chunk = ""
                for word in words:
                    test_chunk = reduced_chunk + " " + word if reduced_chunk else word
                    if self.count_tokens(test_chunk) <= available_tokens:
                        reduced_chunk = test_chunk
                    else:
                        if reduced_chunk:
                            validated_chunks.append(reduced_chunk)
                            reduced_chunk = word
                        else:
                            # Single word is too large, skip it
                            logger.error(f"Single word '{word}' exceeds token limit, skipping")
                            break
                if reduced_chunk:
                    validated_chunks.append(reduced_chunk)
            else:
                validated_chunks.append(chunk)
        
        logger.info(f"Split text into {len(validated_chunks)} validated chunks")
        for i, chunk in enumerate(validated_chunks):
            tokens = self.count_tokens(chunk)
            logger.info(f"Chunk {i+1}: {tokens} tokens")
            
            # Final safety check
            if tokens > available_tokens:
                logger.error(f"ERROR: Chunk {i+1} still exceeds limit ({tokens} > {available_tokens})")
        
        return validated_chunks
    
    def extract_with_gpt4(self, 
                         text: str, 
                         extraction_prompt: str,
                         model: str = "gpt-5",
                         max_tokens: int = 4000,
                         prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Extract structured data from text using GPT-4
        
        Args:
            text: Raw text to extract from
            extraction_prompt: Specific prompt for extraction
            model: Model to use (gpt-4o, gpt-4, claude-3-5-sonnet-20241022)
            max_tokens: Maximum tokens for response
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Dictionary with extraction results
        """
        try:
            # Prioritize Private GPT-4 if available and preferred
            if prefer_private_gpt4 and self.private_gpt4_url and self.private_gpt4_key:
                logger.info("Using Private GPT-4 for extraction")
                return self._extract_with_private_gpt4(text, extraction_prompt, model, max_tokens)
            elif model.startswith("gpt-") and self.openai_client:
                return self._extract_with_openai(text, extraction_prompt, model, max_tokens)
            elif model.startswith("claude") and self.claude_client:
                return self._extract_with_claude(text, extraction_prompt, model, max_tokens)
            elif self.private_gpt4_url and self.private_gpt4_key:
                # Fallback to Private GPT-4 if other providers fail
                logger.info("Falling back to Private GPT-4 for extraction")
                return self._extract_with_private_gpt4(text, extraction_prompt, model, max_tokens)
            else:
                logger.warning(f"Model {model} not available, using fallback")
                return {"error": f"Model {model} not available", "extracted_data": {}}
                
        except Exception as e:
            logger.error(f"Error in GPT-4 extraction: {e}")
            return {"error": str(e), "extracted_data": {}}
    
    def _extract_with_openai(self, text: str, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Extract using OpenAI GPT-4"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert document analyzer and data extractor. Extract the requested information accurately and return it in JSON format."},
                    {"role": "user", "content": f"{prompt}\n\nDocument text:\n{text}"}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            try:
                # Try to parse as JSON
                extracted_data = json.loads(result)
                return {"success": True, "extracted_data": extracted_data, "raw_response": result}
            except json.JSONDecodeError:
                # Return as text if not JSON
                return {"success": True, "extracted_data": {"text": result}, "raw_response": result}
                
        except Exception as e:
            logger.error(f"OpenAI extraction error: {e}")
            return {"error": str(e), "extracted_data": {}}
    
    def _extract_with_claude(self, text: str, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Extract using Claude"""
        try:
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nDocument text:\n{text}\n\nPlease return the extracted information in JSON format."}
                ]
            )
            
            result = response.content[0].text
            try:
                # Try to parse as JSON
                extracted_data = json.loads(result)
                return {"success": True, "extracted_data": extracted_data, "raw_response": result}
            except json.JSONDecodeError:
                # Return as text if not JSON
                return {"success": True, "extracted_data": {"text": result}, "raw_response": result}
                
        except Exception as e:
            logger.error(f"Claude extraction error: {e}")
            return {"error": str(e), "extracted_data": {}}
    
    def _extract_with_private_gpt4(self, text: str, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Extract using Private GPT-4"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.private_gpt4_key,
                'Accept': 'application/json'
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": "You are an expert document analyzer and data extractor. Extract the requested information accurately and return it in JSON format."},
                    {"role": "user", "content": f"{prompt}\n\nDocument text:\n{text}"}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            # Add timeout to prevent hanging
            response = requests.post(self.private_gpt4_url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                # Clean the response to handle markdown formatting
                cleaned_content = self._clean_json_response(content)
                # Try to parse as JSON
                extracted_data = json.loads(cleaned_content)
                return {"success": True, "extracted_data": extracted_data, "raw_response": content}
            except json.JSONDecodeError:
                # Return as text if not JSON
                return {"success": True, "extracted_data": {"text": content}, "raw_response": content}
                
        except requests.exceptions.Timeout:
            logger.error("Private GPT-4 extraction timeout after 30 seconds")
            return {"error": "Request timeout", "extracted_data": {}}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Private GPT-4 connection error: {e}")
            return {"error": f"Connection failed: {str(e)}", "extracted_data": {}}
        except Exception as e:
            logger.error(f"Private GPT-4 extraction error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text}")
            return {"error": str(e), "extracted_data": {}}
    
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
    
    def enhance_text_extraction(self, raw_text: str, file_type: str, prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Enhance text extraction using GPT-4 with automatic chunking for large documents
        
        Args:
            raw_text: Raw extracted text
            file_type: Type of file (.pdf, .docx, etc.)
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Enhanced text and metadata
        """
        prompt = f"""
        You are an expert document processor. Analyze and enhance the following {file_type} document text.
        
        Please:
        1. Clean and format the text for better readability
        2. Identify and preserve document structure (headings, sections, etc.)
        3. Extract key metadata (title, author, date, etc.)
        4. Identify document type and purpose
        5. Extract any tables, lists, or structured data
        6. Remove redundant or irrelevant content
        7. Preserve important formatting and hierarchy
        
        Return the result as JSON with the following structure:
        {{
            "enhanced_text": "cleaned and formatted text",
            "metadata": {{
                "title": "document title",
                "author": "author if found",
                "date": "date if found",
                "document_type": "type of document",
                "purpose": "document purpose",
                "sections": ["list of main sections"],
                "tables": ["extracted table data"],
                "lists": ["extracted list data"]
            }},
            "quality_score": 0.95,
            "processing_notes": "any notes about the processing"
        }}
        """
        
        return self._extract_with_chunking(raw_text, prompt, "gpt-5", prefer_private_gpt4=prefer_private_gpt4)
    
    def _extract_with_chunking(self, text: str, prompt: str, model: str = "gpt-5", prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Extract data with automatic chunking if text is too large
        
        Args:
            text: Text to process
            prompt: Extraction prompt
            model: Model to use
            prefer_private_gpt4: Whether to prefer private GPT-4
            
        Returns:
            Combined extraction results
        """
        # Check if chunking is needed
        chunks = self.chunk_text_for_model(text, prompt, model)
        
        if len(chunks) == 1:
            # No chunking needed, process normally
            return self.extract_with_gpt4(text, prompt, model, max_tokens=4000, prefer_private_gpt4=prefer_private_gpt4)
        
        # Process multiple chunks and combine results
        logger.info(f"Processing document in {len(chunks)} chunks")
        
        all_enhanced_text = []
        combined_metadata = {
            "title": "",
            "author": "",
            "date": "",
            "document_type": "",
            "purpose": "",
            "sections": [],
            "tables": [],
            "lists": []
        }
        quality_scores = []
        processing_notes = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Add chunk context to prompt
            chunk_prompt = f"""
            {prompt}
            
            NOTE: This is chunk {i+1} of {len(chunks)} from a larger document. 
            Focus on processing this section while maintaining awareness that it's part of a larger document.
            """
            
            result = self.extract_with_gpt4(chunk, chunk_prompt, model, max_tokens=4000, prefer_private_gpt4=prefer_private_gpt4)
            
            if result.get("success") and result.get("extracted_data"):
                data = result["extracted_data"]
                
                # Collect enhanced text
                if "enhanced_text" in data:
                    all_enhanced_text.append(data["enhanced_text"])
                
                # Merge metadata
                if "metadata" in data:
                    metadata = data["metadata"]
                    
                    # Take first non-empty title, author, etc.
                    if not combined_metadata["title"] and metadata.get("title"):
                        combined_metadata["title"] = metadata["title"]
                    if not combined_metadata["author"] and metadata.get("author"):
                        combined_metadata["author"] = metadata["author"]
                    if not combined_metadata["date"] and metadata.get("date"):
                        combined_metadata["date"] = metadata["date"]
                    if not combined_metadata["document_type"] and metadata.get("document_type"):
                        combined_metadata["document_type"] = metadata["document_type"]
                    if not combined_metadata["purpose"] and metadata.get("purpose"):
                        combined_metadata["purpose"] = metadata["purpose"]
                    
                    # Extend lists
                    if metadata.get("sections"):
                        combined_metadata["sections"].extend(metadata["sections"])
                    if metadata.get("tables"):
                        combined_metadata["tables"].extend(metadata["tables"])
                    if metadata.get("lists"):
                        combined_metadata["lists"].extend(metadata["lists"])
                
                # Collect quality scores and notes
                if "quality_score" in data:
                    quality_scores.append(data["quality_score"])
                if "processing_notes" in data:
                    processing_notes.append(f"Chunk {i+1}: {data['processing_notes']}")
            else:
                logger.warning(f"Failed to process chunk {i+1}: {result.get('error', 'Unknown error')}")
                all_enhanced_text.append(chunk)  # Use original chunk as fallback
        
        # Combine results
        combined_enhanced_text = "\n\n".join(all_enhanced_text)
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        combined_notes = "; ".join(processing_notes)
        
        return {
            "success": True,
            "extracted_data": {
                "enhanced_text": combined_enhanced_text,
                "metadata": combined_metadata,
                "quality_score": average_quality,
                "processing_notes": f"Processed in {len(chunks)} chunks. {combined_notes}"
            },
            "chunks_processed": len(chunks),
            "total_tokens": self.count_tokens(text)
        }
    
    def extract_structured_data(self, text: str, data_types: List[str], prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Extract specific types of structured data from text
        
        Args:
            text: Document text
            data_types: List of data types to extract (e.g., ["dates", "names", "amounts", "contracts"])
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Extracted structured data
        """
        data_type_descriptions = {
            "dates": "dates, deadlines, time periods",
            "names": "person names, company names, organization names",
            "amounts": "monetary amounts, quantities, percentages",
            "contracts": "contract terms, clauses, obligations",
            "contact_info": "email addresses, phone numbers, addresses",
            "references": "document references, citations, cross-references",
            "key_terms": "important terms, definitions, acronyms"
        }
        
        requested_types = [data_type_descriptions.get(dt, dt) for dt in data_types]
        
        prompt = f"""
        Extract the following types of structured data from the document:
        {', '.join(requested_types)}
        
        Return the result as JSON with the following structure:
        {{
            "extracted_data": {{
                "dates": ["list of dates found"],
                "names": ["list of names found"],
                "amounts": ["list of amounts found"],
                "contracts": ["list of contract terms"],
                "contact_info": ["list of contact information"],
                "references": ["list of references"],
                "key_terms": ["list of key terms"]
            }},
            "confidence_scores": {{
                "dates": 0.95,
                "names": 0.90,
                "amounts": 0.95,
                "contracts": 0.85,
                "contact_info": 0.90,
                "references": 0.80,
                "key_terms": 0.85
            }},
            "processing_summary": "summary of what was extracted"
        }}
        
        Only include the data types that were requested: {data_types}
        """
        
        return self.extract_with_gpt4(text, prompt, "gpt-5", prefer_private_gpt4=prefer_private_gpt4)
    
    def generate_document_summary(self, text: str, summary_type: str = "comprehensive", prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Generate document summary using GPT-4
        
        Args:
            text: Document text
            summary_type: Type of summary ("comprehensive", "executive", "key_points")
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Document summary and key information
        """
        summary_prompts = {
            "comprehensive": "Generate a comprehensive summary of the document including main points, key findings, and important details.",
            "executive": "Generate an executive summary highlighting the most important points for decision-makers.",
            "key_points": "Extract the key points and main takeaways from the document."
        }
        
        prompt = f"""
        {summary_prompts.get(summary_type, summary_prompts["comprehensive"])}
        
        Return the result as JSON with the following structure:
        {{
            "summary": "main summary text",
            "key_points": ["list of key points"],
            "main_topics": ["list of main topics covered"],
            "important_findings": ["list of important findings"],
            "recommendations": ["list of recommendations if any"],
            "summary_length": "short/medium/long",
            "confidence_score": 0.95
        }}
        """
        
        return self.extract_with_gpt4(text, prompt, "gpt-5", prefer_private_gpt4=prefer_private_gpt4)
    
    def extract_legal_contract_data(self, text: str, prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Extract legal contract information using GPT-4
        
        Args:
            text: Contract text
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Extracted contract data
        """
        prompt = """
        Extract legal contract information from the document.
        
        Return the result as JSON with the following structure:
        {
            "contract_info": {
                "contract_title": "title of the contract",
                "parties": ["list of parties involved"],
                "effective_date": "effective date",
                "expiration_date": "expiration date",
                "contract_value": "total contract value",
                "contract_type": "type of contract"
            },
            "key_terms": {
                "obligations": ["list of key obligations"],
                "deliverables": ["list of deliverables"],
                "payment_terms": ["payment terms"],
                "termination_clauses": ["termination clauses"],
                "liability_terms": ["liability terms"]
            },
            "sections": {
                "section_1": {"title": "section title", "key_points": ["key points"]},
                "section_2": {"title": "section title", "key_points": ["key_points"]}
            },
            "risk_factors": ["list of risk factors"],
            "compliance_requirements": ["list of compliance requirements"],
            "extraction_confidence": 0.90
        }
        """
        
        return self.extract_with_gpt4(text, prompt, "gpt-5", prefer_private_gpt4=prefer_private_gpt4)
    
    def clean_and_format_text(self, text: str, preserve_structure: bool = True, prefer_private_gpt4: bool = True) -> Dict[str, Any]:
        """
        Clean and format extracted text using GPT-4
        
        Args:
            text: Raw extracted text
            preserve_structure: Whether to preserve document structure
            prefer_private_gpt4: Whether to prefer Private GPT-4 over other providers
            
        Returns:
            Cleaned and formatted text
        """
        prompt = f"""
        Clean and format the following extracted text. 
        
        Requirements:
        - Remove redundant whitespace and formatting issues
        - Fix broken sentences and paragraphs
        - Preserve document structure and hierarchy
        - Maintain important formatting (headings, lists, etc.)
        - Remove OCR artifacts and scanning errors
        - Ensure proper sentence structure and punctuation
        - Preserve tables and structured data if present
        
        Preserve structure: {preserve_structure}
        
        Return the result as JSON:
        {{
            "cleaned_text": "cleaned and formatted text",
            "formatting_improvements": ["list of improvements made"],
            "structure_preserved": true,
            "quality_improvement": 0.15
        }}
        """
        
        return self.extract_with_gpt4(text, prompt, "gpt-4o", prefer_private_gpt4=prefer_private_gpt4)

    def batch_enhance_chunks(self, chunks: List[Dict[str, Any]], features: Dict[str, bool] = None, prefer_private_gpt4: bool = True) -> List[Dict[str, Any]]:
        """
        Enhance multiple chunks using parallel processing and large batches for maximum efficiency
        
        Args:
            chunks: List of chunk dictionaries with 'content' field
            features: Dictionary of features to enable/disable
            prefer_private_gpt4: Whether to prefer Private GPT-4
            
        Returns:
            List of enhanced chunks
        """
        if not chunks:
            return chunks
            
        if features is None:
            features = {
                'text_enhancement': False,  # Disable by default for speed
                'structured_data': True,
                'contract_analysis': True
            }
        
        logger.info(f"Starting parallel batch processing for {len(chunks)} chunks")
        start_time = time.time()
        
        # Process all chunks with parallel processing
        enhanced_chunks = self._parallel_batch_processing(chunks, features, prefer_private_gpt4)
        
        processing_time = time.time() - start_time
        logger.info(f"Parallel batch processing completed in {processing_time:.2f} seconds")
        
        return enhanced_chunks
    
    def _parallel_batch_processing(self, chunks: List[Dict[str, Any]], features: Dict[str, bool], prefer_private_gpt4: bool) -> List[Dict[str, Any]]:
        """
        Process chunks in parallel using large batches
        """
        # Large batch size for efficiency
        batch_size = 50  # Process 50 chunks at a time
        max_workers = 4  # Number of parallel workers
        
        enhanced_chunks = []
        
        # Split chunks into batches
        batches = []
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batches.append((i // batch_size + 1, batch_chunks))
        
        logger.info(f"Created {len(batches)} batches of {batch_size} chunks each")
        
        # Process batches in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch processing tasks
            future_to_batch = {
                executor.submit(self._process_batch, batch_chunks, features, prefer_private_gpt4, batch_num): batch_num 
                for batch_num, batch_chunks in batches
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    batch_result = future.result()
                    enhanced_chunks.extend(batch_result)
                    logger.info(f"Batch {batch_num} completed successfully")
                except Exception as e:
                    logger.error(f"Batch {batch_num} failed: {e}")
                    # Add original chunks for failed batch
                    batch_chunks = batches[batch_num - 1][1]
                    enhanced_chunks.extend([chunk.copy() for chunk in batch_chunks])
        
        return enhanced_chunks
    
    def _process_batch(self, batch_chunks: List[Dict[str, Any]], features: Dict[str, bool], prefer_private_gpt4: bool, batch_num: int) -> List[Dict[str, Any]]:
        """
        Process a single batch of chunks
        """
        logger.info(f"Processing batch {batch_num} with {len(batch_chunks)} chunks")
        
        # Combine batch chunk contents for efficient processing
        combined_content = "\n\n--- CHUNK SEPARATOR ---\n\n".join([
            f"CHUNK {i+1}:\n{chunk.get('content', '')}" 
            for i, chunk in enumerate(batch_chunks)
        ])
        
        batch_enhanced_chunks = [chunk.copy() for chunk in batch_chunks]
        
        try:
            # Process structured data extraction for the entire batch
            if features.get('structured_data', True):
                data_types = ['dates', 'names', 'amounts', 'key_terms']
                if features.get('contract_analysis', True):
                    data_types.extend(['contracts', 'references'])
                
                structured_result = self.extract_structured_data(combined_content, data_types, prefer_private_gpt4)
                if structured_result.get('success'):
                    # Apply structured data to all chunks in this batch
                    for enhanced_chunk in batch_enhanced_chunks:
                        enhanced_chunk['structured_data'] = structured_result['extracted_data']
            
            # Process contract analysis for the entire batch
            if features.get('contract_analysis', True):
                contract_result = self.extract_legal_contract_data(combined_content, prefer_private_gpt4)
                if contract_result.get('success'):
                    # Apply contract analysis to all chunks in this batch
                    for enhanced_chunk in batch_enhanced_chunks:
                        enhanced_chunk['contract_analysis'] = contract_result['extracted_data']
            
            # Process text enhancement in parallel for individual chunks
            if features.get('text_enhancement', True):
                self._parallel_text_enhancement(batch_enhanced_chunks, prefer_private_gpt4)
                
        except Exception as e:
            logger.warning(f"Batch {batch_num} processing failed: {e}")
            # Fallback to original chunks
            batch_enhanced_chunks = [chunk.copy() for chunk in batch_chunks]
        
        return batch_enhanced_chunks
    
    def _parallel_text_enhancement(self, chunks: List[Dict[str, Any]], prefer_private_gpt4: bool):
        """
        Enhance text for multiple chunks in parallel
        """
        def enhance_single_chunk(chunk_data):
            chunk, index = chunk_data
            try:
                enhancement_result = self.enhance_text_extraction(chunk['content'], '.pdf', prefer_private_gpt4)
                if enhancement_result.get('success'):
                    enhanced_text = enhancement_result['extracted_data'].get('enhanced_text', chunk['content'])
                    chunk['content'] = enhanced_text
            except Exception as e:
                logger.warning(f"Text enhancement failed for chunk {index+1}: {e}")
        
        # Process text enhancement in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            chunk_data = [(chunk, i) for i, chunk in enumerate(chunks)]
            executor.map(enhance_single_chunk, chunk_data)

# Example usage and testing
if __name__ == "__main__":
    # Initialize extractor with available API keys
    extractor = GPT4Extractor(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
        private_gpt4_url=os.getenv('PRIVATE_GPT4_URL'),
        private_gpt4_key=os.getenv('PRIVATE_GPT4_API_KEY')
    )
    
    # Test with sample text
    sample_text = """
    CONTRACT AGREEMENT
    
    This agreement is made between ABC Company and XYZ Corporation.
    
    Effective Date: January 1, 2024
    Contract Value: $500,000
    
    Section 1: Services
    The vendor shall provide IT consulting services.
    
    Section 2: Payment Terms
    Payment shall be made within 30 days of invoice.
    """
    
    # Test different extraction methods
    print("Testing GPT-4 extraction...")
    
    # Test structured data extraction
    result = extractor.extract_structured_data(sample_text, ["dates", "names", "amounts"])
    print("Structured data extraction:", json.dumps(result, indent=2))
    
    # Test contract data extraction
    result = extractor.extract_legal_contract_data(sample_text)
    print("Contract data extraction:", json.dumps(result, indent=2))
    
    # Test document summary
    result = extractor.generate_document_summary(sample_text, "key_points")
    print("Document summary:", json.dumps(result, indent=2)) 