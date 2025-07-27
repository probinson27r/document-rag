from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
from datetime import datetime

# Import our RAG system (assuming it's in the same directory)
from document_rag import DocumentRAG

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv', '.json'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize RAG system
rag = DocumentRAG()

def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main interface"""
    setup_status = rag.check_setup()
    documents = rag.list_documents()
    return render_template('index.html', 
                         setup_status=setup_status, 
                         documents=documents)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Ingest the document
        result = rag.ingest_document(filepath)
        
        if "Successfully ingested" in result:
            flash(f'Document uploaded and processed: {result}', 'success')
        else:
            flash(f'Error processing document: {result}', 'error')
    else:
        flash('Invalid file type. Allowed types: PDF, DOCX, TXT, CSV, JSON', 'error')
    
    return redirect(url_for('index'))

@app.route('/query', methods=['POST'])
def query_documents():
    """Handle document queries"""
    question = request.form.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'No question provided'})
    
    # Query the RAG system
    result = rag.query(question)
    
    return jsonify({
        'answer': result['answer'],
        'sources': result['sources'],
        'context_used': result['context_used'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/documents')
def api_list_documents():
    """API endpoint to list documents"""
    return jsonify(rag.list_documents())

@app.route('/api/documents/<filename>', methods=['DELETE'])
def api_delete_document(filename):
    """API endpoint to delete a document"""
    result = rag.delete_document(filename)
    
    if "Successfully deleted" in result:
        return jsonify({'success': True, 'message': result})
    else:
        return jsonify({'success': False, 'error': result})

@app.route('/api/search')
def api_search():
    """API endpoint for document search"""
    query = request.args.get('q', '')
    n_results = int(request.args.get('n', 5))
    
    if not query:
        return jsonify({'error': 'No query provided'})
    
    results = rag.search_documents(query, n_results)
    return jsonify(results)

@app.route('/api/status')
def api_status():
    """API endpoint to check system status"""
    return jsonify(rag.check_setup())

def create_template():
    """Create the HTML template file"""
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document RAG System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .status {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .status-item {
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        }
        .status-ok { background-color: #d4edda; color: #155724; }
        .status-error { background-color: #f8d7da; color: #721c24; }
        .upload-section {
            border: 2px dashed #ddd;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        .query-section {
            margin-bottom: 20px;
        }
        .query-input {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .query-button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        .query-button:hover {
            background-color: #0056b3;
        }
        .answer-section {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            display: none;
        }
        .documents-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .document-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .delete-btn {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        .flash-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .flash-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Document RAG System</h1>
        
        <!-- System Status -->
        <div class="status">
            <div class="status-item {{ 'status-ok' if setup_status.ollama_available else 'status-error' }}">
                Ollama: {{ '✓' if setup_status.ollama_available else '✗' }}
            </div>
            <div class="status-item {{ 'status-ok' if setup_status.model_available else 'status-error' }}">
                Model: {{ '✓' if setup_status.model_available else '✗' }}
            </div>
            <div class="status-item {{ 'status-ok' if setup_status.embedding_model_loaded else 'status-error' }}">
                Embeddings: {{ '✓' if setup_status.embedding_model_loaded else '✗' }}
            </div>
            <div class="status-item {{ 'status-ok' if setup_status.chroma_db_initialized else 'status-error' }}">
                Database: {{ '✓' if setup_status.chroma_db_initialized else '✗' }}
            </div>
        </div>

        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
    </div>

    <!-- Upload Section -->
    <div class="container">
        <h2>Upload Documents</h2>
        <div class="upload-section">
            <form method="post" enctype="multipart/form-data" action="/upload">
                <input type="file" name="file" accept=".pdf,.docx,.txt,.csv,.json" required>
                <br><br>
                <button type="submit">Upload and Process</button>
            </form>
            <p>Supported formats: PDF, DOCX, TXT, CSV, JSON</p>
        </div>
    </div>

    <!-- Query Section -->
    <div class="container">
        <h2>Query Documents</h2>
        <div class="query-section">
            <input type="text" class="query-input" id="questionInput" placeholder="Ask a question about your documents...">
            <button class="query-button" onclick="queryDocuments()">Ask Question</button>
            
            <div class="loading" id="loading">
                <p>Generating answer...</p>
            </div>
            
            <div class="answer-section" id="answerSection">
                <h3>Answer:</h3>
                <div id="answer"></div>
                <h4>Sources:</h4>
                <div id="sources"></div>
            </div>
        </div>
    </div>

    <!-- Documents List -->
    <div class="container">
        <h2>Uploaded Documents ({{ documents|length }})</h2>
        <div class="documents-list">
            {% for doc in documents %}
            <div class="document-item">
                <div>
                    <strong>{{ doc.filename }}</strong> ({{ doc.file_type }})
                    <br>
                    <small>{{ doc.total_chunks }} chunks, processed {{ doc.processed_time }}</small>
                </div>
                <button class="delete-btn" onclick="deleteDocument('{{ doc.filename }}')">Delete</button>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function queryDocuments() {
            const question = document.getElementById('questionInput').value.trim();
            if (!question) return;
            
            const loading = document.getElementById('loading');
            const answerSection = document.getElementById('answerSection');
            
            loading.style.display = 'block';
            answerSection.style.display = 'none';
            
            fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `question=${encodeURIComponent(question)}`
            })
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                document.getElementById('answer').innerHTML = data.answer.replace(/\\n/g, '<br>');
                document.getElementById('sources').innerHTML = data.sources.map(source => 
                    `<span style="background-color: #e9ecef; padding: 2px 6px; border-radius: 3px; margin-right: 5px;">${source}</span>`
                ).join('');
                
                answerSection.style.display = 'block';
            })
            .catch(error => {
                loading.style.display = 'none';
                alert('Error: ' + error);
            });
        }
        
        function deleteDocument(filename) {
            if (confirm(`Are you sure you want to delete ${filename}?`)) {
                fetch(`/api/documents/${filename}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting document: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error: ' + error);
                });
            }
        }
        
        // Allow Enter key to submit query
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                queryDocuments();
            }
        });
    </script>
</body>
</html>'''
    
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w') as f:
        f.write(template_content)

if __name__ == '__main__':
    # Create templates directory and save the template
    create_template()
    
    print("Document RAG System - Flask Web Interface")
    print("=" * 50)
    print("Make sure Ollama is running first!")
    print("Web interface will be available at: http://localhost:8888")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8888)