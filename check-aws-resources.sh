#!/bin/bash

# AWS Resource Check Script for Legal Document RAG System
# This script checks what AWS resources exist before destruction

set -e

# Configuration (must match deploy-aws.sh)
AWS_REGION="ap-southeast-2"  # Change to your preferred region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY_NAME="legal-document-rag"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"

echo "🔍 Checking AWS resources for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"
echo "🌍 AWS Region: $AWS_REGION"
echo ""

# Function to check resource existence
check_resource() {
    local resource_type=$1
    local resource_name=$2
    local check_command=$3
    
    echo "🔍 Checking $resource_type: $resource_name"
    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ $resource_type '$resource_name' EXISTS"
        return 0
    else
        echo "❌ $resource_type '$resource_name' NOT FOUND"
        return 1
    fi
}

# Check ECS cluster
echo "=== ECS Resources ==="
check_resource "ECS cluster" "$CLUSTER_NAME" \
    "aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION"

# Check ECS service
check_resource "ECS service" "$SERVICE_NAME" \
    "aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"

# Check task definitions
echo "🔍 Checking ECS task definitions..."
TASK_REVISIONS=$(aws ecs list-task-definitions --family-prefix $TASK_DEFINITION_NAME --region $AWS_REGION --query 'taskDefinitionArns' --output text 2>/dev/null || echo "")

if [ -n "$TASK_REVISIONS" ]; then
    echo "✅ Found task definitions:"
    for task_def in $TASK_REVISIONS; do
        echo "   - $task_def"
    done
else
    echo "❌ No task definitions found"
fi

# Check running tasks
echo "🔍 Checking running ECS tasks..."
RUNNING_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region $AWS_REGION --query 'taskArns' --output text 2>/dev/null || echo "")

if [ -n "$RUNNING_TASKS" ]; then
    echo "✅ Found running tasks:"
    for task in $RUNNING_TASKS; do
        echo "   - $task"
    done
else
    echo "❌ No running tasks found"
fi

echo ""

# Check ECR repository
echo "=== ECR Resources ==="
check_resource "ECR repository" "$ECR_REPOSITORY_NAME" \
    "aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION"

# Check ECR images
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "🔍 Checking ECR images..."
    IMAGES=$(aws ecr list-images --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION --query 'imageIds[*].imageTag' --output text 2>/dev/null || echo "")
    
    if [ -n "$IMAGES" ]; then
        echo "✅ Found ECR images:"
        for image in $IMAGES; do
            echo "   - $image"
        done
    else
        echo "❌ No ECR images found"
    fi
else
    echo "ℹ️ ECR repository not found, skipping image check"
fi

echo ""

# Check CloudWatch log groups
echo "=== CloudWatch Resources ==="
LOG_GROUPS=(
    "/ecs/$TASK_DEFINITION_NAME"
    "/aws/ecs/$TASK_DEFINITION_NAME"
)

for log_group in "${LOG_GROUPS[@]}"; do
    check_resource "CloudWatch log group" "$log_group" \
        "aws logs describe-log-groups --log-group-name-prefix $log_group --region $AWS_REGION"
done

echo ""

# Check AWS Secrets Manager secrets
echo "=== Secrets Manager Resources ==="
SECRETS=(
    "legal-rag/secret-key"
    "legal-rag/anthropic-api-key"
    "legal-rag/openai-api-key"
    "legal-rag/private-gpt4-api-key"
)

for secret in "${SECRETS[@]}"; do
    check_resource "Secret" "$secret" \
        "aws secretsmanager describe-secret --secret-id $secret --region $AWS_REGION"
done

# Check Application Load Balancer resources
echo "=== Load Balancer Resources ==="

# Check ALB
ALB_NAME="legal-rag-alb"
check_resource "Application Load Balancer" "$ALB_NAME" \
    "aws elbv2 describe-load-balancers --names $ALB_NAME --region $AWS_REGION"

# Check target group
TG_NAME="legal-rag-tg"
check_resource "Target Group" "$TG_NAME" \
    "aws elbv2 describe-target-groups --names $TG_NAME --region $AWS_REGION"

# Check ALB listeners
ALB_ARN=$(aws elbv2 describe-load-balancers --names $ALB_NAME --region $AWS_REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "None")
if [ "$ALB_ARN" != "None" ] && [ -n "$ALB_ARN" ]; then
    check_resource "ALB Listeners" "Listeners for $ALB_NAME" \
        "aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region $AWS_REGION"
fi

# Check security groups
echo "=== Security Group Resources ==="
SECURITY_GROUPS=(
    "legal-rag-alb-sg"
    "legal-rag-ecs-sg"
)

for sg_name in "${SECURITY_GROUPS[@]}"; do
    check_resource "Security Group" "$sg_name" \
        "aws ec2 describe-security-groups --filters \"Name=group-name,Values=$sg_name\" --region $AWS_REGION"
done

echo ""

# Check local files
echo "=== Local Files ==="
if [ -f "task-definition.json" ]; then
    echo "✅ task-definition.json exists locally"
else
    echo "❌ task-definition.json not found locally"
fi

echo ""

# Summary
echo "📊 Resource Summary:"
echo "=================="

# Count existing resources
ECS_CLUSTER_EXISTS=$(aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION > /dev/null 2>&1 && echo "1" || echo "0")
ECS_SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION > /dev/null 2>&1 && echo "1" || echo "0")
ECR_REPO_EXISTS=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1 && echo "1" || echo "0")
TASK_DEF_COUNT=$(aws ecs list-task-definitions --family-prefix $TASK_DEFINITION_NAME --region $AWS_REGION --query 'length(taskDefinitionArns)' --output text 2>/dev/null || echo "0")
RUNNING_TASK_COUNT=$(aws ecs list-tasks --cluster $CLUSTER_NAME --region $AWS_REGION --query 'length(taskArns)' --output text 2>/dev/null || echo "0")

echo "ECS Clusters: $ECS_CLUSTER_EXISTS"
echo "ECS Services: $ECS_SERVICE_EXISTS"
echo "ECR Repositories: $ECR_REPO_EXISTS"
echo "Task Definitions: $TASK_DEF_COUNT"
echo "Running Tasks: $RUNNING_TASK_COUNT"

echo ""
echo "💡 To destroy all resources, run: ./destroy-aws.sh"
echo "⚠️ This will permanently delete all resources and data!" 