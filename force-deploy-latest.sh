#!/bin/bash

# Force Latest Task Deployment Script for Legal Document RAG System
# This script forces ECS to deploy the latest task definition

set -e

# Configuration
AWS_REGION="ap-southeast-2"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🔄 Force deploying latest task to AWS ECS..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

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
echo "✅ Force deployment completed!" 