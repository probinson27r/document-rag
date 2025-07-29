# Legal Document RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system specifically designed for processing and querying legal documents with complex list structures, hierarchical organization, and cross-references.

## 🎯 Features

### Advanced Document Processing
- **Intelligent Chunking**: Section-based chunking that preserves document structure
- **List Structure Preservation**: Handles complex ordered lists (numeric, alphabetic, roman numerals)
- **Hierarchical Relationships**: Maintains parent-child relationships in nested lists
- **Cross-Reference Detection**: Identifies and tracks legal document cross-references
- **Footer Content Filtering**: Automatically filters out irrelevant footer content

### RAG Capabilities
- **Multi-Model Support**: Local (Ollama) and cloud-based (OpenAI, Claude, Jan.ai) LLMs
- **Vector Storage**: ChromaDB for efficient document retrieval
- **Semantic Search**: Sentence transformers for embedding generation
- **Context-Aware Responses**: Maintains document context in responses

### Web Interface
- **Flask Web Application**: User-friendly web interface
- **Document Upload**: Support for PDF, DOCX, TXT, CSV, JSON files
- **Interactive Chat**: Real-time document querying
- **Response Sources**: Shows which document sections were referenced

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama (for local LLM support)
- Optional: API keys for OpenAI, Claude, or Jan.ai

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd document_rag
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-claude-key"
   export PRIVATE_GPT4_API_KEY="your-private-gpt4-key"
   ```

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Access the web interface**
   - Open http://localhost:5000 in your browser
   - Upload legal documents
   - Start querying your documents

## 📁 Project Structure

```
document_rag/
├── app.py                          # Main Flask application
├── legal_document_rag.py           # Core chunking strategy
├── document_rag.py                 # Legacy document processing
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── COMPLETE_CHUNKING_STRATEGY.md   # Detailed chunking documentation
├── templates/                      # Flask templates
├── static/                         # Static assets
├── uploads/                        # Document upload directory
└── chroma_db/                      # Vector database storage
```

## 🔧 Core Components

### Legal Document Processing (`legal_document_rag.py`)

The heart of the system with advanced chunking capabilities:

- **List Detection**: 9 different types of ordered list markers
- **Section Identification**: Cross-page section detection
- **Quality Validation**: Ensures high-quality chunks
- **Cross-Reference Tracking**: Legal document reference detection

### Web Application (`app.py`)

Flask-based web interface with:
- Document upload and processing
- Multi-model LLM integration
- Interactive chat interface
- Response source tracking

### Vector Database

ChromaDB integration for:
- Efficient document storage
- Semantic search capabilities
- Metadata tracking
- Cross-reference linking

## 📊 Chunking Strategy

The system uses an advanced chunking strategy specifically designed for legal documents:

### List Types Supported
- **Numeric**: 1, 2, 3, 4, 5, etc.
- **Hierarchical Numeric**: 1.1, 1.2, 1.1.1, 1.1.2, etc.
- **Compact Hierarchical**: 3.2(a), 3.2(a)(i), 4.1(A), etc.
- **Section Headings**: 3 OBJECTIVES, 4 SCOPE, etc.
- **Alphabetic**: A, B, C, D, etc.
- **Roman Numerals**: I, II, III, IV, V, etc.
- **Parenthetical**: (A), (B), (C), (a), (b), (c), etc.

### Chunking Features
- **Section-based chunking** instead of page-based
- **List continuity preservation** across boundaries
- **Hierarchical relationship maintenance**
- **Optimal chunk sizes** (1000-1500 characters)
- **Quality validation** and filtering

## 🤖 Supported LLM Models

### Local Models (via Ollama)
- `mistral:7b` (default)
- `llama3.1:8b`
- `llama3.1:70b`
- Any Ollama-compatible model

### Cloud Models
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude Sonnet 4
- **Jan.ai**: GPT-4 (local deployment)
- **Private GPT-4**: Custom Azure OpenAI deployment

## 📝 Usage Examples

### Basic Document Querying
1. Upload a legal document (PDF, DOCX, etc.)
2. Wait for processing to complete
3. Ask questions about the document content
4. Review responses with source citations

### Advanced Features
- **Cross-reference tracking**: See which sections reference others
- **Section-based responses**: Get context from specific document sections
- **Multi-document support**: Query across multiple uploaded documents

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_complete_chunking.py
```

Tests include:
- List detection functionality
- Section detection
- Cross-reference detection
- Chunk quality validation
- Complete PDF processing

## 📈 Performance

The system is optimized for:
- **Large documents**: Handles documents with thousands of pages
- **Complex structures**: Preserves legal document formatting
- **Fast retrieval**: Efficient vector search
- **Quality responses**: Context-aware LLM responses

## 🔒 Security

- **Local processing**: Documents processed locally by default
- **No data persistence**: Uploaded documents not stored permanently
- **API key security**: Environment variable-based configuration
- **Input validation**: Comprehensive input sanitization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **PyMuPDF**: PDF text extraction
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embedding generation
- **Flask**: Web framework
- **Ollama**: Local LLM support

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation in `COMPLETE_CHUNKING_STRATEGY.md`
- Review the test files for usage examples

---

**Note**: This system is specifically designed for legal documents and may require customization for other document types. 