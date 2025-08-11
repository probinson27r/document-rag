#!/bin/bash
# Quick fix for Private GPT-4 API key access
# This script sets up environment variables as a fallback

echo "🔧 Quick fix for Private GPT-4 API key access..."

# Check if running on EC2
if curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/ >/dev/null 2>&1; then
    echo "✅ Running on EC2 instance"
else
    echo "❌ This script should be run on the EC2 instance"
    echo "Usage: ssh to EC2 and run this script there"
    exit 1
fi

echo ""
echo "🔑 Setting up Private GPT-4 API key in environment file..."

# Navigate to application directory
cd /opt/legal-rag-app

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "# Environment variables for Legal Document RAG System" > .env
    echo "FLASK_ENV=production" >> .env
fi

echo ""
echo "📝 Please enter your Private GPT-4 API key:"
echo "(This will be stored in /opt/legal-rag-app/.env)"
read -s -p "Private GPT-4 API key: " PRIVATE_GPT4_KEY
echo ""

if [ -n "$PRIVATE_GPT4_KEY" ]; then
    # Remove any existing PRIVATE_GPT4_API_KEY line
    sed -i '/^PRIVATE_GPT4_API_KEY=/d' .env
    
    # Add the new key
    echo "PRIVATE_GPT4_API_KEY=$PRIVATE_GPT4_KEY" >> .env
    
    echo "✅ Private GPT-4 API key added to .env file"
    
    # Set proper permissions
    chmod 600 .env
    chown ubuntu:ubuntu .env
    
    echo "🔄 Restarting legal-rag service..."
    sudo systemctl restart legal-rag
    
    # Wait a moment and check status
    sleep 3
    if sudo systemctl is-active legal-rag >/dev/null; then
        echo "✅ Service restarted successfully"
        echo "🔍 Checking logs for Private GPT-4 initialization..."
        sudo journalctl -u legal-rag --no-pager -n 10 | grep -i "private.*gpt"
    else
        echo "❌ Service failed to start. Check logs:"
        sudo journalctl -u legal-rag --no-pager -n 20
    fi
else
    echo "❌ No API key entered. Exiting."
    exit 1
fi

echo ""
echo "🎯 Next steps:"
echo "1. Test the application: curl http://localhost:5001/health"
echo "2. Check logs: sudo journalctl -u legal-rag -f"
echo "3. For long-term: Set up AWS IAM role with ./setup-ec2-iam-secrets.sh"
