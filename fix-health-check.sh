#!/bin/bash

# Fix Health Check Script for Legal Document RAG System
# This script fixes the ECS task definition health check to use the correct endpoint

set -e

# Configuration
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"
ECR_REPOSITORY_NAME="legal-document-rag"
IMAGE_TAG="latest"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"

echo "🔧 Fixing ECS task definition health check..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Create new task definition with correct health check
echo "📝 Creating new task definition with corrected health check..."
cat > task-definition-fix.json << EOF
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
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:legal-rag/secret-key"
                },
                {
                    "name": "ANTHROPIC_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:legal-rag/anthropic-api-key"
                },
                {
                    "name": "OPENAI_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:legal-rag/openai-api-key"
                },
                {
                    "name": "PRIVATE_GPT4_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:legal-rag/private-gpt4-api-key"
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
                "command": ["CMD-SHELL", "curl -f http://localhost:5001/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF

# Register new task definition
echo "📋 Registering new task definition..."
NEW_REVISION=$(aws ecs register-task-definition --cli-input-json file://task-definition-fix.json --region $AWS_REGION --query 'taskDefinition.revision' --output text)

echo "✅ New task definition registered: revision $NEW_REVISION"

# Update service to use new task definition
echo "🔄 Updating service to use new task definition..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_NAME:$NEW_REVISION \
    --desired-count 1 \
    --region $AWS_REGION

echo "✅ Service update initiated!"

# Wait for the deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "🎉 Health check fix completed successfully!"

# Get service status
echo "📊 Service status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

# Clean up
rm -f task-definition-fix.json

echo ""
echo "🔗 Useful AWS Console links:"
echo "- ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "- ECS Service: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services/$SERVICE_NAME"
echo ""
echo "✅ Health check fix completed!" 