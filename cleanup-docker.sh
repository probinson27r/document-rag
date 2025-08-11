#!/bin/bash

# Cleanup Docker Resources Script
# This script removes Docker-related AWS resources after migration to EC2

set -e

# Configuration
AWS_REGION="ap-southeast-2"
CLUSTER_NAME="legal-rag-cluster"
SERVICE_NAME="legal-rag-service"
TASK_DEFINITION_NAME="legal-rag-task"
ECR_REPOSITORY_NAME="legal-document-rag"

echo "🧹 Starting Docker resources cleanup..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Function to check if resource exists
resource_exists() {
    local resource_type=$1
    local resource_name=$2
    
    case $resource_type in
        "cluster")
            aws ecs describe-clusters --clusters $resource_name --region $AWS_REGION > /dev/null 2>&1
            ;;
        "service")
            aws ecs describe-services --cluster $CLUSTER_NAME --services $resource_name --region $AWS_REGION > /dev/null 2>&1
            ;;
        "repository")
            aws ecr describe-repositories --repository-names $resource_name --region $AWS_REGION > /dev/null 2>&1
            ;;
    esac
}

# Function to wait for service to be stable
wait_for_service_stable() {
    echo "⏳ Waiting for service to be stable..."
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $AWS_REGION
}

# 1. Stop and delete ECS service
echo "🛑 Stopping ECS service..."
if resource_exists "service" $SERVICE_NAME; then
    # Scale down to 0 tasks
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --desired-count 0 \
        --region $AWS_REGION
    
    # Wait for tasks to stop
    echo "⏳ Waiting for tasks to stop..."
    sleep 30
    
    # Delete the service
    echo "🗑️ Deleting ECS service..."
    aws ecs delete-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --region $AWS_REGION
    
    echo "✅ ECS service deleted"
else
    echo "ℹ️ ECS service not found"
fi

# 2. Delete ECS cluster
echo "🗑️ Deleting ECS cluster..."
if resource_exists "cluster" $CLUSTER_NAME; then
    aws ecs delete-cluster \
        --cluster $CLUSTER_NAME \
        --region $AWS_REGION
    
    echo "✅ ECS cluster deleted"
else
    echo "ℹ️ ECS cluster not found"
fi

# 3. Delete ECR repository
echo "🗑️ Deleting ECR repository..."
if resource_exists "repository" $ECR_REPOSITORY_NAME; then
    aws ecr delete-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --force \
        --region $AWS_REGION
    
    echo "✅ ECR repository deleted"
else
    echo "ℹ️ ECR repository not found"
fi

# 4. Delete task definitions
echo "🗑️ Cleaning up task definitions..."
TASK_DEFINITIONS=$(aws ecs list-task-definitions \
    --family-prefix $TASK_DEFINITION_NAME \
    --region $AWS_REGION \
    --query 'taskDefinitionArns' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$TASK_DEFINITIONS" ]; then
    for task_def in $TASK_DEFINITIONS; do
        echo "🗑️ Deregistering task definition: $task_def"
        aws ecs deregister-task-definition \
            --task-definition $task_def \
            --region $AWS_REGION
    done
    echo "✅ Task definitions cleaned up"
else
    echo "ℹ️ No task definitions found"
fi

# 5. Clean up CloudWatch log groups
echo "🗑️ Cleaning up CloudWatch log groups..."
LOG_GROUPS=$(aws logs describe-log-groups \
    --log-group-name-prefix "/ecs/$TASK_DEFINITION_NAME" \
    --region $AWS_REGION \
    --query 'logGroups[].logGroupName' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$LOG_GROUPS" ]; then
    for log_group in $LOG_GROUPS; do
        echo "🗑️ Deleting log group: $log_group"
        aws logs delete-log-group \
            --log-group-name $log_group \
            --region $AWS_REGION
    done
    echo "✅ CloudWatch log groups cleaned up"
else
    echo "ℹ️ No CloudWatch log groups found"
fi

# 6. Clean up Application Load Balancer (if exists)
echo "🔍 Checking for Application Load Balancer..."
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --region $AWS_REGION \
    --query 'LoadBalancers[?contains(LoadBalancerName, `legal-rag`)].LoadBalancerArn' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$ALB_ARN" ]; then
    echo "🗑️ Deleting Application Load Balancer: $ALB_ARN"
    
    # Get target groups
    TARGET_GROUPS=$(aws elbv2 describe-target-groups \
        --region $AWS_REGION \
        --query 'TargetGroups[?contains(TargetGroupName, `legal-rag`)].TargetGroupArn' \
        --output text 2>/dev/null || echo "")
    
    # Delete load balancer
    aws elbv2 delete-load-balancer \
        --load-balancer-arn $ALB_ARN \
        --region $AWS_REGION
    
    # Delete target groups
    if [ ! -z "$TARGET_GROUPS" ]; then
        for tg_arn in $TARGET_GROUPS; do
            echo "🗑️ Deleting target group: $tg_arn"
            aws elbv2 delete-target-group \
                --target-group-arn $tg_arn \
                --region $AWS_REGION
        done
    fi
    
    echo "✅ Application Load Balancer cleaned up"
else
    echo "ℹ️ No Application Load Balancer found"
fi

# 7. Clean up Security Groups (if they were created specifically for this app)
echo "🔍 Checking for security groups..."
SECURITY_GROUPS=$(aws ec2 describe-security-groups \
    --region $AWS_REGION \
    --filters "Name=group-name,Values=*legal-rag*" \
    --query 'SecurityGroups[].GroupId' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$SECURITY_GROUPS" ]; then
    for sg_id in $SECURITY_GROUPS; do
        echo "🗑️ Deleting security group: $sg_id"
        aws ec2 delete-security-group \
            --group-id $sg_id \
            --region $AWS_REGION
    done
    echo "✅ Security groups cleaned up"
else
    echo "ℹ️ No specific security groups found"
fi

# 8. Clean up IAM roles (if they were created)
echo "🔍 Checking for IAM roles..."
IAM_ROLES=$(aws iam list-roles \
    --query 'Roles[?contains(RoleName, `legal-rag`)].RoleName' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$IAM_ROLES" ]; then
    for role_name in $IAM_ROLES; do
        echo "🗑️ Deleting IAM role: $role_name"
        
        # Detach policies first
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
            --role-name $role_name \
            --query 'AttachedPolicies[].PolicyArn' \
            --output text 2>/dev/null || echo "")
        
        for policy_arn in $ATTACHED_POLICIES; do
            aws iam detach-role-policy \
                --role-name $role_name \
                --policy-arn $policy_arn
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies \
            --role-name $role_name \
            --query 'PolicyNames' \
            --output text 2>/dev/null || echo "")
        
        for policy_name in $INLINE_POLICIES; do
            aws iam delete-role-policy \
                --role-name $role_name \
                --policy-name $policy_name
        done
        
        # Delete the role
        aws iam delete-role --role-name $role_name
    done
    echo "✅ IAM roles cleaned up"
else
    echo "ℹ️ No specific IAM roles found"
fi

# 9. Clean up Secrets Manager secrets (if they were created)
echo "🔍 Checking for Secrets Manager secrets..."
SECRETS=$(aws secretsmanager list-secrets \
    --region $AWS_REGION \
    --query 'SecretList[?contains(Name, `legal-rag`)].Name' \
    --output text 2>/dev/null || echo "")

if [ ! -z "$SECRETS" ]; then
    for secret_name in $SECRETS; do
        echo "🗑️ Deleting secret: $secret_name"
        aws secretsmanager delete-secret \
            --secret-id $secret_name \
            --force-delete-without-recovery \
            --region $AWS_REGION
    done
    echo "✅ Secrets Manager secrets cleaned up"
else
    echo "ℹ️ No specific secrets found"
fi

echo ""
echo "✅ Docker resources cleanup completed!"
echo ""
echo "📋 Summary of cleaned resources:"
echo "- ECS Service: $SERVICE_NAME"
echo "- ECS Cluster: $CLUSTER_NAME"
echo "- ECR Repository: $ECR_REPOSITORY_NAME"
echo "- Task Definitions: $TASK_DEFINITION_NAME"
echo "- CloudWatch Log Groups: /ecs/$TASK_DEFINITION_NAME"
echo "- Application Load Balancer (if found)"
echo "- Security Groups (if found)"
echo "- IAM Roles (if found)"
echo "- Secrets Manager secrets (if found)"
echo ""
echo "💡 Next steps:"
echo "1. Verify your EC2 deployment is working correctly"
echo "2. Remove Docker-related files from your repository"
echo "3. Update your documentation"
echo "4. Consider setting up monitoring for your EC2 instance"
