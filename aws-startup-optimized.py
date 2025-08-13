#!/usr/bin/env python3
"""
AWS-Optimized Application Startup
Optimized version of app.py with AWS-specific performance improvements
"""

import os
import multiprocessing

# Apply AWS performance optimizations before importing heavy libraries
def setup_aws_optimizations():
    """Setup performance optimizations for AWS deployment"""
    
    # CPU/Threading optimizations
    cpu_count = multiprocessing.cpu_count()
    optimal_threads = min(cpu_count, 4)
    
    os.environ.update({
        # Python optimizations
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        
        # NumPy/BLAS optimizations
        'OPENBLAS_NUM_THREADS': str(optimal_threads),
        'MKL_NUM_THREADS': str(optimal_threads),
        'NUMEXPR_MAX_THREADS': str(optimal_threads),
        
        # Tokenizers optimization (prevent deadlocks)
        'TOKENIZERS_PARALLELISM': 'false',
        
        # TensorFlow optimizations
        'TF_CPP_MIN_LOG_LEVEL': '2',
        'TF_NUM_INTRAOP_THREADS': str(optimal_threads),
        'TF_NUM_INTEROP_THREADS': '1',
        
        # HuggingFace cache optimization
        'TRANSFORMERS_CACHE': '/tmp/huggingface_cache',
        'HF_HOME': '/tmp/huggingface_cache',
        'TORCH_HOME': '/tmp/huggingface_cache',
    })
    
    # Create cache directories
    os.makedirs('/tmp/huggingface_cache', exist_ok=True)
    
    print(f"🚀 AWS optimizations applied (CPU cores: {cpu_count}, threads: {optimal_threads})")

# Apply optimizations before importing heavy libraries
setup_aws_optimizations()

# Now import PyTorch and optimize it
try:
    import torch
    
    # Optimize PyTorch for AWS
    cpu_count = multiprocessing.cpu_count()
    optimal_threads = min(cpu_count, 4)
    
    torch.set_num_threads(optimal_threads)
    torch.set_grad_enabled(False)  # Disable gradients for inference
    
    if hasattr(torch.backends, 'cudnn'):
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
    
    print(f"🔧 PyTorch optimized for AWS (threads: {optimal_threads})")
    
except ImportError:
    print("⚠️ PyTorch not available")

# Pre-load and cache the embedding model
def preload_embedding_model():
    """Pre-load the embedding model to avoid startup delays"""
    try:
        from sentence_transformers import SentenceTransformer
        
        print("📡 Pre-loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/tmp/huggingface_cache')
        
        # Warm up the model with a test encoding
        test_embedding = model.encode("initialization test")
        print(f"✅ Embedding model loaded (dimension: {len(test_embedding)})")
        
        return model
    except Exception as e:
        print(f"❌ Failed to pre-load embedding model: {e}")
        return None

# Pre-load model during startup
EMBEDDING_MODEL = preload_embedding_model()

# Now import the main application
if __name__ == '__main__':
    # Import the main app after optimizations
    print("🚀 Starting AWS-optimized Legal Document RAG system...")
    
    # Import and run the main application
    from app import app, initialize_rag_system
    
    # Override the embedding model if pre-loaded successfully
    if EMBEDDING_MODEL:
        import app as main_app
        main_app.embedding_model = EMBEDDING_MODEL
        print("✅ Using pre-loaded embedding model")
    
    # Initialize RAG system
    if initialize_rag_system():
        print("✅ RAG system initialized with AWS optimizations")
        
        # Run the application with AWS-optimized settings
        app.run(
            debug=False,  # Disable debug mode for performance
            host='0.0.0.0',
            port=5001,
            threaded=True,  # Enable threading for better concurrency
            use_reloader=False,  # Disable reloader for performance
        )
    else:
        print("❌ Failed to initialize RAG system")
        exit(1)
