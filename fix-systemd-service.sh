#!/bin/bash

# Fix Systemd Service Configuration for Legal RAG App
echo "🔧 Fixing Systemd Service Configuration"
echo "======================================="

# Check if running on EC2
if [ ! -f /sys/hypervisor/uuid ] || [ ! -f /etc/cloud/cloud.cfg ]; then
    echo "⚠️  This script should be run ON your EC2 instance"
    echo "SSH to your EC2 instance first: ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
    exit 1
fi

APP_DIR="/opt/legal-rag-app"
SERVICE_FILE="/etc/systemd/system/legal-rag.service"

echo "📍 Application directory: $APP_DIR"
echo "📍 Service file: $SERVICE_FILE"
echo ""

# Stop the service if it's running
echo "🛑 Stopping legal-rag service..."
sudo systemctl stop legal-rag 2>/dev/null || true

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory $APP_DIR not found!"
    echo "Make sure the application is deployed first."
    exit 1
fi

# Check if app.py exists
if [ ! -f "$APP_DIR/app.py" ]; then
    echo "❌ app.py not found in $APP_DIR"
    echo "Make sure the application is deployed correctly."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$APP_DIR/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    cd "$APP_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed"
else
    echo "✅ Virtual environment found"
fi

# Create the correct systemd service file
echo "🔧 Creating correct systemd service configuration..."
sudo tee "$SERVICE_FILE" > /dev/null << 'EOF'
[Unit]
Description=Legal Document RAG System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/legal-rag-app
Environment=PATH=/opt/legal-rag-app/venv/bin
ExecStart=/opt/legal-rag-app/venv/bin/python app.py --host 0.0.0.0 --port 5001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created"

# Set proper permissions
echo "🔧 Setting proper permissions..."
sudo chown -R ubuntu:ubuntu "$APP_DIR"
sudo chmod +x "$APP_DIR/app.py" 2>/dev/null || true

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "⚡ Enabling legal-rag service..."
sudo systemctl enable legal-rag

# Start the service
echo "🚀 Starting legal-rag service..."
sudo systemctl start legal-rag

# Wait a moment for startup
sleep 3

# Check service status
echo "📊 Service status:"
sudo systemctl status legal-rag --no-pager -l

echo ""
echo "🔌 Port binding check:"
PORT_BINDING=$(sudo netstat -tlnp | grep :5001 || echo "None")
if [ "$PORT_BINDING" != "None" ]; then
    echo "$PORT_BINDING"
    
    if echo "$PORT_BINDING" | grep -q "0.0.0.0:5001"; then
        echo "✅ App is binding to all interfaces (0.0.0.0:5001)"
    else
        echo "⚠️  App binding pattern: $PORT_BINDING"
    fi
else
    echo "❌ Nothing listening on port 5001"
fi

echo ""
echo "🧪 Testing health endpoint:"
sleep 2
HEALTH_TEST=$(curl -s -w "Status: %{http_code}" http://localhost:5001/health 2>/dev/null || echo "Status: Failed")
echo "$HEALTH_TEST"

if echo "$HEALTH_TEST" | grep -q "Status: 200"; then
    echo "✅ Health endpoint working!"
else
    echo "❌ Health endpoint failed. Check logs:"
    echo "sudo journalctl -u legal-rag -f"
fi

echo ""
echo "🏁 Systemd service fix completed!"
echo ""
echo "💡 Useful commands:"
echo "Check status: sudo systemctl status legal-rag"
echo "View logs: sudo journalctl -u legal-rag -f"
echo "Restart: sudo systemctl restart legal-rag"
echo "Stop: sudo systemctl stop legal-rag"
