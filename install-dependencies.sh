#!/bin/bash

# Install Dependencies for Legal RAG App
echo "📦 Installing Dependencies for Legal RAG App"
echo "============================================"

# Check if running on EC2
if [ ! -f /sys/hypervisor/uuid ] || [ ! -f /etc/cloud/cloud.cfg ]; then
    echo "⚠️  This script should be run ON your EC2 instance"
    echo "SSH to your EC2 instance first: ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
    exit 1
fi

APP_DIR="/opt/legal-rag-app"

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory $APP_DIR not found!"
    echo "Make sure the application is deployed first."
    exit 1
fi

cd "$APP_DIR"
echo "📍 Working in: $(pwd)"

# Stop the service
echo "🛑 Stopping legal-rag service..."
sudo systemctl stop legal-rag

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    echo "Creating basic requirements.txt..."
    cat > requirements.txt << 'EOF'
anthropic
chromadb
faiss-cpu
flask
flask-session
langchain
ollama
openai
pdfplumber
protobuf==4.24.4
PyMuPDF
PyPDF2
python-docx
reportlab
requests
sentence-transformers
boto3
PyJWT
cryptography
numpy<2.0.0
EOF
    echo "✅ Basic requirements.txt created"
fi

# Remove existing venv if it's broken
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    sudo rm -rf venv
fi

# Create fresh virtual environment
echo "🔧 Creating fresh virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies with specific options for memory-constrained environments
echo "📦 Installing dependencies..."
echo "This may take several minutes..."

# Install dependencies in stages to avoid memory issues
pip install --no-cache-dir flask flask-session requests
pip install --no-cache-dir "numpy<2.0.0"
pip install --no-cache-dir anthropic openai
pip install --no-cache-dir boto3 PyJWT cryptography
pip install --no-cache-dir pdfplumber PyMuPDF PyPDF2 python-docx reportlab
pip install --no-cache-dir "protobuf==4.24.4"

# Install heavier packages separately
echo "📦 Installing machine learning packages (this may take longer)..."
pip install --no-cache-dir sentence-transformers
pip install --no-cache-dir chromadb
pip install --no-cache-dir faiss-cpu
pip install --no-cache-dir langchain
pip install --no-cache-dir ollama

echo "✅ Dependencies installed successfully"

# Verify Flask installation
echo "🔍 Verifying Flask installation..."
python -c "import flask; print(f'Flask version: {flask.__version__}')"

# Set proper permissions
echo "🔧 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu "$APP_DIR"

# Start the service
echo "🚀 Starting legal-rag service..."
sudo systemctl start legal-rag

# Wait for startup
sleep 5

# Check service status
echo "📊 Service status:"
sudo systemctl status legal-rag --no-pager -l

echo ""
echo "🧪 Testing application..."
sleep 2
HEALTH_TEST=$(curl -s -w "Status: %{http_code}" http://localhost:5001/health 2>/dev/null || echo "Status: Failed")
echo "$HEALTH_TEST"

if echo "$HEALTH_TEST" | grep -q "Status: 200"; then
    echo "✅ Application is working!"
    echo "🌐 ALB should now be able to reach the application"
else
    echo "❌ Application still not responding. Check logs:"
    echo "sudo journalctl -u legal-rag -f"
fi

echo ""
echo "🏁 Dependency installation completed!"
echo ""
echo "💡 If issues persist, check:"
echo "1. Service logs: sudo journalctl -u legal-rag -f"
echo "2. Virtual environment: source venv/bin/activate && python -c 'import flask'"
echo "3. Manual start: cd $APP_DIR && source venv/bin/activate && python app.py --host 0.0.0.0 --port 5001"
