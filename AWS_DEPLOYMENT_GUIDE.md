# AWS Docker Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Legal Document RAG System to AWS using Docker containers. The deployment uses AWS ECR (Elastic Container Registry) and ECS (Elastic Container Service) for simplicity.

## 🚀 **Quick Start**

### **Prerequisites**
- AWS CLI installed and configured
- Docker installed
- Python 3.8+ installed
- AWS account with appropriate permissions

### **Step 1: Set Up Environment**
```bash
# Run the interactive setup script
./setup-env.sh
```

### **Step 2: Deploy to AWS**
```bash
# Deploy with configured environment
./deploy-with-env.sh
```

### **Step 3: Access Your Application**
After deployment, you'll get a URL like:
```
http://legal-rag-alb-123456789.ap-southeast-2.elb.amazonaws.com
```

## 🔧 **Manual Deployment Steps**

If you prefer to deploy manually or need to customize the deployment:

### **1. Build and Push Docker Image**
```bash
# Build the Docker image
docker build -t legal-document-rag .

# Tag for ECR
docker tag legal-document-rag:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/legal-document-rag:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/legal-document-rag:latest
```

### **2. Create AWS Secrets**
```bash
# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "legal-rag/secret-key" \
    --secret-string "your-secret-key" \
    --region ap-southeast-2

aws secretsmanager create-secret \
    --name "legal-rag/anthropic-api-key" \
    --secret-string "your-claude-api-key" \
    --region ap-southeast-2

aws secretsmanager create-secret \
    --name "legal-rag/openai-api-key" \
    --secret-string "your-openai-api-key" \
    --region ap-southeast-2

aws secretsmanager create-secret \
    --name "legal-rag/private-gpt4-api-key" \
    --secret-string "your-private-gpt4-api-key" \
    --region ap-southeast-2
```

### **3. Deploy Infrastructure**
```bash
# Run the deployment script
./deploy-aws.sh
```

## 🌐 **Application Load Balancer (ALB)**

The deployment automatically creates a complete ALB setup:

### **ALB Components Created**
- **Application Load Balancer**: `legal-rag-alb`
- **Target Group**: `legal-rag-tg` (port 5001)
- **Listener**: HTTP on port 80
- **Security Groups**: 
  - `legal-rag-alb-sg` (ALB security group)
  - `legal-rag-ecs-sg` (ECS tasks security group)

### **ALB Configuration**
- **Protocol**: HTTP (port 80)
- **Health Check**: `/api/status` endpoint
- **Health Check Interval**: 30 seconds
- **Health Check Timeout**: 5 seconds
- **Healthy Threshold**: 2 consecutive checks
- **Unhealthy Threshold**: 2 consecutive checks

### **Security Groups**
- **ALB Security Group**: Allows HTTP (80) and HTTPS (443) from anywhere
- **ECS Security Group**: Allows traffic on port 5001 only from ALB

### **Accessing Your Application**
After deployment, you can access your application at:
```
http://[ALB-DNS-NAME]
```

Example:
```
http://legal-rag-alb-123456789.ap-southeast-2.elb.amazonaws.com
```

### **Health Check Endpoint**
The ALB health check uses:
```
http://[ALB-DNS-NAME]/api/status
```

## 🔍 **Monitoring and Verification**

### **Check Deployment Status**
```bash
# Check all AWS resources
./check-aws-resources.sh
```

### **View Application Logs**
```bash
# Get ECS service logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/legal-rag-task" --region ap-southeast-2

# Get recent log events
aws logs filter-log-events \
    --log-group-name "/ecs/legal-rag-task" \
    --start-time $(date -d '1 hour ago' +%s)000 \
    --region ap-southeast-2
```

### **Test Application Health**
```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --names legal-rag-alb --region ap-southeast-2 --query 'LoadBalancers[0].DNSName' --output text)

# Test health endpoint
curl -f http://$ALB_DNS/api/status

# Test main application
curl -f http://$ALB_DNS/
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. ALB Health Check Failing**
```bash
# Check ECS service status
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service --region ap-southeast-2

# Check target group health
aws elbv2 describe-target-health --target-group-arn [TARGET-GROUP-ARN] --region ap-southeast-2
```

#### **2. ECS Tasks Not Starting**
```bash
# Check task definition
aws ecs describe-task-definition --task-definition legal-rag-task --region ap-southeast-2

# Check ECS events
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service --region ap-southeast-2 --query 'services[0].events'
```

#### **3. Security Group Issues**
```bash
# Check security group rules
aws ec2 describe-security-groups --filters "Name=group-name,Values=legal-rag-*" --region ap-southeast-2
```

#### **4. Secrets Not Loading**
```bash
# Check if secrets exist
aws secretsmanager list-secrets --region ap-southeast-2 --query 'SecretList[?contains(Name, `legal-rag`)]'

# Test secret access
aws secretsmanager get-secret-value --secret-id legal-rag/secret-key --region ap-southeast-2
```

### **Debug Commands**
```bash
# Check all resources in one command
./check-aws-resources.sh

# Get detailed ECS service information
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service --region ap-southeast-2

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names legal-rag-tg --region ap-southeast-2 --query 'TargetGroups[0].TargetGroupArn' --output text) --region ap-southeast-2
```

## 🗑️ **Cleanup**

### **Destroy All Resources**
```bash
# Remove all AWS resources
./destroy-aws.sh
```

This will remove:
- ECS cluster and service
- Application Load Balancer and target group
- Security groups
- ECR repository and images
- CloudWatch log groups
- AWS Secrets Manager secrets

### **Verify Cleanup**
```bash
# Check that all resources are removed
./check-aws-resources.sh
```

## 🔒 **Security Considerations**

### **Production Security**
- **HTTPS**: Add SSL certificate for HTTPS
- **WAF**: Consider AWS WAF for additional protection
- **VPC**: Use private subnets for ECS tasks
- **IAM**: Use least privilege IAM roles
- **Secrets**: Rotate secrets regularly

### **Network Security**
- **ALB Security Group**: Only allows HTTP/HTTPS
- **ECS Security Group**: Only allows traffic from ALB
- **No Direct Access**: ECS tasks are not directly accessible

### **Application Security**
- **SECRET_KEY**: Stored securely in AWS Secrets Manager
- **API Keys**: Stored securely in AWS Secrets Manager
- **Health Checks**: Regular health monitoring
- **Logging**: Centralized logging in CloudWatch 