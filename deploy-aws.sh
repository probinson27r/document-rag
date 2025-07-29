#!/bin/bash

# AWS Docker Deployment Script for Legal Document RAG System
# This script builds and deploys the application to AWS ECR/ECS

set -e

# Configuration
AWS_REGION="ap-southeast-2"  # Change to your preferred region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
IMAGE_TAG="latest"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🚀 Starting AWS deployment for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || echo "Repository already exists"

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .

# Tag image for ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "✅ Docker image pushed successfully!"
echo "📋 ECR Image URI: $ECR_URI:$IMAGE_TAG"

# Create ECS cluster if it doesn't exist
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION 2>/dev/null || echo "Cluster already exists"

# Create task definition
echo "📝 Creating ECS task definition..."
cat > task-definition.json << EOF
{
    "family": "$TASK_DEFINITION_NAME",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "1024",
    "memory": "2048",
    "executionRoleArn": "ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "legal-rag-app",
            "image": "$ECR_URI:$IMAGE_TAG",
            "portMappings": [
                {
                    "containerPort": 5001,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "FLASK_ENV",
                    "value": "production"
                }
            ],
            "secrets": [
                {
                    "name": "SECRET_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/secret-key"
                },
                {
                    "name": "ANTHROPIC_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/anthropic-api-key"
                },
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/openai-api-key"
                },
                {
                    "name": "PRIVATE_GPT4_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/private-gpt4-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/$TASK_DEFINITION_NAME",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:5001/api/status || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

# Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/$TASK_DEFINITION_NAME" --region $AWS_REGION 2>/dev/null || echo "Log group already exists"

echo "✅ Task definition created successfully!"

# Create Application Load Balancer (if needed)
echo "🌐 Setting up load balancer..."
# Note: This is a simplified version. In production, you'd want to create a proper ALB setup

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Create an Application Load Balancer in AWS Console"
echo "2. Create an ECS service using the task definition: $TASK_DEFINITION_NAME"
echo "3. Configure environment variables and secrets in AWS Secrets Manager"
echo "4. Set up proper security groups and VPC configuration"
echo ""
echo "🔗 Useful AWS Console links:"
echo "- ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "- ECR Repository: https://console.aws.amazon.com/ecr/repositories/$ECR_REPOSITORY_NAME?region=$AWS_REGION"
echo "- Task Definition: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/taskDefinitions/$TASK_DEFINITION_NAME"
echo ""
echo "💡 For a complete production setup, consider using AWS CDK or Terraform for infrastructure as code." 