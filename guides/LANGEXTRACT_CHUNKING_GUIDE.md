# LangExtract Chunking Guide

## Overview

LangExtract is Google's intelligent document structure extraction technology that provides an alternative to the existing semantic chunking system. This guide explains how to use LangExtract chunking in the Document RAG system.

## Features

### LangExtract Chunking Capabilities

- **Intelligent Structure Extraction**: Automatically identifies document sections, subsections, and hierarchical relationships
- **List Preservation**: Maintains complete numbered and bulleted lists without breaking them across chunks
- **Semantic Categorization**: Categorizes content by semantic meaning (objectives, definitions, obligations, etc.)
- **Confidence Scoring**: Provides confidence scores for extraction quality
- **Multiple Extraction Methods**: Supports both API-based and fallback pattern-based extraction

### Comparison with Other Chunking Methods

| Feature | Semantic Chunking | LangExtract | GPT-4 Chunking | Traditional |
|---------|------------------|-------------|----------------|-------------|
| **Section Preservation** | ✅ Excellent | ✅ Excellent | ✅ Good | ❌ Poor |
| **List Preservation** | ✅ Excellent | ✅ Excellent | ✅ Good | ❌ Poor |
| **Semantic Understanding** | ✅ Good | ✅ Excellent | ✅ Excellent | ❌ None |
| **API Dependency** | ❌ None | ⚠️ Optional | ✅ Required | ❌ None |
| **Speed** | ✅ Fast | ✅ Fast | ❌ Slow | ✅ Very Fast |
| **Cost** | ✅ Free | ⚠️ API costs | ❌ Expensive | ✅ Free |

## Configuration

### Setting Chunking Method

1. **Via Web Interface**:
   - Navigate to the Configure page (`/configure`)
   - Select "LangExtract (Google AI)" from the "Document Chunking Method" dropdown
   - Click "Save" to apply the configuration

2. **Via API**:
   ```bash
   curl -X POST /api/extraction/config \
     -H "Content-Type: application/json" \
     -d '{
       "chunking": {
         "method": "langextract"
       }
     }'
   ```

3. **Programmatically**:
   ```python
   from document_rag import DocumentRAG
   
   # Initialize with LangExtract chunking
   rag = DocumentRAG(chunking_method='langextract')
   ```

### Available Chunking Methods

- `semantic`: Semantic chunking (default) - preserves document sections and lists
- `langextract`: LangExtract chunking - Google's intelligent structure extraction
- `gpt4`: GPT-4 chunking - AI-powered chunking (requires API)
- `traditional`: Traditional chunking - basic text splitting

## API Setup (Optional)

### Google API Configuration

To use LangExtract with Google's API for enhanced extraction:

1. **Get Google API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Set the `GOOGLE_API_KEY` environment variable

2. **Install Dependencies**:
   ```bash
   pip install langchain-google-genai
   ```

3. **Environment Variables**:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

### Fallback Mode

If the Google API is not available or configured, LangExtract automatically falls back to pattern-based extraction that provides similar benefits without external dependencies.

## Usage Examples

### Basic Usage

```python
from langextract_chunking import LangExtractChunker

# Initialize chunker
chunker = LangExtractChunker(
    max_chunk_size=2000,
    min_chunk_size=200,
    preserve_lists=True,
    preserve_sections=True,
    use_langextract_api=True  # Set to False for fallback mode
)

# Chunk a document
chunks = chunker.chunk_document(document_text)

# Process chunks
for chunk in chunks:
    print(f"Chunk ID: {chunk.chunk_id}")
    print(f"Section Type: {chunk.section_type}")
    print(f"Section Title: {chunk.section_title}")
    print(f"Confidence: {chunk.confidence}")
    print(f"Content: {chunk.content[:100]}...")
```

### Integration with DocumentRAG

```python
from document_rag import DocumentRAG

# Initialize RAG system with LangExtract chunking
rag = DocumentRAG(chunking_method='langextract')

# Ingest documents
result = rag.ingest_document('document.pdf')
print(result)
```

## Chunk Metadata

LangExtract chunks include rich metadata:

```python
{
    "content": "chunk text content",
    "chunk_id": "langextract_1",
    "section_type": "objectives",
    "section_title": "Project Objectives",
    "chunk_type": "complete_section",
    "semantic_theme": "objectives",
    "list_items": [
        {
            "number": "1",
            "text": "First objective",
            "hierarchy_level": 1
        }
    ],
    "start_position": 0,
    "end_position": 500,
    "confidence": 0.95,
    "extraction_method": "langextract_api"
}
```

## Best Practices

### When to Use LangExtract

- **Legal Documents**: Excellent for contracts, agreements, and legal text
- **Technical Documents**: Great for specifications, requirements, and procedures
- **Structured Content**: Ideal for documents with clear sections and lists
- **High-Quality Extraction**: When you need confidence scores and semantic categorization

### Performance Optimization

1. **Chunk Size**: Adjust `max_chunk_size` based on your use case:
   - 1500-2000: Good balance for most documents
   - 1000-1500: For detailed analysis
   - 2000-3000: For broader context

2. **API Usage**: Use fallback mode for:
   - High-volume processing
   - Cost-sensitive applications
   - Offline environments

3. **Caching**: LangExtract results can be cached to avoid reprocessing

### Error Handling

```python
try:
    chunks = chunker.chunk_document(text)
except Exception as e:
    print(f"LangExtract failed: {e}")
    # Fallback to traditional chunking
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter()
    chunks = text_splitter.split_text(text)
```

## Troubleshooting

### Common Issues

1. **No chunks generated**:
   - Check if document has sufficient content
   - Verify chunk size settings
   - Ensure document format is supported

2. **API errors**:
   - Verify Google API key is set correctly
   - Check API quota and limits
   - Use fallback mode if API is unavailable

3. **Poor extraction quality**:
   - Adjust chunk size parameters
   - Check document formatting
   - Consider using different chunking method

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

chunker = LangExtractChunker()
chunks = chunker.chunk_document(text)
```

## Testing

Run the test suite to verify LangExtract functionality:

```bash
python3 test_langextract_chunking.py
```

This will test:
- Basic chunking functionality
- Different chunk size configurations
- Integration with DocumentRAG
- Fallback mode operation

## Migration from Other Chunking Methods

### From Semantic Chunking

1. Update configuration to use `langextract`
2. Re-process existing documents if needed
3. Monitor chunk quality and adjust parameters

### From Traditional Chunking

1. Expect improved section and list preservation
2. Review chunk metadata for additional insights
3. Consider adjusting search parameters for better results

## Future Enhancements

Planned improvements for LangExtract chunking:

- **Enhanced API Integration**: Better error handling and retry logic
- **Custom Extraction Patterns**: User-defined section and list patterns
- **Multi-language Support**: Support for non-English documents
- **Performance Optimization**: Caching and parallel processing
- **Quality Metrics**: Automated chunk quality assessment

## Support

For issues or questions about LangExtract chunking:

1. Check the troubleshooting section above
2. Review the test output for error details
3. Verify configuration settings
4. Test with fallback mode to isolate API issues

## Conclusion

LangExtract chunking provides a powerful alternative to existing chunking methods, offering intelligent document structure extraction with excellent section and list preservation. Whether using the Google API or fallback mode, it delivers high-quality chunks suitable for RAG applications.
