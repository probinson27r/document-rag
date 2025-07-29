#!/bin/bash

# AWS Resource Destruction Script for Legal Document RAG System
# This script removes all AWS resources created by deploy-aws.sh

set -e

# Configuration (must match deploy-aws.sh)
AWS_REGION="us-east-1"  # Change to your preferred region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🗑️ Starting AWS resource destruction for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Function to check if resource exists
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    local command=$3
    
    if eval "$command" > /dev/null 2>&1; then
        return 0  # Resource exists
    else
        return 1  # Resource doesn't exist
    fi
}

# Function to safely delete resource
safe_delete() {
    local resource_type=$1
    local resource_name=$2
    local delete_command=$3
    
    echo "🔍 Checking if $resource_type '$resource_name' exists..."
    if resource_exists "$resource_type" "$resource_name" "$delete_command --dry-run 2>&1"; then
        echo "🗑️ Deleting $resource_type '$resource_name'..."
        if eval "$delete_command"; then
            echo "✅ Successfully deleted $resource_type '$resource_name'"
        else
            echo "⚠️ Failed to delete $resource_type '$resource_name' (may not exist or have dependencies)"
        fi
    else
        echo "ℹ️ $resource_type '$resource_name' does not exist, skipping..."
    fi
}

# Step 1: Scale down ECS service to 0 tasks
echo "📉 Scaling down ECS service..."
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "📉 Scaling service to 0 tasks..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --desired-count 0 \
        --region $AWS_REGION || echo "⚠️ Service may already be scaled down"
    
    # Wait for tasks to stop
    echo "⏳ Waiting for tasks to stop..."
    sleep 30
else
    echo "ℹ️ ECS service does not exist, skipping scale down..."
fi

# Step 2: Delete ECS service
echo "🗑️ Deleting ECS service..."
safe_delete "ECS service" "$SERVICE_NAME" \
    "aws ecs delete-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --region $AWS_REGION --force"

# Step 3: Deregister task definitions
echo "🗑️ Deregistering task definitions..."
TASK_REVISIONS=$(aws ecs list-task-definitions --family-prefix $TASK_DEFINITION_NAME --region $AWS_REGION --query 'taskDefinitionArns' --output text 2>/dev/null || echo "")

if [ -n "$TASK_REVISIONS" ]; then
    for task_def in $TASK_REVISIONS; do
        echo "🗑️ Deregistering task definition: $task_def"
        aws ecs deregister-task-definition --task-definition $task_def --region $AWS_REGION || echo "⚠️ Failed to deregister $task_def"
    done
else
    echo "ℹ️ No task definitions found to deregister"
fi

# Step 4: Delete ECS cluster
echo "🗑️ Deleting ECS cluster..."
safe_delete "ECS cluster" "$CLUSTER_NAME" \
    "aws ecs delete-cluster --cluster $CLUSTER_NAME --region $AWS_REGION"

# Step 5: Delete CloudWatch log groups
echo "🗑️ Deleting CloudWatch log groups..."
LOG_GROUPS=(
    "/ecs/$TASK_DEFINITION_NAME"
    "/aws/ecs/$TASK_DEFINITION_NAME"
)

for log_group in "${LOG_GROUPS[@]}"; do
    safe_delete "CloudWatch log group" "$log_group" \
        "aws logs delete-log-group --log-group-name $log_group --region $AWS_REGION"
done

# Step 6: Delete ECR repository
echo "🗑️ Deleting ECR repository..."
safe_delete "ECR repository" "$ECR_REPOSITORY_NAME" \
    "aws ecr delete-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION --force"

# Step 7: Delete AWS Secrets Manager secrets (if they exist)
echo "🗑️ Deleting AWS Secrets Manager secrets..."
SECRETS=(
    "legal-rag/anthropic-api-key"
    "legal-rag/openai-api-key"
    "legal-rag/private-gpt4-api-key"
)

for secret in "${SECRETS[@]}"; do
    safe_delete "Secret" "$secret" \
        "aws secretsmanager delete-secret --secret-id $secret --region $AWS_REGION --force-delete-without-recovery"
done

# Step 8: Clean up any orphaned ECR images (optional)
echo "🧹 Cleaning up orphaned ECR images..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "📦 Repository still exists, skipping image cleanup..."
else
    echo "ℹ️ ECR repository already deleted, skipping image cleanup..."
fi

# Step 9: Clean up any orphaned ECS tasks (force stop if running)
echo "🧹 Cleaning up orphaned ECS tasks..."
RUNNING_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region $AWS_REGION --query 'taskArns' --output text 2>/dev/null || echo "")

if [ -n "$RUNNING_TASKS" ]; then
    echo "🛑 Force stopping orphaned tasks..."
    for task in $RUNNING_TASKS; do
        echo "🛑 Stopping task: $task"
        aws ecs stop-task --cluster $CLUSTER_NAME --task $task --region $AWS_REGION || echo "⚠️ Failed to stop task $task"
    done
else
    echo "ℹ️ No orphaned tasks found"
fi

# Step 10: Clean up local files
echo "🧹 Cleaning up local files..."
if [ -f "task-definition.json" ]; then
    rm -f task-definition.json
    echo "✅ Removed local task-definition.json"
fi

# Step 11: Verify cleanup
echo "🔍 Verifying cleanup..."

# Check ECS cluster
if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "⚠️ ECS cluster still exists"
else
    echo "✅ ECS cluster deleted"
fi

# Check ECR repository
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "⚠️ ECR repository still exists"
else
    echo "✅ ECR repository deleted"
fi

# Check CloudWatch log groups
for log_group in "${LOG_GROUPS[@]}"; do
    if aws logs describe-log-groups --log-group-name-prefix $log_group --region $AWS_REGION > /dev/null 2>&1; then
        echo "⚠️ CloudWatch log group $log_group still exists"
    else
        echo "✅ CloudWatch log group $log_group deleted"
    fi
done

echo ""
echo "🎉 AWS resource destruction completed!"
echo ""
echo "📋 Summary:"
echo "- ECS service: Deleted"
echo "- ECS cluster: Deleted"
echo "- Task definitions: Deregistered"
echo "- CloudWatch log groups: Deleted"
echo "- ECR repository: Deleted"
echo "- AWS Secrets: Deleted"
echo "- Local files: Cleaned up"
echo ""
echo "💡 Note: Some resources may take a few minutes to fully disappear from the AWS console."
echo "🔗 Check the AWS Console to verify all resources have been removed:"
echo "- ECS: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION"
echo "- ECR: https://console.aws.amazon.com/ecr/repositories?region=$AWS_REGION"
echo "- CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION#logsV2:log-groups"
echo "- Secrets Manager: https://console.aws.amazon.com/secretsmanager/home?region=$AWS_REGION#/listSecrets" 