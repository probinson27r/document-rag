# Quick Fixes for AWS Secrets Access

## Issue: "AWS credentials not found" Error

Your EC2 instance cannot access AWS Secrets Manager because it lacks AWS credentials/IAM permissions.

## 🚀 Quick Fix (5 minutes)

### SSH to EC2 and run:
```bash
# Download and run the quick fix script
wget https://raw.githubusercontent.com/your-repo/document_rag/main/quick-fix-private-gpt4.sh
chmod +x quick-fix-private-gpt4.sh
./quick-fix-private-gpt4.sh
```

### Manual Alternative:
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Edit environment file
sudo nano /opt/legal-rag-app/.env

# Add this line with your actual key:
PRIVATE_GPT4_API_KEY=your-actual-private-gpt4-api-key

# Save and restart service
sudo systemctl restart legal-rag

# Check status
sudo systemctl status legal-rag
sudo journalctl -u legal-rag -f
```

## 🔐 Proper Solution (15 minutes)

### 1. Set up IAM Role (run locally):
```bash
./setup-ec2-iam-secrets.sh
```

### 2. Attach IAM Role to EC2:
- Go to AWS Console → EC2 → Instances
- Select your instance → Actions → Security → Modify IAM role
- Choose: `LegalRAG-EC2-SecretsManager-Profile`

### 3. Create AWS Secrets:
```bash
./setup-aws-secrets.sh
```

### 4. Restart Application:
```bash
# SSH to EC2
sudo systemctl restart legal-rag
```

## 🔍 Troubleshooting

### Check if fix worked:
```bash
# Test health endpoint
curl http://localhost:5001/health

# Check logs
sudo journalctl -u legal-rag -f

# Run diagnostics
./diagnose-secrets-access.sh
```

### Expected Log Messages:
✅ Good: `"Private GPT-4 client initialized"`  
❌ Bad: `"No Private GPT-4 API key found"`

## 🎯 Recommendation

**Use Quick Fix first** to get your app working immediately, then **implement the IAM role solution** for production security.

The environment variable approach is perfectly valid and secure when the .env file has proper permissions (600, ubuntu:ubuntu).
