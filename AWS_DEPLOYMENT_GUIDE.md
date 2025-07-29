# AWS Docker Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Legal Document RAG System to AWS using Docker containers. The deployment uses AWS ECR (Elastic Container Registry) and ECS (Elastic Container Service) for simplicity.

## Prerequisites

### Required Tools
- [Docker](https://docs.docker.com/get-docker/) installed and running
- [AWS CLI](https://aws.amazon.com/cli/) installed and configured
- AWS account with appropriate permissions

### AWS Permissions
Your AWS user/role needs the following permissions:
- ECR: Full access
- ECS: Full access
- IAM: Create roles and policies
- CloudWatch Logs: Create log groups
- Secrets Manager: Create and manage secrets (optional)

## Quick Start

### 1. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and preferred region
```

### 2. Run the Deployment Script
```bash
./deploy-aws.sh
```

This script will:
- Build the Docker image
- Push it to ECR
- Create ECS cluster and task definition
- Set up CloudWatch logging

## Manual Deployment Steps

### Step 1: Build and Push Docker Image

```bash
# Build the image
docker build -t legal-document-rag:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag legal-document-rag:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/legal-document-rag:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/legal-document-rag:latest
```

### Step 2: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name legal-rag-cluster --region us-east-1
```

### Step 3: Create Task Definition

The deployment script creates a task definition automatically. You can also create it manually:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 4: Create ECS Service

```bash
aws ecs create-service \
  --cluster legal-rag-cluster \
  --service-name legal-rag-service \
  --task-definition legal-rag-task:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

## Environment Configuration

### Environment Variables

The application uses the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `FLASK_ENV` | Flask environment (production/development) | Yes |
| `SECRET_KEY` | Flask secret key for sessions | Yes |
| `ANTHROPIC_API_KEY` | Claude API key | No |
| `OPENAI_API_KEY` | OpenAI API key | No |
| `PRIVATE_GPT4_API_KEY` | Private GPT-4 API key | No |

### AWS Secrets Manager (Recommended)

For production, store API keys in AWS Secrets Manager:

```bash
# Create secrets
aws secretsmanager create-secret \
  --name legal-rag/anthropic-api-key \
  --secret-string "your-claude-api-key"

aws secretsmanager create-secret \
  --name legal-rag/openai-api-key \
  --secret-string "your-openai-api-key"

aws secretsmanager create-secret \
  --name legal-rag/private-gpt4-api-key \
  --secret-string "your-private-gpt4-api-key"
```

## Local Testing

### Using Docker Compose

```bash
# Build and run locally
docker-compose up --build

# Access the application
open http://localhost:5001
```

### Using Docker

```bash
# Build image
docker build -t legal-document-rag .

# Run container
docker run -p 5001:5001 \
  -e FLASK_ENV=development \
  -e SECRET_KEY=dev-secret-key \
  legal-document-rag
```

## Monitoring and Logs

### CloudWatch Logs
Logs are automatically sent to CloudWatch:
- Log Group: `/ecs/legal-rag-task`
- Stream Prefix: `ecs`

### Health Checks
The application includes health checks:
- Endpoint: `GET /api/status`
- Interval: 30 seconds
- Timeout: 5 seconds
- Retries: 3

## Scaling

### Manual Scaling
```bash
# Scale the service
aws ecs update-service \
  --cluster legal-rag-cluster \
  --service legal-rag-service \
  --desired-count 2
```

### Auto Scaling
For production, consider setting up auto scaling based on CPU/memory usage.

## Security Considerations

### Network Security
- Use private subnets for ECS tasks
- Configure security groups to allow only necessary traffic
- Use Application Load Balancer for public access

### Data Security
- Store API keys in AWS Secrets Manager
- Use HTTPS for all external communication
- Implement proper IAM roles and policies

### Container Security
- Run containers as non-root user
- Regularly update base images
- Scan images for vulnerabilities

## Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   # Check ECS task logs
   aws logs describe-log-streams --log-group-name "/ecs/legal-rag-task"
   aws logs get-log-events --log-group-name "/ecs/legal-rag-task" --log-stream-name "stream-name"
   ```

2. **Image pull fails**
   ```bash
   # Verify ECR repository exists
   aws ecr describe-repositories --repository-names legal-document-rag
   ```

3. **Health check fails**
   ```bash
   # Check if application is responding
   curl http://localhost:5001/api/status
   ```

### Debug Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster legal-rag-cluster --services legal-rag-service

# Check task definition
aws ecs describe-task-definition --task-definition legal-rag-task

# List running tasks
aws ecs list-tasks --cluster legal-rag-cluster
```

## Cost Optimization

### Resource Allocation
- Start with minimal resources (1 vCPU, 2GB RAM)
- Monitor usage and adjust as needed
- Use Spot instances for non-critical workloads

### Storage
- Use EFS for persistent storage if needed
- Consider S3 for document storage
- Clean up unused ECR images

## Production Considerations

### High Availability
- Deploy across multiple Availability Zones
- Use Application Load Balancer
- Implement proper monitoring and alerting

### Backup and Recovery
- Backup ChromaDB data regularly
- Document recovery procedures
- Test disaster recovery scenarios

### Performance
- Monitor application performance
- Optimize container resources
- Consider caching strategies

## Cleanup

To remove all resources:

```bash
# Check what resources exist first
./check-aws-resources.sh

# Destroy all resources
./destroy-aws.sh
```

### Manual Cleanup Commands

If you prefer to clean up manually:

```bash
# Delete ECS service
aws ecs update-service --cluster legal-rag-cluster --service legal-rag-service --desired-count 0
aws ecs delete-service --cluster legal-rag-cluster --service legal-rag-service

# Delete ECS cluster
aws ecs delete-cluster --cluster legal-rag-cluster

# Delete ECR repository
aws ecr delete-repository --repository-name legal-document-rag --force

# Delete CloudWatch log group
aws logs delete-log-group --log-group-name "/ecs/legal-rag-task"

# Delete secrets (if created)
aws secretsmanager delete-secret --secret-id legal-rag/anthropic-api-key
aws secretsmanager delete-secret --secret-id legal-rag/openai-api-key
aws secretsmanager delete-secret --secret-id legal-rag/private-gpt4-api-key
```

## Resource Management Scripts

### Check Resources
```bash
./check-aws-resources.sh
```
This script shows you what AWS resources currently exist for the Legal Document RAG system.

### Destroy Resources
```bash
./destroy-aws.sh
```
This script safely removes all AWS resources created by the deployment, including:
- ECS service and cluster
- Task definitions
- ECR repository and images
- CloudWatch log groups
- AWS Secrets Manager secrets
- Local deployment files

### Safety Features
- **Graceful shutdown**: Scales down services before deletion
- **Resource verification**: Checks if resources exist before attempting deletion
- **Error handling**: Continues even if some resources don't exist
- **Verification**: Confirms cleanup was successful

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Verify AWS service status
4. Check application logs in the container 