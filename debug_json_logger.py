#!/usr/bin/env python3
"""
JSON Debug Logger

This module provides utilities to write JSON data to the filesystem for debugging purposes.
It logs configuration changes, document processing results, and chunking outputs.
"""

import json
import os
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class JSONDebugLogger:
    """Logger for writing JSON debug information to filesystem"""
    
    def __init__(self, debug_dir: str = "debug_json"):
        """Initialize the JSON debug logger
        
        Args:
            debug_dir: Directory to store debug JSON files
        """
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.debug_dir / "config").mkdir(exist_ok=True)
        (self.debug_dir / "processing").mkdir(exist_ok=True)
        (self.debug_dir / "chunks").mkdir(exist_ok=True)
        (self.debug_dir / "extraction").mkdir(exist_ok=True)
        (self.debug_dir / "queries").mkdir(exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for filenames"""
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    
    def _write_json_file(self, data: Dict[Any, Any], filepath: Path, description: str = ""):
        """Write JSON data to file with error handling
        
        Args:
            data: Dictionary to write as JSON
            filepath: Path to write the file
            description: Description for logging
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[DEBUG JSON] {description} written to: {filepath}")
            return True
            
        except Exception as e:
            print(f"[DEBUG JSON ERROR] Failed to write {description}: {e}")
            return False
    
    def log_configuration(self, config: Dict[str, Any], config_type: str = "extraction") -> str:
        """Log configuration changes
        
        Args:
            config: Configuration dictionary
            config_type: Type of configuration (extraction, chat, etc.)
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        filename = f"{config_type}_config_{timestamp}.json"
        filepath = self.debug_dir / "config" / filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "config_type": config_type,
            "config": config
        }
        
        self._write_json_file(debug_data, filepath, f"Configuration ({config_type})")
        return str(filepath)
    
    def log_document_processing(self, 
                               filename: str,
                               processing_result: Dict[str, Any],
                               config: Optional[Dict[str, Any]] = None) -> str:
        """Log document processing results
        
        Args:
            filename: Name of the processed document
            processing_result: Result from document processing
            config: Configuration used for processing
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        json_filename = f"processing_{safe_filename}_{timestamp}.json"
        filepath = self.debug_dir / "processing" / json_filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "document_filename": filename,
            "config_used": config,
            "processing_result": processing_result
        }
        
        self._write_json_file(debug_data, filepath, f"Document Processing ({filename})")
        return str(filepath)
    
    def log_chunks(self, 
                   filename: str,
                   chunks: List[Dict[str, Any]],
                   chunking_method: str,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log document chunks
        
        Args:
            filename: Name of the source document
            chunks: List of chunk dictionaries
            chunking_method: Method used for chunking
            metadata: Additional metadata about chunking
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        json_filename = f"chunks_{safe_filename}_{chunking_method}_{timestamp}.json"
        filepath = self.debug_dir / "chunks" / json_filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "document_filename": filename,
            "chunking_method": chunking_method,
            "total_chunks": len(chunks),
            "metadata": metadata or {},
            "chunks": chunks
        }
        
        self._write_json_file(debug_data, filepath, f"Chunks ({filename}, {chunking_method})")
        return str(filepath)
    
    def log_extraction_result(self, 
                             filename: str,
                             extraction_type: str,
                             extraction_result: Dict[str, Any]) -> str:
        """Log extraction results (LangExtract, GPT-4, etc.)
        
        Args:
            filename: Name of the source document
            extraction_type: Type of extraction (langextract, gpt4, etc.)
            extraction_result: Result from extraction
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        json_filename = f"extraction_{extraction_type}_{safe_filename}_{timestamp}.json"
        filepath = self.debug_dir / "extraction" / json_filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "document_filename": filename,
            "extraction_type": extraction_type,
            "extraction_result": extraction_result
        }
        
        self._write_json_file(debug_data, filepath, f"Extraction ({extraction_type}, {filename})")
        return str(filepath)
    
    def log_query_result(self, 
                        query: str,
                        result: Dict[str, Any],
                        context_docs: Optional[List[str]] = None) -> str:
        """Log query results
        
        Args:
            query: The query string
            result: Query result
            context_docs: List of documents used for context
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        # Create safe query for filename
        safe_query = "".join(c for c in query[:50] if c.isalnum() or c in " ._-").strip().replace(" ", "_")
        json_filename = f"query_{safe_query}_{timestamp}.json"
        filepath = self.debug_dir / "queries" / json_filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "query": query,
            "context_documents": context_docs or [],
            "result": result
        }
        
        self._write_json_file(debug_data, filepath, f"Query Result ({query[:50]}...)")
        return str(filepath)
    
    def log_session_data(self, session_data: Dict[str, Any]) -> str:
        """Log session data
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Path to the written file
        """
        timestamp = self._get_timestamp()
        json_filename = f"session_{timestamp}.json"
        filepath = self.debug_dir / "config" / json_filename
        
        debug_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_data": session_data
        }
        
        self._write_json_file(debug_data, filepath, "Session Data")
        return str(filepath)
    
    def create_debug_summary(self) -> str:
        """Create a summary of all debug files
        
        Returns:
            Path to the summary file
        """
        timestamp = self._get_timestamp()
        summary_file = self.debug_dir / f"debug_summary_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "debug_directory": str(self.debug_dir),
            "subdirectories": {
                "config": len(list((self.debug_dir / "config").glob("*.json"))),
                "processing": len(list((self.debug_dir / "processing").glob("*.json"))),
                "chunks": len(list((self.debug_dir / "chunks").glob("*.json"))),
                "extraction": len(list((self.debug_dir / "extraction").glob("*.json"))),
                "queries": len(list((self.debug_dir / "queries").glob("*.json")))
            },
            "recent_files": []
        }
        
        # Get recent files from each subdirectory
        for subdir in ["config", "processing", "chunks", "extraction", "queries"]:
            subdir_path = self.debug_dir / subdir
            if subdir_path.exists():
                recent_files = sorted(subdir_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                summary["recent_files"].extend([{
                    "subdirectory": subdir,
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                } for f in recent_files])
        
        self._write_json_file(summary, summary_file, "Debug Summary")
        return str(summary_file)

# Global debug logger instance
debug_logger = JSONDebugLogger()

def log_debug_json(data: Dict[str, Any], category: str, description: str = "") -> str:
    """Convenience function to log JSON data
    
    Args:
        data: Data to log
        category: Category (config, processing, chunks, extraction, queries)
        description: Description for the log
        
    Returns:
        Path to the written file
    """
    if category == "config":
        return debug_logger.log_configuration(data, description or "general")
    elif category == "processing":
        return debug_logger.log_document_processing(
            data.get("filename", "unknown"),
            data,
            data.get("config")
        )
    elif category == "chunks":
        return debug_logger.log_chunks(
            data.get("filename", "unknown"),
            data.get("chunks", []),
            data.get("chunking_method", "unknown"),
            data.get("metadata")
        )
    elif category == "extraction":
        return debug_logger.log_extraction_result(
            data.get("filename", "unknown"),
            data.get("extraction_type", "unknown"),
            data
        )
    elif category == "queries":
        return debug_logger.log_query_result(
            data.get("query", "unknown"),
            data,
            data.get("context_docs")
        )
    else:
        # Generic logging
        timestamp = debug_logger._get_timestamp()
        filepath = debug_logger.debug_dir / f"{category}_{timestamp}.json"
        debug_logger._write_json_file(data, filepath, description)
        return str(filepath)

if __name__ == "__main__":
    # Test the debug logger
    print("🔍 Testing JSON Debug Logger")
    print("=" * 50)
    
    # Test configuration logging
    test_config = {
        "extraction_method": "langextract",
        "chunking_method": "semantic",
        "prefer_private_gpt4": False
    }
    
    config_file = debug_logger.log_configuration(test_config, "extraction")
    print(f"✅ Config logged: {config_file}")
    
    # Test chunk logging
    test_chunks = [
        {"content": "Test chunk 1", "chunk_type": "semantic", "tokens": 50},
        {"content": "Test chunk 2", "chunk_type": "semantic", "tokens": 75}
    ]
    
    chunks_file = debug_logger.log_chunks("test_doc.txt", test_chunks, "semantic")
    print(f"✅ Chunks logged: {chunks_file}")
    
    # Create summary
    summary_file = debug_logger.create_debug_summary()
    print(f"✅ Summary created: {summary_file}")
    
    print("\n📁 Debug directory structure created!")
    print(f"   Location: {debug_logger.debug_dir}")
    print("   Subdirectories: config/, processing/, chunks/, extraction/, queries/")
