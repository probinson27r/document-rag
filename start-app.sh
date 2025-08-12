#!/bin/bash

# ED19024 Application Starter Script
# Ensures correct virtual environment and starts the application

echo "🚀 ED19024 Legal Document RAG System"
echo "==================================="

# Deactivate any current virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "📦 Deactivating current virtual environment..."
    deactivate
fi

# Always use the fresh 'venv' directory (not .venv)
if [ -d "venv" ]; then
    echo "✅ Activating fresh 'venv' environment..."
    source venv/bin/activate
    echo "📍 Using Python: $(which python)"
    echo "📍 Virtual env: $VIRTUAL_ENV"
else
    echo "❌ Fresh 'venv' directory not found!"
    echo "💡 Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if ChromaDB works in this environment
echo "🔍 Testing ChromaDB compatibility..."
python -c "
import chromadb
try:
    client = chromadb.PersistentClient(path='./chroma_db')
    collection = client.get_or_create_collection('documents')
    print('✅ ChromaDB working correctly')
except Exception as e:
    print(f'❌ ChromaDB issue: {e}')
    exit(1)
" || exit 1

# Start the application
echo "🌐 Starting application..."
if [ "$1" = "--https" ]; then
    echo "🔐 HTTPS mode enabled"
    python app.py --https
else
    echo "🌐 HTTP mode"
    python app.py
fi
