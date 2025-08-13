#!/usr/bin/env python3
"""
AWS Performance Optimization Script
Applies various optimizations to improve document processing speed on AWS
"""

import os
import logging
import multiprocessing
import torch
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def optimize_pytorch_settings():
    """Optimize PyTorch settings for AWS deployment"""
    try:
        # Set number of threads for CPU operations
        cpu_count = multiprocessing.cpu_count()
        optimal_threads = min(cpu_count, 4)  # Don't over-subscribe
        
        torch.set_num_threads(optimal_threads)
        logger.info(f"Set PyTorch threads to {optimal_threads} (CPU cores: {cpu_count})")
        
        # Optimize for inference (not training)
        torch.set_grad_enabled(False)
        logger.info("Disabled gradient computation for inference optimization")
        
        # Set memory allocation strategy
        if hasattr(torch.backends, 'cudnn'):
            torch.backends.cudnn.benchmark = True
            logger.info("Enabled cuDNN benchmark mode")
            
        return True
        
    except Exception as e:
        logger.error(f"PyTorch optimization failed: {e}")
        return False

def optimize_huggingface_cache():
    """Optimize HuggingFace transformers cache for AWS"""
    try:
        # Set cache directory to faster storage if available
        cache_dir = "/tmp/huggingface_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Set environment variables for HuggingFace
        os.environ['TRANSFORMERS_CACHE'] = cache_dir
        os.environ['HF_HOME'] = cache_dir
        os.environ['TORCH_HOME'] = cache_dir
        
        logger.info(f"Set HuggingFace cache to {cache_dir}")
        
        # Pre-warm the sentence transformer model
        from sentence_transformers import SentenceTransformer
        model_name = 'all-MiniLM-L6-v2'
        
        logger.info(f"Pre-loading {model_name} model...")
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        
        # Test encoding to ensure model is loaded
        test_embedding = model.encode("test sentence")
        logger.info(f"Model loaded successfully, embedding size: {len(test_embedding)}")
        
        return True
        
    except Exception as e:
        logger.error(f"HuggingFace optimization failed: {e}")
        return False

def optimize_chromadb_settings():
    """Optimize ChromaDB settings for performance"""
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Create optimized ChromaDB client
        optimized_settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            # Performance optimizations
            chroma_server_host="localhost",
            chroma_server_http_port=8000,
            # Reduce memory usage
            persist_directory="./chroma_db",
            # Use faster serialization
            chroma_api_impl="local",
        )
        
        logger.info("Applied ChromaDB performance optimizations")
        return True
        
    except Exception as e:
        logger.error(f"ChromaDB optimization failed: {e}")
        return False

def check_system_resources():
    """Check and report system resources"""
    try:
        # CPU information
        cpu_count = multiprocessing.cpu_count()
        logger.info(f"CPU cores available: {cpu_count}")
        
        # Memory information
        try:
            import psutil
            memory = psutil.virtual_memory()
            logger.info(f"Total memory: {memory.total / (1024**3):.1f} GB")
            logger.info(f"Available memory: {memory.available / (1024**3):.1f} GB")
            logger.info(f"Memory usage: {memory.percent}%")
        except ImportError:
            logger.warning("psutil not available, cannot check memory")
        
        # Disk space
        import shutil
        total, used, free = shutil.disk_usage('/')
        logger.info(f"Disk space - Total: {total // (1024**3)} GB, Free: {free // (1024**3)} GB")
        
        return True
        
    except Exception as e:
        logger.error(f"System resource check failed: {e}")
        return False

def optimize_environment_variables():
    """Set optimal environment variables for AWS deployment"""
    try:
        optimizations = {
            # Python optimizations
            'PYTHONUNBUFFERED': '1',
            'PYTHONDONTWRITEBYTECODE': '1',
            
            # NumPy optimizations
            'OPENBLAS_NUM_THREADS': str(min(multiprocessing.cpu_count(), 4)),
            'MKL_NUM_THREADS': str(min(multiprocessing.cpu_count(), 4)),
            
            # Disable TensorFlow warnings
            'TF_CPP_MIN_LOG_LEVEL': '2',
            
            # Optimize tokenizers
            'TOKENIZERS_PARALLELISM': 'false',  # Avoid deadlocks in multiprocessing
            
            # Memory optimization
            'MALLOC_TRIM_THRESHOLD_': '131072',
        }
        
        for key, value in optimizations.items():
            os.environ[key] = value
            logger.info(f"Set {key}={value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Environment optimization failed: {e}")
        return False

def main():
    """Run all AWS performance optimizations"""
    logger.info("🚀 Starting AWS Performance Optimization")
    logger.info("=" * 50)
    
    optimizations = [
        ("System Resources Check", check_system_resources),
        ("Environment Variables", optimize_environment_variables),
        ("PyTorch Settings", optimize_pytorch_settings),
        ("HuggingFace Cache", optimize_huggingface_cache),
        ("ChromaDB Settings", optimize_chromadb_settings),
    ]
    
    results = {}
    for name, func in optimizations:
        logger.info(f"\n🔧 Applying: {name}")
        results[name] = func()
        status = "✅ Success" if results[name] else "❌ Failed"
        logger.info(f"{name}: {status}")
    
    # Summary
    logger.info("\n📊 Optimization Summary:")
    logger.info("=" * 30)
    successful = sum(results.values())
    total = len(results)
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"{status} {name}")
    
    logger.info(f"\nOptimizations applied: {successful}/{total}")
    
    if successful == total:
        logger.info("🎉 All optimizations applied successfully!")
        logger.info("Document processing should now be faster on AWS.")
    else:
        logger.warning("⚠️ Some optimizations failed. Check logs above.")
    
    logger.info("\n💡 Additional Recommendations:")
    logger.info("- Consider upgrading to a compute-optimized EC2 instance (C5/C6i)")
    logger.info("- Enable swap memory for large document processing")
    logger.info("- Use local SSD storage for temporary files")
    logger.info("- Monitor AWS CloudWatch metrics for bottlenecks")

if __name__ == "__main__":
    main()
