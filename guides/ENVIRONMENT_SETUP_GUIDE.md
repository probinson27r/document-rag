# Environment Setup Guide

## Overview

This guide explains how to set up environment variables and secrets for the Legal Document RAG System, both for local development and AWS deployment.

## 🔧 **Quick Setup**

### **Automated Setup (Recommended)**
```bash
# Run the interactive setup script
./setup-env.sh
```

This script will:
- Generate or accept a SECRET_KEY
- Prompt for API keys (optional)
- Create AWS Secrets Manager secrets
- Generate local environment files
- Create a deployment script with your settings

### **Manual Setup**

#### **1. Generate a SECRET_KEY**
```bash
# Generate a random 32-byte hex string
openssl rand -hex 32
```

#### **2. Set Environment Variables**

**For Local Development:**
```bash
# Create .env file
cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=your-generated-secret-key-here
ANTHROPIC_API_KEY=your-claude-api-key
OPENAI_API_KEY=your-openai-api-key
PRIVATE_GPT4_API_KEY=your-private-gpt4-api-key
EOF
```

**For AWS Deployment:**
```bash
# Set environment variable for deployment
export SECRET_KEY="your-generated-secret-key-here"
./deploy-aws.sh
```

## 🔐 **AWS Secrets Manager Setup**

### **Create Secrets Manually**
```bash
# Set your AWS region
export AWS_REGION="ap-southeast-2"

# Create secrets
aws secretsmanager create-secret \
    --name "legal-rag/secret-key" \
    --secret-string "your-generated-secret-key-here" \
    --region $AWS_REGION

aws secretsmanager create-secret \
    --name "legal-rag/anthropic-api-key" \
    --secret-string "your-claude-api-key" \
    --region $AWS_REGION

aws secretsmanager create-secret \
    --name "legal-rag/openai-api-key" \
    --secret-string "your-openai-api-key" \
    --region $AWS_REGION

aws secretsmanager create-secret \
    --name "legal-rag/private-gpt4-api-key" \
    --secret-string "your-private-gpt4-api-key" \
    --region $AWS_REGION
```

### **Update Existing Secrets**
```bash
aws secretsmanager update-secret \
    --secret-id "legal-rag/secret-key" \
    --secret-string "new-secret-key-value" \
    --region $AWS_REGION
```

## 🌍 **Environment Variables Reference**

### **Required Variables**

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment mode | `development` or `production` |
| `SECRET_KEY` | Flask secret key for sessions | `a1b2c3d4e5f6...` (32+ characters) |

### **Optional Variables**

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `PRIVATE_GPT4_API_KEY` | Private GPT-4 API key | `your-private-key` |

## 🚀 **Deployment Methods**

### **Method 1: Using setup-env.sh (Recommended)**
```bash
# 1. Run setup
./setup-env.sh

# 2. Deploy with configured environment
./deploy-with-env.sh
```

### **Method 2: Manual Environment Variables**
```bash
# Set environment variables
export SECRET_KEY="your-secret-key"
export AWS_REGION="ap-southeast-2"

# Deploy
./deploy-aws.sh
```

### **Method 3: AWS Secrets Manager Only**
```bash
# Create secrets first (see above)
# Then deploy (secrets are automatically loaded)
./deploy-aws.sh
```

## 🔍 **Verification**

### **Check Local Environment**
```bash
# Test local environment
source .env
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "FLASK_ENV: $FLASK_ENV"
```

### **Check AWS Secrets**
```bash
# List secrets
aws secretsmanager list-secrets --region ap-southeast-2

# Get secret value (be careful - this shows the value)
aws secretsmanager get-secret-value \
    --secret-id "legal-rag/secret-key" \
    --region ap-southeast-2 \
    --query 'SecretString' \
    --output text
```

### **Check Application**
```bash
# Test local application
python app.py

# Check AWS deployment
./check-aws-resources.sh
```

## 🛡️ **Security Best Practices**

### **SECRET_KEY Requirements**
- **Length**: At least 32 characters
- **Complexity**: Mix of letters, numbers, and symbols
- **Randomness**: Use cryptographically secure random generation
- **Uniqueness**: Never reuse across applications

### **API Key Security**
- **Never commit** API keys to version control
- **Use AWS Secrets Manager** for production
- **Rotate keys** regularly
- **Limit permissions** to minimum required

### **Environment Separation**
- **Development**: Use `.env` files locally
- **Production**: Use AWS Secrets Manager
- **Testing**: Use separate test keys

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. SECRET_KEY not set**
```bash
# Error: RuntimeError: The session is unavailable because no secret key was set
# Solution: Set SECRET_KEY environment variable
export SECRET_KEY="your-secret-key"
```

#### **2. AWS Secrets not found**
```bash
# Error: SecretsManagerException: Secrets Manager can't find the specified secret
# Solution: Create the secret first
aws secretsmanager create-secret \
    --name "legal-rag/secret-key" \
    --secret-string "your-secret-key" \
    --region ap-southeast-2
```

#### **3. Permission denied**
```bash
# Error: AccessDeniedException
# Solution: Check IAM permissions for Secrets Manager
aws iam list-attached-user-policies --user-name your-username
```

#### **4. Region mismatch**
```bash
# Error: Resource not found in region
# Solution: Ensure all resources are in the same region
export AWS_REGION="ap-southeast-2"
```

### **Debug Commands**
```bash
# Check environment variables
env | grep -E "(FLASK|SECRET|API)"

# Check AWS configuration
aws configure list

# Check secrets existence
aws secretsmanager list-secrets --region ap-southeast-2

# Test secret access
aws secretsmanager describe-secret \
    --secret-id "legal-rag/secret-key" \
    --region ap-southeast-2
```

## 📋 **Checklist**

### **Before Deployment**
- [ ] SECRET_KEY is set and secure
- [ ] FLASK_ENV is set to `production`
- [ ] API keys are configured (if needed)
- [ ] AWS Secrets Manager secrets are created
- [ ] AWS CLI is configured
- [ ] Region is set correctly

### **After Deployment**
- [ ] Application is accessible
- [ ] Health checks are passing
- [ ] Logs are being generated
- [ ] Secrets are being loaded correctly
- [ ] No sensitive data in logs

## 🔄 **Updating Secrets**

### **Update SECRET_KEY**
```bash
# Generate new key
NEW_SECRET_KEY=$(openssl rand -hex 32)

# Update AWS secret
aws secretsmanager update-secret \
    --secret-id "legal-rag/secret-key" \
    --secret-string "$NEW_SECRET_KEY" \
    --region ap-southeast-2

# Redeploy application
./deploy-aws.sh
```

### **Update API Keys**
```bash
# Update specific API key
aws secretsmanager update-secret \
    --secret-id "legal-rag/anthropic-api-key" \
    --secret-string "new-api-key" \
    --region ap-southeast-2

# Redeploy application
./deploy-aws.sh
```

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section
2. Verify AWS permissions
3. Check application logs
4. Ensure all environment variables are set correctly 