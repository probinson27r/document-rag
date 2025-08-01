# Tests Directory

This directory contains all test files for the Document RAG system.

## Test Categories

### 🧪 **Core Functionality Tests**

- **`test_gpt4_extraction.py`** - Tests GPT-4 extraction functionality
- **`test_gpt4_processing.py`** - Tests GPT-4 document processing pipeline
- **`test_gpt4_chunking.py`** - Tests GPT-4 chunking strategies
- **`test_complete_chunking.py`** - Tests complete chunking implementation
- **`test_improved_chunking.py`** - Tests improved chunking algorithms

### 🔧 **Parallel Processing Tests**

- **`test_parallel_processing.py`** - Tests parallel processing implementation with OpenAI
- **`test_parallel_processing_private.py`** - Tests parallel processing with Private GPT-4
- **`test_large_parallel_processing.py`** - Tests parallel processing with large documents (100+ chunks)

### 📊 **Batch Processing Tests**

- **`test_batch_processing.py`** - Tests batch processing functionality
- **`test_batch_debug.py`** - Debug tests for batch processing
- **`test_batch_debug_detailed.py`** - Detailed batch processing debug tests
- **`test_batch_error_debug.py`** - Error debugging for batch processing

### 🚀 **Performance & Optimization Tests**

- **`test_large_document.py`** - Tests processing of large documents
- **`test_large_document_optimized.py`** - Tests optimized large document processing
- **`test_optimized_processing.py`** - Tests processing optimizations
- **`test_final_optimization.py`** - Tests final optimization strategies

### 🔐 **Private GPT-4 Tests**

- **`test_private_gpt4.py`** - Basic Private GPT-4 functionality tests
- **`test_private_gpt4_config.py`** - Private GPT-4 configuration tests
- **`test_private_gpt4_default.py`** - Tests Private GPT-4 as default model
- **`test_private_gpt4_processing.py`** - Private GPT-4 processing pipeline tests
- **`test_private_gpt4_debug.py`** - Debug tests for Private GPT-4

### 🌐 **Web Application Tests**

- **`test_web_simple.py`** - Simple web application tests
- **`test_web_upload.py`** - File upload functionality tests
- **`test_progress.py`** - Progress tracking tests
- **`test_timeout_fix.py`** - Timeout handling tests

### 📝 **Document Processing Tests**

- **`test_pdf_gpt4.py`** - PDF processing with GPT-4 tests
- **`test_traditional.py`** - Traditional document processing tests
- **`test_document_rag_integration.py`** - Full RAG integration tests

### 🔧 **Configuration & Setup Tests**

- **`test_openai_default.py`** - Tests OpenAI as default model
- **`test_json_fix.py`** - JSON parsing fix tests
- **`test_simple_fix.py`** - Simple bug fix tests

### 💬 **Chat & History Tests**

- **`test_chat_history.py`** - Chat history functionality tests
- **`test_chat_history_debug.py`** - Chat history debug tests

### 🔍 **Analysis Tests**

- **`analyze_section_detection.py`** - Section detection analysis

## Debug Files

- **`debug_pdf_hanging.py`** - Debug PDF processing hanging issues
- **`debug_private_gpt4_timeout.py`** - Debug Private GPT-4 timeout issues
- **`debug_pdf_processing.py`** - Debug PDF processing issues
- **`debug_private_gpt4_response.py`** - Debug Private GPT-4 response issues

## Running Tests

To run a specific test:

```bash
python tests/test_name.py
```

To run all tests (if you have pytest installed):

```bash
pytest tests/
```

## Test Environment

All tests require:
- Environment variables loaded from `.env.local`
- Required dependencies installed
- Appropriate API keys configured

## Notes

- Most tests are designed to run independently
- Tests use mock data or small sample documents
- Debug files contain additional logging and error handling
- Performance tests may take longer to complete 