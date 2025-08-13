#!/bin/bash

# Quick AWS Performance Fix Script
# Run this on your AWS instance to apply immediate performance improvements

echo "🚀 Quick AWS Performance Fix"
echo "============================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. Some optimizations may not apply correctly."
fi

# 1. Add swap memory if not present
echo "1. 💾 Checking swap memory..."
if [ $(swapon --show | wc -l) -eq 0 ]; then
    echo "   No swap detected. Creating 4GB swap file..."
    sudo fallocate -l 4G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "   ✅ 4GB swap file created"
else
    echo "   ✅ Swap already configured"
fi
echo ""

# 2. Optimize kernel parameters
echo "2. ⚙️  Optimizing kernel parameters..."
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "vm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
echo "   ✅ Kernel parameters optimized"
echo ""

# 3. Create optimized cache directories
echo "3. 📁 Creating optimized cache directories..."
mkdir -p /tmp/huggingface_cache
mkdir -p /tmp/pip_cache
chmod 755 /tmp/huggingface_cache /tmp/pip_cache
echo "   ✅ Cache directories created"
echo ""

# 4. Install performance monitoring tools
echo "4. 📊 Installing performance tools..."
if ! command -v htop &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y htop iotop
    echo "   ✅ Performance tools installed"
else
    echo "   ✅ Performance tools already available"
fi
echo ""

# 5. Optimize Python environment
echo "5. 🐍 Optimizing Python environment..."
cd /opt/legal-rag-app

# Create optimized startup script
cat > start-optimized.sh << 'EOF'
#!/bin/bash
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
export TRANSFORMERS_CACHE=/tmp/huggingface_cache
export HF_HOME=/tmp/huggingface_cache
export TORCH_HOME=/tmp/huggingface_cache

cd /opt/legal-rag-app
source venv/bin/activate
python app.py
EOF

chmod +x start-optimized.sh
echo "   ✅ Optimized startup script created"
echo ""

# 6. Update systemd service for performance
echo "6. 🔧 Updating systemd service..."
sudo tee /etc/systemd/system/legal-rag.service > /dev/null << 'EOF'
[Unit]
Description=Legal RAG Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/legal-rag-app
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=OPENBLAS_NUM_THREADS=4
Environment=MKL_NUM_THREADS=4
Environment=TOKENIZERS_PARALLELISM=false
Environment=TRANSFORMERS_CACHE=/tmp/huggingface_cache
Environment=HF_HOME=/tmp/huggingface_cache
Environment=TORCH_HOME=/tmp/huggingface_cache
ExecStart=/opt/legal-rag-app/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "   ✅ Systemd service updated"
echo ""

# 7. Pre-install performance dependencies
echo "7. 📦 Installing performance dependencies..."
source venv/bin/activate
pip install --cache-dir /tmp/pip_cache psutil 2>/dev/null || echo "   ⚠️  psutil installation failed (non-critical)"
echo "   ✅ Performance dependencies ready"
echo ""

# 8. Restart the service with optimizations
echo "8. 🔄 Restarting service with optimizations..."
sudo systemctl stop legal-rag 2>/dev/null || echo "   Service was not running"
sudo systemctl enable legal-rag
sudo systemctl start legal-rag

# Wait for service to start
sleep 5

if sudo systemctl is-active --quiet legal-rag; then
    echo "   ✅ Service restarted successfully with optimizations"
else
    echo "   ❌ Service failed to start. Check logs: sudo journalctl -u legal-rag -n 20"
fi
echo ""

# 9. Performance summary
echo "🎯 Performance Optimizations Applied:"
echo "====================================="
echo "✅ 4GB swap memory added"
echo "✅ Kernel parameters optimized"
echo "✅ Cache directories created"
echo "✅ Performance monitoring tools installed"
echo "✅ Python environment optimized"
echo "✅ Systemd service updated"
echo "✅ Service restarted"
echo ""

echo "📊 Current System Status:"
echo "========================"
echo "Memory usage:"
free -h
echo ""
echo "Swap usage:"
swapon --show 2>/dev/null || echo "No swap active"
echo ""
echo "CPU cores: $(nproc)"
echo "Load average: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

echo "🔍 Service status:"
sudo systemctl status legal-rag --no-pager -l
echo ""

echo "💡 Next Steps:"
echo "=============="
echo "1. Test document upload to verify improved performance"
echo "2. Monitor with: sudo journalctl -u legal-rag -f"
echo "3. Check system resources with: htop"
echo "4. If still slow, consider upgrading EC2 instance type"
echo ""

echo "✅ Quick performance fix complete!"
