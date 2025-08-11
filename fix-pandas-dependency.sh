#!/bin/bash
# Quick fix for missing pandas dependency
# This script installs pandas in the existing virtual environment

set -e

echo "🐼 Fixing missing pandas dependency..."

# Check if we're on EC2
if curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/ >/dev/null 2>&1; then
    echo "✅ Running on EC2 instance"
else
    echo "ℹ️  Not on EC2 - you can run this script locally too"
fi

# Navigate to application directory
if [ -d "/opt/legal-rag-app" ]; then
    cd /opt/legal-rag-app
    echo "📂 Working in: /opt/legal-rag-app"
elif [ -f "app.py" ]; then
    echo "📂 Working in: $(pwd)"
else
    echo "❌ Cannot find application directory. Please run this from the app directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please ensure venv directory exists."
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing pandas..."
pip install pandas

echo "🔍 Verifying pandas installation..."
python -c "import pandas as pd; print(f'✅ Pandas {pd.__version__} installed successfully')"

# If this is on EC2, restart the service
if [ -f "/etc/systemd/system/legal-rag.service" ]; then
    echo "🔄 Restarting legal-rag service..."
    sudo systemctl restart legal-rag
    
    # Wait and check status
    sleep 3
    if sudo systemctl is-active legal-rag >/dev/null; then
        echo "✅ Service restarted successfully"
        
        echo "🔍 Checking recent logs for pandas-related errors..."
        if sudo journalctl -u legal-rag --no-pager -n 10 | grep -i "pandas\|module.*found" >/dev/null; then
            echo "📋 Recent logs:"
            sudo journalctl -u legal-rag --no-pager -n 10 | grep -i "pandas\|module.*found"
        else
            echo "✅ No pandas-related errors in recent logs"
        fi
    else
        echo "❌ Service failed to start. Check logs:"
        sudo journalctl -u legal-rag --no-pager -n 20
    fi
else
    echo "ℹ️  Not running as a systemd service - you may need to restart your application manually"
fi

echo ""
echo "🎯 Pandas dependency fixed! Next steps:"
echo "1. Test CSV file processing functionality"
echo "2. Check application logs: sudo journalctl -u legal-rag -f"
echo "3. Test health endpoint: curl http://localhost:5001/health"
