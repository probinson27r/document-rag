from flask import Flask, request, jsonify, render_template, send_from_directory, send_file, after_this_request
import os
import json
from werkzeug.utils import secure_filename
from legal_document_rag import process_legal_pdf_nemo
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import ollama
import anthropic
import logging
import openai
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
embedding_model = None
chroma_client = None
collection = None
ollama_client = None
claude_client = None
openai_client = None
jan_client = None
current_model = 'mistral:7b'  # Default to local model
openai_model_name = 'gpt-4o'  # Default OpenAI model name
jan_model_name = 'gpt-4'  # Default Jan.ai model name
user_instructions = """You are Ed-AI, an AI assistant with expertise in technology, legal document analysis and ITIL. I aim to be helpful, honest, and direct while maintaining a warm, conversational tone.

When analyzing legal documents, I:
- Always be positive and helpful
- Determine if the user is the customer or the vendor
- Use the Objectivesd outlined in section 3.2 of the contract to answer questions about the contract
- The customer is the Department of Education
- The vendor is LIFT Alliance
- Refer to the contract as the ED19024 contract
- Think step-by-step to ensure accuracy
- Always consider if the request requires a service variation
- Always consider if there will be an impact to base services
- Cite specific clauses, sections, and page references when possible
- Use clear, accessible language while maintaining legal precision
- Consider the broader context and practical implications
- Acknowledge limitations and uncertainties openly
- Structure my responses logically for easy understanding

I'm here to help you understand complex legal documents. Let me analyze the provided context and answer your question thoughtfully."""

def initialize_rag_system():
    """Initialize the RAG system with legal document processing"""
    global embedding_model, chroma_client, collection, ollama_client, claude_client, openai_client, jan_client
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded")
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma_client.get_or_create_collection(
            name="legal_documents",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB initialized")
        ollama_client = ollama.Client(host='http://localhost:11434')
        logger.info("Ollama client initialized")
        claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        if claude_api_key:
            claude_client = anthropic.Anthropic(api_key=claude_api_key)
            logger.info("Claude client initialized")
        else:
            logger.info("No ANTHROPIC_API_KEY found - Claude API not available")
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            openai.api_key = openai_api_key
            openai_client = openai
            logger.info("OpenAI client initialized")
        else:
            logger.info("No OPENAI_API_KEY found - OpenAI API not available")
        try:
            response = requests.get('http://localhost:1337/v1/models', timeout=5)
            if response.status_code == 200:
                jan_client = {
                    'base_url': 'http://localhost:1337',
                    'api_key': 'jan-ai-key'
                }
                logger.info("Jan.ai client initialized")
            else:
                logger.info("Jan.ai not running on localhost:1337")
        except Exception as e:
            logger.info(f"Jan.ai not available: {e}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'csv', 'json'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ingest_legal_document(file_path: str) -> dict:
    """Ingest a legal document using NeMo Retriever only"""
    try:
        logger.info(f"Processing legal document: {file_path} using NeMo Retriever")
        result = process_legal_pdf_nemo(file_path)
        chunks = result['chunks']
        extraction_method = result['extraction_method']
        documents = []
        metadatas = []
        ids = []
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            content = chunk['content']
            chunk_type = chunk['chunk_type']
            section_number = chunk.get('section_number')
            section_title = chunk.get('section_title')
            pages = chunk.get('pages', [])
            cross_references = chunk.get('cross_references', [])
            metadata = {
                'chunk_type': str(chunk_type) if chunk_type else '',
                'section_number': str(section_number) if section_number else '',
                'section_title': str(section_title) if section_title else '',
                'pages': ','.join(map(str, pages)) if pages else '',
                'cross_references': ','.join(cross_references) if cross_references else '',
                'extraction_method': str(extraction_method) if extraction_method else '',
                'character_count': str(len(content))
            }
            documents.append(content)
            metadatas.append(metadata)
            ids.append(chunk_id)
        if documents:
            embeddings = embedding_model.encode(documents).tolist()
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} chunks to ChromaDB")
        return {
            'success': True,
            'total_chunks': len(chunks),
            'extraction_method': extraction_method,
            'filename': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Error ingesting legal document: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat_interface.html')

@app.route('/configure')
def configure():
    return render_template('configure.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    import sys, traceback
    if not embedding_model or not collection:
        return jsonify({'error': 'RAG system not initialized'}), 500
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PDF, DOCX, TXT, CSV, JSON'}), 400
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result = ingest_legal_document(filepath)
        if result['success']:
            return jsonify({
                'message': f"Document uploaded and processed successfully. {result['total_chunks']} chunks created using {result['extraction_method']}.",
                'filename': result['filename'],
                'chunks': result['total_chunks']
            })
        else:
            return jsonify({'error': f"Failed to process document: {result['error']}"}), 500
    except Exception as e:
        traceback.print_exc()
        sys.stdout.flush()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/query', methods=['POST'])
def query():
    """Handle document queries"""
    try:
        question = request.form.get('question', '').strip()
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Search for relevant chunks
        results = collection.query(
            query_texts=[question],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results['documents'] or not results['documents'][0]:
            return jsonify({'answer': 'No relevant information found in the documents.'})
        
        # Prepare context from chunks
        context_chunks = results['documents'][0]
        context = '\n\n'.join(context_chunks)
        
        # Generate response based on current model
        if current_model == 'Claude Sonnet 4' and claude_client:
            # Use Claude API with user instructions
            prompt = f"""{user_instructions}

Context from the legal document:
{context}

Your question: {question}

Let me help you understand this:"""
            
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.content[0].text
            
        elif current_model == 'OpenAI GPT-4' and openai_client:
            # Use OpenAI API with user instructions
            prompt = f"""{user_instructions}\n\nContext from the legal document:\n{context}\n\nYour question: {question}\n\nLet me help you understand this:"""
            completion = openai_client.chat.completions.create(
                model=openai_model_name,
                messages=[{"role": "system", "content": user_instructions},
                         {"role": "user", "content": f"Context from the legal document:\n{context}\n\nYour question: {question}\nLet me help you understand this:"}],
                max_tokens=1000
            )
            answer = completion.choices[0].message.content
            
        elif current_model == 'Jan.ai GPT-4' and jan_client:
            # Use Jan.ai local API with user instructions
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {jan_client["api_key"]}'
            }
            
            payload = {
                'model': jan_model_name,
                'messages': [
                    {"role": "system", "content": user_instructions},
                    {"role": "user", "content": f"Context from the legal document:\n{context}\n\nYour question: {question}\nLet me help you understand this:"}
                ],
                'max_tokens': 1000,
                'temperature': 0.7
            }
            
            response = requests.post(
                f'{jan_client["base_url"]}/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
            else:
                raise Exception(f"Jan.ai API error: {response.status_code} - {response.text}")
        else:
            # Use local Ollama model with user instructions
            prompt = f"""<s>[INST] {user_instructions}

Context from the legal document:
{context}

Your question: {question}

Let me help you understand this: [/INST]"""
            
            # Map display names to actual model names for Ollama
            ollama_model = current_model
            if current_model in ['Claude Sonnet 4', 'OpenAI GPT-4', 'Jan.ai GPT-4']:
                ollama_model = 'mistral:7b'  # Fallback to local model if external APIs not available
            
            response = ollama_client.chat(
                model=ollama_model,
                messages=[{'role': 'user', 'content': prompt}]
            )
            answer = response['message']['content']
        
        # Prepare sources
        sources = []
        for metadata in results['metadatas'][0]:
            section_info = f"{metadata.get('section_number', 'Unknown')} - {metadata.get('section_title', 'Unknown')}"
            sources.append(section_info)
        
        return jsonify({
            'answer': answer,
            'sources': sources
        })
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@app.route('/api/status')
def api_status():
    """Check system status"""
    try:
        return jsonify({
            'embedding_model': embedding_model is not None,
            'chromadb': collection is not None,
            'ollama': ollama_client is not None,
            'claude': claude_client is not None,
            'openai': openai_client is not None,
            'jan_ai': jan_client is not None,
            'current_model': current_model
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models')
def api_models():
    """Get current model information"""
    try:
        available_models = ['mistral:7b', 'llama3.1:8b']
        if claude_client:
            available_models.append('Claude Sonnet 4')
        if openai_client:
            available_models.append('OpenAI GPT-4')
        if jan_client:
            available_models.append('Jan.ai GPT-4')
        
        return jsonify({
            'current_model': current_model,
            'available_models': available_models,
            'embedding_model': 'all-MiniLM-L6-v2',
            'claude_available': claude_client is not None,
            'openai_available': openai_client is not None,
            'jan_ai_available': jan_client is not None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """Switch between available models"""
    global current_model
    
    try:
        data = request.get_json()
        new_model = data.get('model')
        
        if not new_model:
            return jsonify({'error': 'No model specified'}), 400
        
        # Validate model availability
        available_models = ['mistral:7b', 'llama3.1:8b']
        if claude_client:
            available_models.append('Claude Sonnet 4')
        if openai_client:
            available_models.append('OpenAI GPT-4')
        if jan_client:
            available_models.append('Jan.ai GPT-4')
        
        if new_model not in available_models:
            return jsonify({'error': f'Model {new_model} not available'}), 400
        
        # Switch model
        current_model = new_model
        logger.info(f"Switched to model: {current_model}")
        
        return jsonify({
            'message': f'Switched to {current_model}',
            'current_model': current_model
        })
        
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents')
def api_documents():
    """Get list of ingested documents"""
    try:
        # Get all documents from ChromaDB
        results = collection.get()
        
        # Group by document (assuming filename is in metadata)
        documents = {}
        for i, metadata in enumerate(results['metadatas']):
            # Extract filename from chunk_id or use a default
            chunk_id = results['ids'][i]
            filename = chunk_id.split('_')[0] if '_' in chunk_id else 'Unknown'
            
            if filename not in documents:
                documents[filename] = {
                    'filename': filename,
                    'total_chunks': 0,
                    'file_type': '.pdf'
                }
            
            documents[filename]['total_chunks'] += 1
        
        return jsonify(list(documents.values()))
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify([])

@app.route('/api/documents/<filename>/chunks')
def api_document_chunks(filename):
    """Get chunks for a specific document"""
    try:
        # Get all chunks and filter by filename
        results = collection.get()
        
        chunks = []
        for i, (chunk_id, content, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            # Check if this chunk belongs to the requested document
            if filename in chunk_id or metadata.get('section_title', '').startswith(filename):
                chunks.append({
                    'index': i,
                    'text': content,
                    'length': len(content),
                    'chunk_type': metadata.get('chunk_type', 'Unknown'),
                    'section_number': metadata.get('section_number', 'Unknown'),
                    'section_title': metadata.get('section_title', 'Unknown'),
                    'pages': metadata.get('pages', ''),
                    'cross_references': metadata.get('cross_references', '')
                })
        
        return jsonify({
            'filename': filename,
            'total_chunks': len(chunks),
            'chunks': chunks
        })
        
    except Exception as e:
        logger.error(f"Error getting chunks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>/search')
def api_document_search(filename):
    """Search within a specific document"""
    try:
        query = request.args.get('q', '').strip()
        n_results = int(request.args.get('n', 10))
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Search in ChromaDB
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Filter results for the specific document
        filtered_results = []
        for i, (chunk_id, content, metadata, distance) in enumerate(zip(
            results['ids'][0], 
            results['documents'][0], 
            results['metadatas'][0],
            results['distances'][0]
        )):
            # Check if this chunk belongs to the requested document
            if filename in chunk_id or metadata.get('section_title', '').startswith(filename):
                filtered_results.append({
                    'index': i,
                    'text': content,
                    'length': len(content),
                    'similarity_score': 1 - distance,  # Convert distance to similarity
                    'chunk_type': metadata.get('chunk_type', 'Unknown'),
                    'section_number': metadata.get('section_number', 'Unknown'),
                    'section_title': metadata.get('section_title', 'Unknown')
                })
        
        return jsonify({
            'filename': filename,
            'query': query,
            'results': filtered_results
        })
        
    except Exception as e:
        logger.error(f"Error searching document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['DELETE'])
def api_delete_document(filename):
    """Delete a document and its chunks"""
    try:
        # Get all chunks and filter by filename
        results = collection.get()
        
        # Find chunks to delete
        chunks_to_delete = []
        for chunk_id in results['ids']:
            if filename in chunk_id:
                chunks_to_delete.append(chunk_id)
        
        # Delete chunks
        if chunks_to_delete:
            collection.delete(ids=chunks_to_delete)
            logger.info(f"Deleted {len(chunks_to_delete)} chunks for document {filename}")
        
        return jsonify({'message': f'Document {filename} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instructions', methods=['GET', 'POST'])
def api_instructions():
    """Get or set user instructions for the AI"""
    global user_instructions
    
    if request.method == 'GET':
        return jsonify({
            'instructions': user_instructions,
            'default_instructions': """You are Claude, an AI assistant with expertise in legal document analysis. I aim to be helpful, honest, and direct while maintaining a warm, conversational tone.

When analyzing legal documents, I:
- Think step-by-step to ensure accuracy
- Cite specific clauses, sections, and page references when possible
- Use clear, accessible language while maintaining legal precision
- Consider the broader context and practical implications
- Acknowledge limitations and uncertainties openly
- Structure my responses logically for easy understanding

I'm here to help you understand complex legal documents. Let me analyze the provided context and answer your question thoughtfully."""
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            new_instructions = data.get('instructions', '').strip()
            
            if not new_instructions:
                return jsonify({'error': 'Instructions cannot be empty'}), 400
            
            user_instructions = new_instructions
            logger.info("User instructions updated")
            
            return jsonify({
                'message': 'Instructions updated successfully',
                'instructions': user_instructions
            })
            
        except Exception as e:
            logger.error(f"Error updating instructions: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/instructions/reset', methods=['POST'])
def api_instructions_reset():
    """Reset instructions to default"""
    global user_instructions
    
    try:
        user_instructions = """You are Claude, an AI assistant with expertise in legal document analysis. I aim to be helpful, honest, and direct while maintaining a warm, conversational tone.

When analyzing legal documents, I:
- Think step-by-step to ensure accuracy
- Cite specific clauses, sections, and page references when possible
- Use clear, accessible language while maintaining legal precision
- Consider the broader context and practical implications
- Acknowledge limitations and uncertainties openly
- Structure my responses logically for easy understanding

I'm here to help you understand complex legal documents. Let me analyze the provided context and answer your question thoughtfully."""
        
        logger.info("Instructions reset to default")
        return jsonify({
            'message': 'Instructions reset to default',
            'instructions': user_instructions
        })
        
    except Exception as e:
        logger.error(f"Error resetting instructions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompt/templates')
def api_prompt_templates():
    """Get available prompt templates"""
    templates = {
        'legal_assistant': {
            'name': 'Legal Assistant',
            'description': 'Specialized for legal document analysis and interpretation',
            'prompt': 'You are a legal document assistant. Analyze the provided context carefully and provide accurate, well-reasoned answers based on the legal document content. When referencing specific clauses or sections, be precise.'
        },
        'general': {
            'name': 'General Assistant',
            'description': 'General purpose document analysis',
            'prompt': 'You are a helpful assistant. Answer questions based on the provided document context. Be clear and concise.'
        }
    }
    return jsonify(templates)

@app.route('/api/prompt', methods=['GET', 'POST'])
def api_prompt():
    """Get or set the current prompt"""
    if request.method == 'GET':
        # Return default prompt
        return jsonify({'prompt': 'You are a helpful assistant. Answer questions based on the provided document context.'})
    else:
        # Set new prompt (in a real app, you'd save this to a database)
        data = request.get_json()
        new_prompt = data.get('prompt', '')
        return jsonify({'message': 'Prompt updated successfully', 'prompt': new_prompt})

@app.route('/api/prompt/reset', methods=['POST'])
def api_prompt_reset():
    """Reset to default prompt"""
    default_prompt = 'You are a helpful assistant. Answer questions based on the provided document context.'
    return jsonify({'message': 'Prompt reset successfully', 'prompt': default_prompt})

@app.route('/contract')
def contract_viewer_page():
    return render_template('contract_viewer.html')

@app.route('/contract/latest')
def serve_latest_contract():
    """Serve the most recently uploaded PDF contract from the uploads directory."""
    try:
        upload_dir = app.config['UPLOAD_FOLDER']
        files = [f for f in os.listdir(upload_dir) if f.lower().endswith('.pdf')]
        if not files:
            return "No contract uploaded yet.", 404
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(upload_dir, f)))
        @after_this_request
        def add_header(response):
            response.headers['X-Frame-Options'] = 'ALLOWALL'
            return response
        return send_file(os.path.join(upload_dir, latest_file), mimetype='application/pdf')
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    # Initialize the RAG system
    if initialize_rag_system():
        print("✅ Legal Document RAG system initialized successfully")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to initialize Legal Document RAG system")
        exit(1)