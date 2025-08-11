#!/bin/bash
# Fix protobuf version conflict with unstructured packages
# This resolves the 'cannot import name runtime_version' error

set -e

echo "🔧 Fixing protobuf version conflict..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [ -d "venv" ]; then
        echo "📦 Activating virtual environment..."
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo "📦 Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "❌ No virtual environment found. Please create one first."
        exit 1
    fi
fi

echo "🔍 Current protobuf version:"
pip show protobuf | grep Version || echo "Protobuf not installed"

echo ""
echo "🚀 Upgrading protobuf to resolve compatibility issues..."

# Force upgrade protobuf to a compatible version
pip install --upgrade "protobuf>=4.25.0"

echo ""
echo "🔄 Reinstalling unstructured packages to ensure compatibility..."

# Reinstall unstructured packages
pip install --upgrade --force-reinstall unstructured unstructured_inference

echo ""
echo "✅ Testing the fix..."

# Test if the import works now
python << 'EOF'
try:
    from google.protobuf import runtime_version
    print("✅ protobuf runtime_version import successful")
    
    try:
        from unstructured.partition.pdf import partition_pdf
        print("✅ unstructured.partition.pdf import successful")
    except Exception as e:
        print(f"⚠️ unstructured import still has issues: {e}")
        
except Exception as e:
    print(f"❌ protobuf import still failing: {e}")
EOF

echo ""
echo "📋 Current package versions:"
pip show protobuf | grep Version
pip show unstructured | grep Version
pip show onnx | grep Version

echo ""
echo "🎯 Fix completed!"
echo ""
echo "If you still see issues:"
echo "1. Restart your application: python app.py"
echo "2. Try upgrading all packages: pip install --upgrade -r requirements.txt"
echo "3. Consider recreating the virtual environment if problems persist"
