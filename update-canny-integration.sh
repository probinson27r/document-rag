#!/bin/bash

# Update Canny Integration Script for Legal Document RAG System
# This script updates the task definition to include Canny secrets and redeploys

set -e

# Configuration
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
IMAGE_TAG="latest"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🔧 Setting up Canny integration in AWS deployment..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get ECR URI
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"

echo "📋 ECR Repository: $ECR_URI"

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build new Docker image for linux/amd64 platform
echo "🔨 Building new Docker image for linux/amd64 platform..."
docker buildx build --platform linux/amd64 -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .

# Tag image for ECR
echo "🏷️ Tagging image for ECR..."
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "✅ Docker image pushed successfully!"

# Create new task definition with Canny secrets
echo "📝 Creating new task definition with Canny integration..."
cat > task-definition-canny.json << EOF
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
                },
                {
                    "name": "CANNY_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/canny-api-key"
                },
                {
                    "name": "CANNY_BOARD_ID",
                    "valueFrom": "arn:aws:secretsmanager:ap-southeast-2:$AWS_ACCOUNT_ID:secret:legal-rag/canny-board-id"
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
echo "📋 Registering new task definition with Canny integration..."
NEW_REVISION=$(aws ecs register-task-definition --cli-input-json file://task-definition-canny.json --region $AWS_REGION --query 'taskDefinition.revision' --output text)

echo "✅ New task definition registered: revision $NEW_REVISION"

# Force new deployment by updating service
echo "🔄 Forcing new deployment with Canny integration..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_NAME:$NEW_REVISION \
    --force-new-deployment \
    --region $AWS_REGION

echo "✅ Service updated with Canny integration!"

# Wait for service to stabilize
echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "✅ Service is stable!"

# Get service details
echo "📊 Getting service details..."
SERVICE_DETAILS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION)

# Check if service is running
RUNNING_COUNT=$(echo "$SERVICE_DETAILS" | jq -r '.services[0].runningCount')
DESIRED_COUNT=$(echo "$SERVICE_DETAILS" | jq -r '.services[0].desiredCount')

echo "📈 Service Status:"
echo "- Running tasks: $RUNNING_COUNT"
echo "- Desired tasks: $DESIRED_COUNT"

if [ "$RUNNING_COUNT" -eq "$DESIRED_COUNT" ] && [ "$RUNNING_COUNT" -gt 0 ]; then
    echo "✅ Service is running successfully!"
else
    echo "⚠️ Service may not be fully running. Check AWS Console for details."
fi

# Get service URL
echo "🌍 Getting service URL..."
ALB_DNS=$(aws elbv2 describe-load-balancers --names "legal-rag-alb" --region $AWS_REGION --query 'LoadBalancers[0].DNSName' --output text 2>/dev/null || echo "Load balancer not found")

echo ""
echo "🎉 Canny integration deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "- Task Definition: $TASK_DEFINITION_NAME (revision $NEW_REVISION)"
echo "- ECS Service: $SERVICE_NAME"
echo "- Cluster: $CLUSTER_NAME"
echo "- Image: $ECR_URI:$IMAGE_TAG"
echo "- Platform: linux/amd64"
echo "- Running Tasks: $RUNNING_COUNT/$DESIRED_COUNT"
echo "- Health Check Endpoint: /health (no auth required)"
echo ""
echo "🔧 Canny Integration:"
echo "- CANNY_API_KEY: ✅ Configured from AWS Secrets Manager"
echo "- CANNY_BOARD_ID: ✅ Configured from AWS Secrets Manager"
echo "- Feedback Endpoint: /api/submit_feedback (requires auth)"
echo ""

if [ "$ALB_DNS" != "Load balancer not found" ]; then
    echo "🌍 Application URL: http://$ALB_DNS"
    echo "🏥 Health Check: http://$ALB_DNS/health"
    echo "📊 Status Check: http://$ALB_DNS/api/status (requires auth)"
    echo "💬 Feedback: Available in chat interface (bottom-left corner)"
    echo ""
    echo "💡 Test the health check endpoint to ensure it's working correctly."
    echo "💡 The Canny feedback integration is now active in the chat interface."
else
    echo "⚠️ Load balancer not found. Check your deployment configuration."
fi

echo ""
echo "🔗 Useful AWS Console links:"
echo "- ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "- ECS Service: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services/$SERVICE_NAME"
echo "- ECR Repository: https://console.aws.amazon.com/ecr/repositories/$ECR_REPOSITORY_NAME?region=$AWS_REGION"
echo "- Secrets Manager: https://console.aws.amazon.com/secretsmanager/home?region=$AWS_REGION#/list"
echo ""
echo "💡 Next steps:"
echo "1. Test the health check at http://$ALB_DNS/health"
echo "2. Test the feedback functionality in the chat interface"
echo "3. Check the service logs in CloudWatch"
echo "4. Monitor the service health in AWS Console"
echo ""
echo "⚠️ Important: Make sure to update the Canny secrets with real values:"
echo "   aws secretsmanager update-secret --secret-id legal-rag/canny-api-key --secret-string 'your_real_canny_api_key'"
echo "   aws secretsmanager update-secret --secret-id legal-rag/canny-board-id --secret-string 'your_real_canny_board_id'" 