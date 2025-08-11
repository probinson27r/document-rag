#!/usr/bin/env python3
"""
Hybrid Search Implementation for Document RAG System
Combines semantic search with exact text matching for better retrieval
Enhanced for numbered list detection and enumeration queries
"""

import chromadb
import re
from typing import List, Dict, Tuple, Optional
import logging

class HybridSearch:
    def __init__(self, chroma_path: str = './chroma_db', collection_name: str = 'documents'):
        """
        Initialize hybrid search with ChromaDB connection
        
        Args:
            chroma_path: Path to ChromaDB directory
            collection_name: Name of the collection to search
        """
        # Initialize ChromaDB with same settings as Flask app
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_collection(collection_name)
        self.logger = logging.getLogger(__name__)
    
    def is_list_query(self, query: str) -> bool:
        """
        Detect if the query is asking for a list or enumeration
        
        Args:
            query: Search query
            
        Returns:
            True if query is asking for a list
        """
        list_keywords = [
            'list', 'enumerate', 'show all', 'all of', 'every', 'complete list',
            'numbered', 'objectives', 'items', 'points', 'requirements',
            'what are the', 'what are all the', 'tell me all', 'give me all'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in list_keywords)
    
    def is_objectives_query(self, query: str) -> bool:
        """
        Detect if the query is specifically asking about objectives
        
        Args:
            query: Search query
            
        Returns:
            True if query is about objectives
        """
        objectives_keywords = [
            'objectives', 'objective', 'contract objectives', 'agreement objectives',
            'section objectives', 'clause objectives'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in objectives_keywords)
    
    def extract_section_numbers(self, query: str) -> List[str]:
        """
        Extract section numbers from query (e.g., "11.4", "Section 3.2")
        
        Args:
            query: Search query
            
        Returns:
            List of section numbers found
        """
        # Pattern to match section numbers like 11.4, 3.2, etc.
        section_pattern = r'\b(\d+\.\d+)\b'
        section_numbers = re.findall(section_pattern, query)
        
        # Also look for "Section X.Y" patterns
        section_text_pattern = r'Section\s+(\d+\.\d+)'
        section_text_numbers = re.findall(section_text_pattern, query, re.IGNORECASE)
        
        return list(set(section_numbers + section_text_numbers))
    
    def find_numbered_patterns(self, text: str) -> List[Tuple[str, str]]:
        """
        Find numbered patterns in text (1., 2., 3., etc.)
        
        Args:
            text: Text to search for numbered patterns
            
        Returns:
            List of tuples (number, content)
        """
        # Pattern to match numbered lists: 1., 2., 3., etc.
        numbered_pattern = r'\b(\d+)\.\s*([^.\n]+(?:[.\n][^.\n]+)*)'
        matches = re.findall(numbered_pattern, text)
        
        # Also look for patterns like (1), (2), etc.
        parenthetical_pattern = r'\((\d+)\)\s*([^.\n]+(?:[.\n][^.\n]+)*)'
        parenthetical_matches = re.findall(parenthetical_pattern, text)
        
        # Also look for patterns like 1), 2), etc.
        bracket_pattern = r'\b(\d+)\)\s*([^.\n]+(?:[.\n][^.\n]+)*)'
        bracket_matches = re.findall(bracket_pattern, text)
        
        all_matches = matches + parenthetical_matches + bracket_matches
        return [(num, content.strip()) for num, content in all_matches]
    
    def find_section_content(self, section_numbers: List[str], all_documents: List[str]) -> List[Dict]:
        """
        Find content related to specific sections
        
        Args:
            section_numbers: List of section numbers to search for
            all_documents: List of all document texts
            
        Returns:
            List of section-related content
        """
        section_results = []
        
        for i, doc_text in enumerate(all_documents):
            doc_lower = doc_text.lower()
            
            for section_num in section_numbers:
                # Look for section headers
                section_patterns = [
                    rf'\b{section_num}\b',  # Exact section number
                    rf'section\s+{section_num}',  # "Section 3.2"
                    rf'clause\s+{section_num}',   # "Clause 3.2"
                    rf'paragraph\s+{section_num}' # "Paragraph 3.2"
                ]
                
                for pattern in section_patterns:
                    if re.search(pattern, doc_lower, re.IGNORECASE):
                        # Find numbered patterns in this document
                        numbered_items = self.find_numbered_patterns(doc_text)
                        
                        section_results.append({
                            'id': f'section_{section_num}_{i}',
                            'text': doc_text,
                            'section_number': section_num,
                            'numbered_items': numbered_items,
                            'search_type': 'section_content',
                            'distance': 0.0,  # High relevance
                            'rank': len(section_results) + 1
                        })
                        break
        
        return section_results
    
    def find_objectives_content(self, all_documents: List[str]) -> List[Dict]:
        """
        Find content specifically related to objectives
        
        Args:
            all_documents: List of all document texts
            
        Returns:
            List of objectives-related content
        """
        objectives_results = []
        
        for i, doc_text in enumerate(all_documents):
            doc_lower = doc_text.lower()
            
            # Look for objectives-related patterns
            objectives_patterns = [
                r'\bobjectives?\b',
                r'section\s+\d+\.\d+.*objectives?',
                r'clause\s+\d+\.\d+.*objectives?',
                r'\d+\.\d+.*objectives?'
            ]
            
            for pattern in objectives_patterns:
                if re.search(pattern, doc_lower, re.IGNORECASE):
                    # Find numbered patterns in this document
                    numbered_items = self.find_numbered_patterns(doc_text)
                    
                    objectives_results.append({
                        'id': f'objectives_{i}',
                        'text': doc_text,
                        'numbered_items': numbered_items,
                        'search_type': 'objectives_content',
                        'distance': 0.0,  # High relevance
                        'rank': len(objectives_results) + 1
                    })
                    break
        
        return objectives_results
    
    def expand_list_query(self, query: str, section_numbers: List[str]) -> List[str]:
        """
        Expand a list query with additional search terms
        
        Args:
            query: Original query
            section_numbers: Section numbers found in query
            
        Returns:
            List of expanded search queries
        """
        expanded_queries = [query]
        
        # Add section-specific queries
        for section_num in section_numbers:
            expanded_queries.extend([
                f"Section {section_num} objectives",
                f"Section {section_num} list",
                f"Section {section_num} numbered",
                f"Section {section_num} items",
                f"Clause {section_num} objectives",
                f"Clause {section_num} list"
            ])
        
        # Add general list-related queries
        expanded_queries.extend([
            "numbered list",
            "objectives list",
            "complete list",
            "all items",
            "enumerate"
        ])
        
        return expanded_queries
    
    def semantic_search(self, query: str, n_results: int = 10, distance_threshold: float = 0.8) -> List[Dict]:
        """
        Perform semantic search using vector similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            distance_threshold: Maximum distance threshold (higher = more permissive)
            
        Returns:
            List of search results with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            semantic_results = []
            for i, (doc_id, doc_text, distance) in enumerate(zip(
                results['ids'][0], 
                results['documents'][0], 
                results['distances'][0]
            )):
                if distance <= distance_threshold:
                    semantic_results.append({
                        'id': doc_id,
                        'text': doc_text,
                        'distance': distance,
                        'search_type': 'semantic',
                        'rank': i + 1
                    })
            
            return semantic_results
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            return []
    
    def exact_text_search(self, query: str, section_numbers: List[str] = None) -> List[Dict]:
        """
        Perform exact text search for specific terms or section numbers
        
        Args:
            query: Search query
            section_numbers: List of section numbers to search for
            
        Returns:
            List of search results with metadata
        """
        try:
            # Get all documents
            all_results = self.collection.get()
            
            exact_results = []
            search_terms = []
            
            # Add section numbers to search terms
            if section_numbers:
                search_terms.extend(section_numbers)
            
            # Add key terms from query
            key_terms = query.lower().split()
            search_terms.extend([term for term in key_terms if len(term) > 2])
            
            # Search for exact matches
            for i, (doc_id, doc_text) in enumerate(zip(all_results['ids'], all_results['documents'])):
                doc_lower = doc_text.lower()
                matches = []
                
                for term in search_terms:
                    if term.lower() in doc_lower:
                        matches.append(term)
                
                if matches:
                    # Calculate a simple relevance score based on number of matches
                    relevance_score = len(matches) / len(search_terms)
                    exact_results.append({
                        'id': doc_id,
                        'text': doc_text,
                        'distance': 1.0 - relevance_score,  # Convert to distance format
                        'search_type': 'exact',
                        'matches': matches,
                        'rank': len(exact_results) + 1
                    })
            
            # Sort by relevance (lower distance = better)
            exact_results.sort(key=lambda x: x['distance'])
            
            return exact_results
            
        except Exception as e:
            self.logger.error(f"Exact text search failed: {e}")
            return []
    
    def list_enhanced_search(self, query: str, section_numbers: List[str], n_results: int = 15) -> List[Dict]:
        """
        Enhanced search specifically for list queries
        
        Args:
            query: Search query
            section_numbers: Section numbers to search for
            n_results: Number of results to return
            
        Returns:
            List of search results optimized for list retrieval
        """
        try:
            # Get all documents
            all_results = self.collection.get()
            
            # Find section content
            section_results = self.find_section_content(section_numbers, all_results['documents'])
            
            # Expand the search with multiple queries
            expanded_queries = self.expand_list_query(query, section_numbers)
            
            all_results_list = []
            
            # Search with each expanded query
            for expanded_query in expanded_queries:
                semantic_results = self.semantic_search(expanded_query, n_results=10, distance_threshold=0.9)
                all_results_list.extend(semantic_results)
            
            # Add section-specific results
            all_results_list.extend(section_results)
            
            # Remove duplicates and sort by relevance
            seen_ids = set()
            unique_results = []
            
            for result in all_results_list:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)
            
            # Sort by distance (lower is better)
            unique_results.sort(key=lambda x: x['distance'])
            
            return unique_results[:n_results]
            
        except Exception as e:
            self.logger.error(f"List enhanced search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, n_results: int = 10, 
                     semantic_weight: float = 0.7, exact_weight: float = 0.3,
                     distance_threshold: float = 0.8) -> List[Dict]:
        """
        Perform hybrid search combining semantic and exact text matching
        
        Args:
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic search results (0.0-1.0)
            exact_weight: Weight for exact text search results (0.0-1.0)
            distance_threshold: Maximum distance threshold for semantic search
            
        Returns:
            List of combined and ranked search results
        """
        # Extract section numbers from query
        section_numbers = self.extract_section_numbers(query)
        
        # Perform both searches
        semantic_results = self.semantic_search(query, n_results * 2, distance_threshold)
        exact_results = self.exact_text_search(query, section_numbers)
        
        # Combine results
        combined_results = {}
        
        # Add semantic results
        for result in semantic_results:
            doc_id = result['id']
            if doc_id not in combined_results:
                combined_results[doc_id] = result.copy()
                combined_results[doc_id]['combined_score'] = semantic_weight * (1.0 - result['distance'])
            else:
                # If already exists, update with better score
                existing_score = combined_results[doc_id]['combined_score']
                new_score = semantic_weight * (1.0 - result['distance'])
                combined_results[doc_id]['combined_score'] = max(existing_score, new_score)
        
        # Add exact results
        for result in exact_results:
            doc_id = result['id']
            if doc_id not in combined_results:
                combined_results[doc_id] = result.copy()
                combined_results[doc_id]['combined_score'] = exact_weight * (1.0 - result['distance'])
            else:
                # If already exists, boost the score
                existing_score = combined_results[doc_id]['combined_score']
                exact_score = exact_weight * (1.0 - result['distance'])
                combined_results[doc_id]['combined_score'] = existing_score + exact_score
        
        # Convert to list and sort by combined score
        final_results = list(combined_results.values())
        final_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Limit to requested number of results
        return final_results[:n_results]
    
    def search_with_fallback(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Search with intelligent fallback strategy and enhanced list detection
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results
        """
        # Extract section numbers
        section_numbers = self.extract_section_numbers(query)
        
        # Check if this is a list query
        is_list = self.is_list_query(query)
        
        # Check if this is an objectives query
        is_objectives = self.is_objectives_query(query)
        
        if is_list and section_numbers:
            self.logger.info(f"List query detected for sections: {section_numbers}")
            
            # Use enhanced list search
            list_results = self.list_enhanced_search(query, section_numbers, n_results * 2)
            if list_results:
                self.logger.info(f"Found {len(list_results)} list-enhanced results")
                return list_results[:n_results]
            
            # Fallback to hybrid search with list bias
            self.logger.info("No list results, trying hybrid search with list bias")
            return self.hybrid_search(query, n_results, semantic_weight=0.3, exact_weight=0.7)
        
        elif is_objectives and not section_numbers:
            self.logger.info("Objectives query detected without section numbers")
            
            # Try to find objectives content specifically
            try:
                all_results = self.collection.get()
                objectives_results = self.find_objectives_content(all_results['documents'])
                
                if objectives_results:
                    self.logger.info(f"Found {len(objectives_results)} objectives-specific results")
                    return objectives_results[:n_results]
                
                # Fallback to semantic search with objectives focus
                self.logger.info("No objectives-specific results, trying semantic search with objectives focus")
                objectives_queries = [
                    "objectives of the agreement",
                    "section 3.2 objectives",
                    "contract objectives",
                    "agreement objectives",
                    "objectives list"
                ]
                
                all_results = []
                for obj_query in objectives_queries:
                    results = self.semantic_search(obj_query, n_results=5, distance_threshold=0.9)
                    all_results.extend(results)
                
                # Remove duplicates and sort
                seen_ids = set()
                unique_results = []
                for result in all_results:
                    if result['id'] not in seen_ids:
                        seen_ids.add(result['id'])
                        unique_results.append(result)
                
                unique_results.sort(key=lambda x: x['distance'])
                return unique_results[:n_results]
                
            except Exception as e:
                self.logger.error(f"Objectives search failed: {e}")
                # Fallback to regular semantic search
                return self.semantic_search(query, n_results, distance_threshold=0.8)
        
        elif section_numbers:
            self.logger.info(f"Found section numbers: {section_numbers}")
            
            # Try exact search first
            exact_results = self.exact_text_search(query, section_numbers)
            if exact_results:
                self.logger.info(f"Found {len(exact_results)} exact matches")
                return exact_results[:n_results]
            
            # Fallback to hybrid search
            self.logger.info("No exact matches, trying hybrid search")
            return self.hybrid_search(query, n_results, semantic_weight=0.3, exact_weight=0.7)
        
        elif is_list:
            self.logger.info("List query detected without section numbers")
            
            # Use expanded queries for list search
            expanded_queries = self.expand_list_query(query, [])
            all_results = []
            
            for expanded_query in expanded_queries[:3]:  # Limit to first 3 expanded queries
                results = self.semantic_search(expanded_query, n_results=5, distance_threshold=0.9)
                all_results.extend(results)
            
            # Remove duplicates and sort
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    unique_results.append(result)
            
            unique_results.sort(key=lambda x: x['distance'])
            return unique_results[:n_results]
        
        else:
            # No section numbers, use semantic search with fallback
            self.logger.info("No section numbers found, using semantic search")
            semantic_results = self.semantic_search(query, n_results, distance_threshold=0.8)
            
            if semantic_results:
                return semantic_results
            
            # Fallback to more permissive search
            self.logger.info("No semantic results, trying more permissive search")
            return self.semantic_search(query, n_results, distance_threshold=0.9)

# Example usage and testing
if __name__ == "__main__":
    # Initialize hybrid search
    hybrid_search = HybridSearch()
    
    # Test queries
    test_queries = [
        "Section 11.4",
        "11.4",
        "No commitment",
        "What is Section 11.4 about?",
        "Project Services Quote",
        "Statement of Work",
        "List the objectives in section 3.2",
        "Show all objectives in section 3.2",
        "Enumerate every objective in section 3.2",
        "List the contract objectives",
        "What are the objectives",
        "Contract objectives"
    ]
    
    print("Testing Enhanced Hybrid Search:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        is_list = hybrid_search.is_list_query(query)
        is_objectives = hybrid_search.is_objectives_query(query)
        section_numbers = hybrid_search.extract_section_numbers(query)
        
        print(f"  List query: {is_list}")
        print(f"  Objectives query: {is_objectives}")
        print(f"  Section numbers: {section_numbers}")
        
        results = hybrid_search.search_with_fallback(query, n_results=3)
        
        for i, result in enumerate(results):
            contains_11_4 = '11.4' in result['text']
            contains_3_2 = '3.2' in result['text']
            relevance = '✓ RELEVANT' if (contains_11_4 or contains_3_2) else '✗ NOT RELEVANT'
            print(f"  {i+1}. Score: {result.get('combined_score', 1.0 - result['distance']):.4f} | {relevance}")
            print(f"     Type: {result.get('search_type', 'unknown')}")
            print(f"     Text: {result['text'][:100]}...")
            if contains_11_4:
                print(f"     ✓ Found 11.4 in this result!")
            if contains_3_2:
                print(f"     ✓ Found 3.2 in this result!")
