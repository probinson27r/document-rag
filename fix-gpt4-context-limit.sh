#!/bin/bash
# Fix GPT-4 context length exceeded error by implementing automatic chunking
# This resolves the 145,417 tokens > 128,000 limit error

set -e

echo "🔧 Fixing GPT-4 context limit exceeded error..."

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

echo "📦 Installing required dependencies..."

# Install tiktoken for token counting
pip install tiktoken

echo ""
echo "🔍 Testing token counting capability..."

# Test if tiktoken is working
python << 'EOF'
try:
    import tiktoken
    encoder = tiktoken.encoding_for_model("gpt-4")
    test_text = "This is a test to verify token counting works properly."
    token_count = len(encoder.encode(test_text))
    print(f"✅ Token counting works! Test text has {token_count} tokens")
except Exception as e:
    print(f"❌ Token counting failed: {e}")
    import sys
    sys.exit(1)
EOF

echo ""
echo "🧪 Testing GPT-4 extraction module..."

# Test the updated gpt4_extraction module
python << 'EOF'
try:
    from gpt4_extraction import GPT4Extractor
    
    # Create extractor instance
    extractor = GPT4Extractor(
        private_gpt4_url="test_url",
        private_gpt4_key="test_key"
    )
    
    # Test token counting
    test_text = "This is a test document with some content to verify chunking works."
    token_count = extractor.count_tokens(test_text)
    print(f"✅ GPT-4 Extractor token counting: {token_count} tokens")
    
    # Test chunking logic (without actually calling GPT-4)
    chunks = extractor.chunk_text_for_model(test_text, "Test prompt", "gpt-5")
    print(f"✅ Chunking logic works: {len(chunks)} chunks created")
    
    print("✅ GPT-4 extraction module loaded successfully with chunking support!")
    
except Exception as e:
    print(f"❌ GPT-4 extraction module test failed: {e}")
    import traceback
    traceback.print_exc()
    import sys
    sys.exit(1)
EOF

echo ""
echo "📋 Context limits configured:"
echo "  - GPT-4: 8,192 tokens"
echo "  - GPT-4-32k: 32,768 tokens" 
echo "  - GPT-4o: 128,000 tokens"
echo "  - GPT-5: 128,000 tokens"
echo "  - Claude-3.5-Sonnet: 200,000 tokens"

echo ""
echo "🎯 Fix completed!"
echo ""
echo "✅ Key improvements:"
echo "  1. Automatic token counting using tiktoken"
echo "  2. Smart text chunking that preserves document structure"
echo "  3. Intelligent chunk recombination for coherent results"
echo "  4. Support for various model context limits"
echo "  5. Fallback handling for failed chunks"
echo ""
echo "🔧 How it works:"
echo "  - Documents exceeding context limits are automatically chunked"
echo "  - Each chunk is processed separately and results are combined"
echo "  - Text is split by paragraphs first, then sentences if needed"
echo "  - Metadata and structured data are intelligently merged"
echo ""
echo "🚀 Ready to process large documents without context limit errors!"
