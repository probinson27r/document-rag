#!/bin/bash

# Fix NumPy 2.0 Compatibility Issues
# This script fixes the AttributeError: `np.float_` was removed in NumPy 2.0

set -e

echo "🔧 Fixing NumPy 2.0 compatibility issues..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Consider activating one."
fi

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Uninstall current numpy if it exists
echo "🗑️ Removing current NumPy installation..."
pip uninstall numpy -y || true

# Install compatible NumPy version
echo "📦 Installing NumPy < 2.0.0..."
pip install "numpy<2.0.0"

# Reinstall key dependencies that might have NumPy conflicts
echo "🔄 Reinstalling key dependencies..."
pip install --force-reinstall "sentence-transformers>=2.2.0"
pip install --force-reinstall "chromadb>=0.4.0"
pip install --force-reinstall "faiss-cpu>=1.7.0"

# Verify NumPy version
echo "✅ Verifying NumPy version..."
python -c "import numpy as np; print(f'NumPy version: {np.__version__}')"

# Test key imports
echo "🧪 Testing key imports..."
python -c "
import numpy as np
import sentence_transformers
import chromadb
import faiss
print('✅ All imports successful!')
"

echo ""
echo "✅ NumPy compatibility fix completed!"
echo ""
echo "📋 Summary:"
echo "- Installed NumPy < 2.0.0"
echo "- Reinstalled sentence-transformers, chromadb, and faiss-cpu"
echo "- Verified all imports work correctly"
echo ""
echo "💡 If you still encounter issues:"
echo "1. Restart your Python environment"
echo "2. Clear any cached files: find . -name '*.pyc' -delete"
echo "3. Reinstall the virtual environment if needed"
