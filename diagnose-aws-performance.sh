#!/bin/bash

# AWS Deployment Performance Diagnostic Script
# This script helps identify performance bottlenecks in AWS deployment

echo "🔍 AWS Deployment Performance Diagnostic"
echo "========================================"
echo ""

# Check system resources
echo "📊 System Resources:"
echo "===================="
echo "CPU Info:"
nproc --all
echo "CPU cores available: $(nproc --all)"
echo ""

echo "Memory Info:"
free -h
echo ""

echo "Disk Space:"
df -h /
echo ""

echo "Load Average:"
uptime
echo ""

# Check Python/pip performance
echo "🐍 Python Environment:"
echo "======================"
echo "Python version:"
python3 --version
echo ""

echo "Virtual environment location:"
which python
echo ""

echo "Pip cache location:"
pip cache dir 2>/dev/null || echo "Pip cache info not available"
echo ""

# Check network performance
echo "🌐 Network Performance:"
echo "======================="
echo "Testing DNS resolution:"
time nslookup google.com
echo ""

echo "Testing internet connectivity:"
time curl -s -o /dev/null -w "Total time: %{time_total}s\n" https://httpbin.org/delay/1
echo ""

# Check key dependencies
echo "📦 Key Dependencies:"
echo "==================="
echo "ChromaDB status:"
if python3 -c "import chromadb; print('✅ ChromaDB imported successfully')" 2>/dev/null; then
    echo "ChromaDB: OK"
else
    echo "❌ ChromaDB import failed"
fi
echo ""

echo "SentenceTransformers status:"
if python3 -c "from sentence_transformers import SentenceTransformer; print('✅ SentenceTransformers imported successfully')" 2>/dev/null; then
    echo "SentenceTransformers: OK"
else
    echo "❌ SentenceTransformers import failed"
fi
echo ""

echo "PyTorch backend:"
python3 -c "
try:
    import torch
    print(f'PyTorch version: {torch.__version__}')
    print(f'CUDA available: {torch.cuda.is_available()}')
    print(f'MPS available: {torch.backends.mps.is_available() if hasattr(torch.backends, \"mps\") else \"N/A\"}')
    print(f'Device: {torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\")}')
except ImportError:
    print('❌ PyTorch not available')
"
echo ""

# Check storage performance
echo "💾 Storage Performance:"
echo "======================="
echo "Testing write performance:"
dd if=/dev/zero of=/tmp/test_write bs=1M count=100 2>&1 | grep -E "(copied|MB/s)"
rm -f /tmp/test_write
echo ""

echo "Testing read performance:"
sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || echo "Cannot clear cache (expected on non-root)"
dd if=/dev/zero of=/tmp/test_read bs=1M count=100 2>/dev/null
time dd if=/tmp/test_read of=/dev/null bs=1M 2>&1 | grep -E "(copied|MB/s)"
rm -f /tmp/test_read
echo ""

# Check application-specific performance
echo "🚀 Application Performance:"
echo "==========================="
echo "ChromaDB initialization time:"
time python3 -c "
import chromadb
from chromadb.config import Settings
client = chromadb.PersistentClient(
    path='./chroma_db',
    settings=Settings(anonymized_telemetry=False, allow_reset=True)
)
collection = client.get_or_create_collection(name='test_performance')
print('ChromaDB initialized')
" 2>/dev/null
echo ""

echo "Embedding model load time:"
time python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print('Embedding model loaded')
" 2>/dev/null
echo ""

# Check process information
echo "🔧 Process Information:"
echo "======================="
echo "Running Python processes:"
ps aux | grep python | grep -v grep
echo ""

echo "Memory usage by Python processes:"
ps aux | grep python | grep -v grep | awk '{print $4, $11}' | sort -nr
echo ""

# Performance recommendations
echo "💡 Performance Recommendations:"
echo "==============================="
echo "1. Check if AWS instance type has sufficient CPU/Memory"
echo "2. Verify ChromaDB is using persistent storage efficiently"  
echo "3. Ensure sentence-transformers models are cached locally"
echo "4. Consider using GPU-enabled instances for ML workloads"
echo "5. Check if swap memory is configured for large document processing"
echo "6. Verify network latency to external APIs (GPT-4, Google GenAI)"
echo ""

echo "📋 Next Steps:"
echo "=============="
echo "1. Compare these metrics with local development machine"
echo "2. Check AWS CloudWatch metrics for instance performance"
echo "3. Consider upgrading instance type if CPU/Memory constrained"
echo "4. Optimize model loading and caching strategies"
