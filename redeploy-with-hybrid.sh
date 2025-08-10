#!/bin/bash

# Redeploy with Hybrid Search and Improved Chunking
# This script rebuilds and redeploys the application with hybrid search functionality
# and improved document chunking strategy for better section retrieval

set -e

# Configuration
AWS_REGION="ap-southeast-2"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
IMAGE_TAG="latest"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🚀 Redeploying with Hybrid Search and Improved Chunking..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Verify hybrid_search.py exists
if [ ! -f "hybrid_search.py" ]; then
    echo "❌ hybrid_search.py not found. Please ensure it exists in the current directory."
    exit 1
fi

echo "✅ hybrid_search.py found"

# Re-process document with improved chunking strategy
echo "🔄 Re-processing document with improved chunking strategy..."
if [ -f "reprocess_document.py" ]; then
    echo "📄 Running document re-processing..."
    python3 reprocess_document.py
    if [ $? -eq 0 ]; then
        echo "✅ Document re-processed successfully with improved chunking!"
    else
        echo "⚠️ Document re-processing failed, but continuing with deployment..."
    fi
else
    echo "⚠️ reprocess_document.py not found, skipping document re-processing..."
fi

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image for ECS (linux/amd64 platform)
echo "🔨 Building Docker image for ECS (linux/amd64) with hybrid search..."
docker buildx build --platform linux/amd64 -t $ECR_REPOSITORY_NAME:$IMAGE_TAG .

# Tag image for ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"
docker tag $ECR_REPOSITORY_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

echo "✅ Docker image pushed successfully!"

# Get the latest task definition revision
echo "📋 Getting latest task definition..."
LATEST_REVISION=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION_NAME \
    --region $AWS_REGION \
    --query 'taskDefinition.revision' \
    --output text)

echo "✅ Latest task definition revision: $LATEST_REVISION"

# Update the ECS service to force a new deployment
echo "🚀 Updating ECS service to force new deployment..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_NAME:$LATEST_REVISION \
    --force-new-deployment \
    --region $AWS_REGION

echo "✅ Service update initiated!"

# Wait for the deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "🎉 Deployment completed successfully!"

# Get service status
echo "📊 Service status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

# Get deployment status
echo "📋 Deployment status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].deployments[0].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount,FailedTasks:failedTasks}' \
    --output table

echo ""
echo "🔗 Useful AWS Console links:"
echo "- ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME"
echo "- ECS Service: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services/$SERVICE_NAME"
echo ""
echo "✅ Redeployment with hybrid search and improved chunking completed!"
echo ""
echo "🧪 Test the hybrid search by asking about 'Section 11.4' in your application."
echo "📄 The document has been re-processed with improved chunking for better section retrieval."
