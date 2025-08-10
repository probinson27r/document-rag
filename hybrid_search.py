#!/usr/bin/env python3
"""
Hybrid Search Implementation for Document RAG System
Combines semantic search with exact text matching for better retrieval
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
        Search with intelligent fallback strategy
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results
        """
        # Extract section numbers
        section_numbers = self.extract_section_numbers(query)
        
        # If query contains section numbers, prioritize exact search
        if section_numbers:
            self.logger.info(f"Found section numbers: {section_numbers}")
            
            # Try exact search first
            exact_results = self.exact_text_search(query, section_numbers)
            if exact_results:
                self.logger.info(f"Found {len(exact_results)} exact matches")
                return exact_results[:n_results]
            
            # Fallback to hybrid search
            self.logger.info("No exact matches, trying hybrid search")
            return self.hybrid_search(query, n_results, semantic_weight=0.3, exact_weight=0.7)
        
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
        "Statement of Work"
    ]
    
    print("Testing Hybrid Search:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = hybrid_search.search_with_fallback(query, n_results=3)
        
        for i, result in enumerate(results):
            contains_11_4 = '11.4' in result['text']
            relevance = '✓ RELEVANT' if contains_11_4 else '✗ NOT RELEVANT'
            print(f"  {i+1}. Score: {result.get('combined_score', 1.0 - result['distance']):.4f} | {relevance}")
            print(f"     Type: {result.get('search_type', 'unknown')}")
            print(f"     Text: {result['text'][:100]}...")
            if contains_11_4:
                print(f"     ✓ Found 11.4 in this result!")
