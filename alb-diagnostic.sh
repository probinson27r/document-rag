#!/bin/bash

# ALB Diagnostic Script
AWS_REGION="ap-southeast-2"

echo "🔍 ALB to EC2 Connection Diagnostic"

# Check ALB
echo "📊 Checking ALB..."
aws elbv2 describe-load-balancers --region $AWS_REGION --query 'LoadBalancers[?contains(LoadBalancerName, `legal-rag`)].{Name: LoadBalancerName, DNS: DNSName, State: State.Code}' --output table

# Check Target Groups
echo "📊 Checking Target Groups..."
aws elbv2 describe-target-groups --region $AWS_REGION --query 'TargetGroups[?contains(TargetGroupName, `legal-rag`)].{Name: TargetGroupName, Port: Port, Protocol: Protocol}' --output table

# Check Target Health
echo "📊 Checking Target Health..."
TARGET_GROUPS=$(aws elbv2 describe-target-groups --region $AWS_REGION --query 'TargetGroups[?contains(TargetGroupName, `legal-rag`)].TargetGroupArn' --output text)

for TG_ARN in $TARGET_GROUPS; do
    echo "Target Group: $TG_ARN"
    aws elbv2 describe-target-health --target-group-arn $TG_ARN --region $AWS_REGION --query 'TargetHealthDescriptions[].{Target: Target.Id, Health: TargetHealth.State, Description: TargetHealth.Description}' --output table
done

echo "💡 Common fixes:"
echo "1. EC2 security group must allow HTTP/HTTPS from ALB security group"
echo "2. Target group must have correct port (5001 for your app)"
echo "3. Application must be running and healthy on EC2"
echo "4. VPC and subnets must be properly configured"
