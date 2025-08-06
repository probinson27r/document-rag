#!/bin/bash

# ED19024 HTTPS Development Server
# This script runs the application with HTTPS support

echo "🔐 ED19024 HTTPS Development Server"
echo "=================================="

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL is not installed. Please install it first:"
    echo "   macOS: brew install openssl"
    echo "   Ubuntu/Debian: sudo apt-get install openssl"
    echo "   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "❌ No virtual environment found. Please create one first:"
        echo "   python3 -m venv .venv"
        echo "   source .venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# Set environment variables
export DISABLE_AUTH=true

# Run the application with HTTPS
echo "🚀 Starting HTTPS server..."
python app.py --https

echo "✅ Server stopped." 