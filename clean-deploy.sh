#!/bin/bash

# Clean Deployment Script for Legal Document RAG System
# This script cleans up deployment conflicts and forces a clean deployment

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

echo "🧹 Cleaning up deployment conflicts..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get current service status
echo "📊 Current service status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

# Get deployment status
echo "📋 Current deployments:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].deployments[].{Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount,FailedTasks:failedTasks,TaskDefinition:taskDefinition}' \
    --output table

# Stop the service to clean up deployments
echo "🛑 Stopping service to clean up deployments..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --desired-count 0 \
    --region $AWS_REGION

echo "⏳ Waiting for service to stop..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "✅ Service stopped successfully!"

# Get the latest task definition revision
echo "📋 Getting latest task definition..."
LATEST_REVISION=$(aws ecs describe-task-definition \
    --task-definition $TASK_DEFINITION_NAME \
    --region $AWS_REGION \
    --query 'taskDefinition.revision' \
    --output text)

echo "✅ Latest task definition revision: $LATEST_REVISION"

# Start the service with the latest task definition
echo "🚀 Starting service with latest task definition..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --task-definition $TASK_DEFINITION_NAME:$LATEST_REVISION \
    --desired-count 1 \
    --region $AWS_REGION

echo "✅ Service update initiated!"

# Wait for the deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo "🎉 Clean deployment completed successfully!"

# Get final service status
echo "📊 Final service status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].{ServiceName:serviceName,Status:status,DesiredCount:desiredCount,RunningCount:runningCount,PendingCount:pendingCount}' \
    --output table

# Get final deployment status
echo "📋 Final deployment status:"
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
echo "✅ Clean deployment completed!"
