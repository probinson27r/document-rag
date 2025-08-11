#!/bin/bash

# EC2 Setup Script for Legal Document RAG System
# This script sets up an EC2 instance with all necessary dependencies

set -e

echo "🚀 Setting up EC2 instance for Legal Document RAG System..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y poppler-utils  # For PDF processing
sudo apt install -y tesseract-ocr  # For OCR if needed
sudo apt install -y nginx  # For reverse proxy
sudo apt install -y certbot python3-certbot-nginx  # For SSL certificates

# Install Node.js and npm (for any frontend tools)
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/legal-rag-app
sudo chown ubuntu:ubuntu /opt/legal-rag-app

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /opt/legal-rag-app
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install wheel setuptools

# Install specific versions for stability
pip install flask==2.3.3
pip install chromadb==0.4.18
pip install sentence-transformers==2.2.2
pip install anthropic==0.7.8
pip install openai==1.3.7
pip install ollama==0.1.7
pip install pdfplumber==0.10.3
pip install PyMuPDF==1.23.8
pip install PyPDF2==3.0.1
pip install python-docx==1.1.0
pip install reportlab==4.0.7
pip install requests==2.31.0
pip install boto3==1.34.0
pip install PyJWT==2.8.0
pip install cryptography==41.0.7
pip install flask-session==0.5.0
pip install langchain==0.0.350
pip install faiss-cpu==1.7.4
pip install protobuf==4.24.4

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p uploads
mkdir -p chroma_db
mkdir -p flask_session
mkdir -p logs

# Set up Nginx configuration
echo "🌐 Setting up Nginx..."
sudo tee /etc/nginx/sites-available/legal-rag << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static/ {
        alias /opt/legal-rag-app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Upload size limit
    client_max_body_size 50M;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/legal-rag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Create systemd service for the application
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/legal-rag.service << EOF
[Unit]
Description=Legal Document RAG System
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/legal-rag-app
Environment=PATH=/opt/legal-rag-app/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=app.py
ExecStart=/opt/legal-rag-app/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable legal-rag

# Create environment file template
echo "📝 Creating environment file template..."
tee /opt/legal-rag-app/.env.template << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
PRIVATE_GPT4_API_KEY=your-private-gpt4-api-key

# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Database Configuration
CHROMA_DB_PATH=./chroma_db

# Application Configuration
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=52428800
EOF

# Create deployment script
echo "📝 Creating deployment script..."
tee /opt/legal-rag-app/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Activate virtual environment
source venv/bin/activate

# Stop existing service
echo "🛑 Stopping existing service..."
sudo systemctl stop legal-rag || true

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start service
echo "🚀 Starting service..."
sudo systemctl start legal-rag

# Check status
echo "📋 Service status:"
sudo systemctl status legal-rag --no-pager

echo "✅ Deployment completed!"
echo "📄 Logs: sudo journalctl -u legal-rag -f"
EOF

chmod +x /opt/legal-rag-app/deploy.sh

# Create monitoring script
echo "📝 Creating monitoring script..."
tee /opt/legal-rag-app/monitor.sh << 'EOF'
#!/bin/bash

echo "📊 Legal Document RAG System Status"
echo "=================================="

# Service status
echo "🔧 Service Status:"
sudo systemctl is-active legal-rag

# Process status
echo "🔄 Process Status:"
pgrep -f "python.*app.py" && echo "✅ Application running" || echo "❌ Application not running"

# Port status
echo "🌐 Port Status:"
netstat -tlnp | grep :5001 || echo "❌ Port 5001 not listening"

# Disk usage
echo "💾 Disk Usage:"
df -h /opt/legal-rag-app

# Memory usage
echo "🧠 Memory Usage:"
free -h

# Recent logs
echo "📄 Recent Logs:"
sudo journalctl -u legal-rag --no-pager -n 20
EOF

chmod +x /opt/legal-rag-app/monitor.sh

# Set up log rotation
echo "📄 Setting up log rotation..."
sudo tee /etc/logrotate.d/legal-rag << EOF
/opt/legal-rag-app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload legal-rag
    endscript
}
EOF

# Create backup script
echo "📝 Creating backup script..."
tee /opt/legal-rag-app/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/legal-rag"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="legal-rag-backup-$DATE.tar.gz"

echo "💾 Creating backup: $BACKUP_FILE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop service
sudo systemctl stop legal-rag

# Create backup
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude='venv' \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    /opt/legal-rag-app

# Start service
sudo systemctl start legal-rag

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE"

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "legal-rag-backup-*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/legal-rag-app/backup.sh

# Set up cron jobs
echo "⏰ Setting up cron jobs..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/legal-rag-app/backup.sh") | crontab -
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/legal-rag-app/monitor.sh > /opt/legal-rag-app/logs/monitor.log 2>&1") | crontab -

# Set up firewall
echo "🔥 Setting up firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "✅ EC2 setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your application files to /opt/legal-rag-app/"
echo "2. Set up your environment variables in .env file"
echo "3. Run: cd /opt/legal-rag-app && ./deploy.sh"
echo "4. Check status: ./monitor.sh"
echo ""
echo "🔧 Useful commands:"
echo "- View logs: sudo journalctl -u legal-rag -f"
echo "- Restart service: sudo systemctl restart legal-rag"
echo "- Check status: sudo systemctl status legal-rag"
echo "- Monitor: ./monitor.sh"
echo "- Backup: ./backup.sh"
