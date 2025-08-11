#!/bin/bash
# Setup IAM Role for EC2 and AWS Secrets Manager
# This script creates the necessary IAM role and policies for EC2 to access Secrets Manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔐 Setting up EC2 IAM Role for AWS Secrets Manager Access..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "ap-southeast-2")

echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"
echo "🌏 AWS Region: $AWS_REGION"

# IAM Role name for EC2
ROLE_NAME="LegalRAG-EC2-SecretsManager-Role"
INSTANCE_PROFILE_NAME="LegalRAG-EC2-SecretsManager-Profile"

# Create IAM role trust policy
cat > /tmp/ec2-trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create IAM policy for Secrets Manager access
cat > /tmp/secrets-manager-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:legal-rag/*"
            ]
        }
    ]
}
EOF

echo "🏗️ Creating IAM role and policies..."

# Create IAM role
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ IAM role $ROLE_NAME already exists${NC}"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/ec2-trust-policy.json \
        --description "Role for Legal RAG EC2 instance to access Secrets Manager"
    echo -e "${GREEN}✅ Created IAM role: $ROLE_NAME${NC}"
fi

# Create and attach custom policy for Secrets Manager
POLICY_NAME="LegalRAG-SecretsManager-Policy"
POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"

if aws iam get-policy --policy-arn "$POLICY_ARN" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Policy $POLICY_NAME already exists${NC}"
else
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file:///tmp/secrets-manager-policy.json \
        --description "Policy for Legal RAG to access Secrets Manager"
    echo -e "${GREEN}✅ Created policy: $POLICY_NAME${NC}"
fi

# Attach policy to role
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"
echo -e "${GREEN}✅ Attached Secrets Manager policy to role${NC}"

# Attach AWS managed policy for CloudWatch (optional but useful)
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
echo -e "${GREEN}✅ Attached CloudWatch policy to role${NC}"

# Create instance profile
if aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Instance profile $INSTANCE_PROFILE_NAME already exists${NC}"
else
    aws iam create-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME"
    echo -e "${GREEN}✅ Created instance profile: $INSTANCE_PROFILE_NAME${NC}"
fi

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE_NAME" \
    --role-name "$ROLE_NAME" 2>/dev/null || true
echo -e "${GREEN}✅ Added role to instance profile${NC}"

echo ""
echo "🎯 Next Steps:"
echo "1. Create the AWS secrets (if they don't exist):"
echo "   ./setup-aws-secrets.sh"
echo ""
echo "2. Attach the IAM role to your EC2 instance:"
echo "   - Go to EC2 Console → Instances"
echo "   - Select your instance → Actions → Security → Modify IAM role"
echo "   - Choose: $INSTANCE_PROFILE_NAME"
echo ""
echo "3. Or use AWS CLI to attach the role:"
echo "   aws ec2 associate-iam-instance-profile \\"
echo "     --instance-id YOUR_INSTANCE_ID \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME"
echo ""
echo -e "${GREEN}✅ IAM setup completed!${NC}"

# Clean up temporary files
rm -f /tmp/ec2-trust-policy.json /tmp/secrets-manager-policy.json
