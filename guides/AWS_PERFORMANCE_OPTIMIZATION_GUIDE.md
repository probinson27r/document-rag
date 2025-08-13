# AWS Performance Optimization Guide

## 🐌 Problem: Slow Document Processing on AWS

Document processing is significantly slower on AWS compared to local development. This guide provides comprehensive solutions.

## 🔍 Common Causes

### 1. **Instance Type Limitations**
- **Problem**: T2/T3 instances have burstable CPU that throttles under sustained load
- **Solution**: Upgrade to compute-optimized instances (C5, C6i, M5, M6i)

### 2. **Memory Constraints**
- **Problem**: Insufficient RAM causes swapping, especially for ML models
- **Solution**: Ensure at least 8GB RAM, preferably 16GB+ for large documents

### 3. **Model Loading Overhead**
- **Problem**: SentenceTransformers and PyTorch models reload on every request
- **Solution**: Pre-load and cache models in memory

### 4. **Storage Performance**
- **Problem**: EBS gp2 volumes have limited IOPS
- **Solution**: Use gp3 or local SSD storage for temporary files

### 5. **CPU Threading Issues**
- **Problem**: Default threading settings may not be optimal for AWS
- **Solution**: Optimize thread counts for available CPU cores

## 🚀 Quick Fixes

### 1. Run Performance Diagnostic
```bash
./diagnose-aws-performance.sh
```

### 2. Apply Optimizations
```bash
python3 optimize-aws-performance.py
```

### 3. Use Optimized Startup
```bash
python3 aws-startup-optimized.py
```

## 🔧 Detailed Solutions

### Instance Type Optimization

**Current Recommended Instance Types:**
- **Small deployments**: `t3.large` (2 vCPU, 8GB RAM)
- **Medium deployments**: `c5.xlarge` (4 vCPU, 8GB RAM) 
- **Large deployments**: `c5.2xlarge` (8 vCPU, 16GB RAM)
- **High performance**: `c6i.2xlarge` (8 vCPU, 16GB RAM)

**Storage Optimization:**
- Use `gp3` volumes with 3000+ IOPS
- Consider instance store for temporary files (faster but not persistent)

### Memory Optimization

**Add Swap Memory:**
```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Monitor Memory Usage:**
```bash
# Check memory usage
free -h
# Check swap usage  
swapon --show
```

### Application-Level Optimizations

**1. Pre-load Models**
```python
# In app.py initialization
from sentence_transformers import SentenceTransformer

# Pre-load model globally
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
```

**2. Optimize PyTorch Settings**
```python
import torch
import multiprocessing

# Set optimal thread count
cpu_count = multiprocessing.cpu_count()
torch.set_num_threads(min(cpu_count, 4))

# Disable gradients for inference
torch.set_grad_enabled(False)
```

**3. Cache Model Downloads**
```bash
# Set cache directory to faster storage
export TRANSFORMERS_CACHE="/tmp/huggingface_cache"
export HF_HOME="/tmp/huggingface_cache"
```

### System-Level Optimizations

**1. Update systemd service for performance:**
```ini
[Unit]
Description=Legal RAG Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/legal-rag-app
Environment=PYTHONUNBUFFERED=1
Environment=OPENBLAS_NUM_THREADS=4
Environment=TOKENIZERS_PARALLELISM=false
ExecStart=/opt/legal-rag-app/venv/bin/python aws-startup-optimized.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**2. Optimize kernel parameters:**
```bash
# Add to /etc/sysctl.conf
vm.swappiness=10
vm.vfs_cache_pressure=50
```

### Network Optimization

**1. Regional Considerations:**
- Ensure EC2 instance is in same region as your users
- Use CloudFront for static content caching

**2. API Latency:**
- Private GPT-4: Usually fast (same region)
- Google GenAI: May have higher latency from AWS
- Consider API timeout optimizations

## 📊 Performance Monitoring

### CloudWatch Metrics to Monitor
- **CPUUtilization**: Should be < 80% sustained
- **MemoryUtilization**: Should be < 85%
- **DiskReadOps/DiskWriteOps**: Monitor for bottlenecks
- **NetworkIn/NetworkOut**: Check for bandwidth limits

### Application Metrics
- Document processing time per MB
- Model loading time
- Memory usage growth over time
- API response times

### Custom Monitoring Script
```bash
# Add to crontab for regular monitoring
*/5 * * * * /opt/legal-rag-app/diagnose-aws-performance.sh >> /var/log/performance.log
```

## 🎯 Expected Performance Improvements

| Optimization | Performance Gain | Effort |
|-------------|------------------|---------|
| Instance upgrade (t3.small → c5.large) | 2-3x faster | Low |
| Model pre-loading | 5-10x faster startup | Medium |
| Memory optimization | 20-50% faster | Low |
| Storage upgrade (gp2 → gp3) | 10-30% faster | Low |
| Threading optimization | 10-20% faster | Low |

## 🔄 Deployment Updates

### Update GitHub Actions for Performance

Add to `.github/workflows/deploy.yml`:

```yaml
- name: Apply AWS Performance Optimizations
  run: |
    ssh -i ssh_key -o StrictHostKeyChecking=no ubuntu@${{ secrets.EC2_INSTANCE_IP }} "
      cd /opt/legal-rag-app &&
      python3 optimize-aws-performance.py &&
      sudo systemctl restart legal-rag
    "
```

### Monitor After Deployment
```bash
# Check application logs
sudo journalctl -u legal-rag -f

# Monitor system resources
htop

# Test document processing speed
curl -X POST -F 'file=@test.pdf' http://localhost:5001/upload
```

## 🆘 Troubleshooting

### If Still Slow After Optimizations

1. **Check Instance Limits:**
   ```bash
   # Check if T-series instance is throttled
   aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUCreditBalance --dimensions Name=InstanceId,Value=i-1234567890abcdef0 --start-time 2024-01-01T00:00:00Z --end-time 2024-01-01T23:59:59Z --period 3600 --statistics Average
   ```

2. **Profile Application:**
   ```bash
   # Install profiling tools
   pip install py-spy
   
   # Profile running application
   sudo py-spy top --pid $(pgrep -f "python.*app.py")
   ```

3. **Check Network Latency:**
   ```bash
   # Test API endpoints
   curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com/v1/models
   ```

## 📞 Support

If performance issues persist after applying these optimizations:

1. Run `./diagnose-aws-performance.sh` and share results
2. Check CloudWatch metrics for resource bottlenecks  
3. Consider upgrading instance type or adding load balancing
4. Profile application to identify specific bottlenecks

---

*Last updated: $(date)*
