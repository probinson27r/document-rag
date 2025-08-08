# GPT-4 Chunking Guide

## Overview

The document RAG system now includes intelligent GPT-4-powered chunking that can intelligently split documents into optimal chunks for RAG (Retrieval-Augmented Generation) systems while preserving semantic meaning and document structure.

## Features

### 🧠 Intelligent Semantic Chunking
- **Semantic Coherence**: Chunks are created based on semantic meaning rather than arbitrary character limits
- **Structure Preservation**: Maintains document hierarchy, sections, and relationships
- **Context Awareness**: Keeps related information together within chunks
- **Quality Optimization**: Optimizes chunks for better RAG performance

### 🔧 Multiple Provider Support
- **OpenAI GPT-4**: Primary provider with advanced reasoning capabilities
- **Anthropic Claude**: Alternative provider for enhanced analysis
- **Private GPT-4**: Secure, private deployment option
- **Fallback System**: Automatic fallback to traditional chunking if GPT-4 is unavailable

### 📄 Document Type Specialization
- **Legal Documents**: Preserves legal clauses, sections, and cross-references
- **Technical Documents**: Maintains code blocks, specifications, and procedures
- **General Documents**: Optimized for general content with logical flow
- **Auto-Detection**: Automatically determines document type based on content

## Architecture

### Core Components

1. **GPT4Chunker Class** (`gpt4_chunking.py`)
   - Main chunking engine with GPT-4 integration
   - Provider management (OpenAI, Claude, Private GPT-4)
   - Fallback mechanisms
   - Chunk optimization for RAG

2. **DocumentProcessor Integration** (`document_rag.py`)
   - Seamless integration with existing document processing
   - Automatic GPT-4 chunking when available
   - Metadata preservation and enhancement

3. **Configuration System** (`app.py`)
   - User-configurable chunking options
   - API key management
   - Feature toggles

### Chunking Process

```
Document Input
     ↓
Text Extraction
     ↓
GPT-4 Analysis
     ↓
Semantic Chunking
     ↓
Chunk Optimization
     ↓
Metadata Enhancement
     ↓
RAG Storage
```

## Usage

### Basic Usage

```python
from gpt4_chunking import GPT4Chunker

# Initialize chunker
chunker = GPT4Chunker(
    openai_api_key="your_openai_key",
    anthropic_api_key="your_anthropic_key",
    private_gpt4_url="your_private_gpt4_url",
    private_gpt4_key="your_private_gpt4_key"
)

# Chunk document
result = chunker.chunk_document_with_gpt4(
    text="your_document_text",
    document_type="legal",  # or "technical", "general"
    preserve_structure=True
)

# Access results
chunks = result['chunks']
summary = result['summary']
```

### Integration with DocumentRAG

```python
from document_rag import DocumentRAG

# Initialize RAG system with GPT-4 chunking
rag = DocumentRAG()

# Document will be automatically chunked using GPT-4 if available
result = rag.ingest_document("document.pdf")
```

### Configuration Options

```python
# Configure chunking behavior
config = {
    'extraction_method': 'auto',  # auto, gpt4_enhanced, traditional
    'features': {
        'gpt4_chunking': True,  # Enable GPT-4 chunking
        'text_enhancement': True,
        'structured_data': True
    },
    'chunking': {
        'method': 'auto',  # auto, gpt4, traditional
        'document_type': 'auto',  # auto, legal, technical, general
        'preserve_structure': True
    }
}
```

## API Reference

### GPT4Chunker Class

#### Constructor
```python
GPT4Chunker(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    private_gpt4_url: Optional[str] = None,
    private_gpt4_key: Optional[str] = None,
    default_chunk_size: int = 1000,
    max_chunk_size: int = 2000,
    min_chunk_size: int = 200
)
```

#### Methods

##### `chunk_document_with_gpt4()`
```python
def chunk_document_with_gpt4(
    text: str,
    document_type: str = "general",
    preserve_structure: bool = True,
    model: str = "gpt-4o"
) -> Dict[str, Any]
```

**Parameters:**
- `text`: Document text to chunk
- `document_type`: Type of document ("legal", "technical", "general")
- `preserve_structure`: Whether to preserve document structure
- `model`: GPT-4 model to use

**Returns:**
```python
{
    'success': True,
    'chunks': [
        {
            'chunk_id': 'chunk_1',
            'content': 'chunk content',
            'chunk_type': 'section',
            'section_number': '1.1',
            'section_title': 'Definitions',
            'semantic_theme': 'legal_definitions',
            'quality_score': 0.95,
            'gpt4_chunked': True
        }
    ],
    'summary': {
        'total_chunks': 5,
        'average_chunk_size': 850,
        'semantic_coherence_score': 0.92,
        'structure_preservation_score': 0.88
    },
    'chunking_method': 'gpt4_intelligent'
}
```

##### `optimize_chunks_for_rag()`
```python
def optimize_chunks_for_rag(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

Post-processes chunks to optimize them for RAG performance.

## Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key

# Private GPT-4
PRIVATE_GPT4_URL=your_private_gpt4_url
PRIVATE_GPT4_API_KEY=your_private_gpt4_key
```

### Web Interface Configuration

Access the configuration page at `/configure` to:
- Enable/disable GPT-4 chunking
- Select document types
- Configure chunking parameters
- Set API preferences

## Testing

### Run Tests
```bash
# Test GPT-4 chunking functionality
python test_gpt4_chunking.py

# Test API key availability
python check_api_keys.py
```

### Test Results
The test suite validates:
- ✅ GPT-4 chunker import and initialization
- ✅ API key availability and connectivity
- ✅ Document chunking with different types
- ✅ Chunk optimization for RAG
- ✅ Fallback mechanisms
- ✅ Integration with DocumentRAG

## Performance

### Chunking Quality Metrics
- **Semantic Coherence Score**: Measures how well chunks maintain semantic meaning
- **Structure Preservation Score**: Measures how well document structure is preserved
- **Quality Score**: Overall chunk quality assessment
- **Size Distribution**: Analysis of chunk size distribution

### Optimization Features
- **Content Cleaning**: Removes excessive whitespace and formatting issues
- **Entity Extraction**: Identifies key entities (names, amounts, dates)
- **Cross-Reference Detection**: Finds document cross-references
- **Theme Extraction**: Identifies semantic themes for each chunk

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Error: Invalid API key provided
   Solution: Verify API keys in .env.local file
   ```

2. **Fallback to Traditional Chunking**
   ```
   Warning: GPT-4 chunking failed, using fallback
   Solution: Check API key validity and network connectivity
   ```

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'gpt4_chunking'
   Solution: Ensure all dependencies are installed
   ```

### Debug Mode
Enable debug logging to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### Document Preparation
1. **Clean Input**: Ensure documents are properly extracted and cleaned
2. **Format Consistency**: Use consistent formatting for better structure detection
3. **File Types**: Prefer PDF and DOCX for best results

### Configuration
1. **Document Type**: Set appropriate document type for optimal chunking
2. **Structure Preservation**: Enable for legal and technical documents
3. **API Selection**: Use the most reliable API provider for your use case

### Performance Optimization
1. **Chunk Size**: Adjust based on your RAG system requirements
2. **Quality Thresholds**: Set appropriate quality thresholds
3. **Caching**: Consider caching results for repeated documents

## Future Enhancements

### Planned Features
- **Multi-language Support**: Extend to other languages
- **Advanced Entity Recognition**: Enhanced entity extraction
- **Dynamic Chunking**: Adaptive chunk sizes based on content density
- **Cross-Document Linking**: Link related sections across documents
- **Table Preservation**: Better handling of tabular data
- **Image Context**: Include image context in chunking decisions

### Integration Opportunities
- **Vector Database Optimization**: Optimize for specific vector databases
- **Custom Models**: Support for custom fine-tuned models
- **Batch Processing**: Efficient batch processing of multiple documents
- **Real-time Processing**: Stream processing for live documents

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review test results for specific error messages
3. Verify API key configuration
4. Test with the provided test scripts

## Conclusion

GPT-4 chunking provides a significant improvement in document processing quality for RAG systems. By leveraging the semantic understanding capabilities of GPT-4, documents are chunked in a way that preserves meaning and context, leading to better retrieval and generation results.

The system is designed to be robust with automatic fallbacks and comprehensive error handling, ensuring reliable operation even when GPT-4 services are unavailable. 