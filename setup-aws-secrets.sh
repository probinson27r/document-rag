#!/bin/bash
# Setup AWS Secrets Manager secrets for Legal Document RAG system
# This script creates the necessary secrets in AWS Secrets Manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔐 Setting up AWS Secrets Manager for Legal Document RAG..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS region
AWS_REGION=$(aws configure get region || echo "ap-southeast-2")
echo "🌏 AWS Region: $AWS_REGION"

# Function to create or update a secret
create_or_update_secret() {
    local secret_name="$1"
    local secret_description="$2"
    local prompt_message="$3"
    
    echo ""
    echo -e "${BLUE}📝 Setting up: $secret_name${NC}"
    echo "$secret_description"
    
    # Check if secret already exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Secret $secret_name already exists${NC}"
        read -p "Do you want to update it? (y/N): " update_choice
        if [[ "$update_choice" != "y" && "$update_choice" != "Y" ]]; then
            echo "Skipping $secret_name"
            return
        fi
        action="update"
    else
        action="create"
    fi
    
    # Prompt for secret value
    echo "$prompt_message"
    read -s -p "Enter value (input hidden): " secret_value
    echo ""
    
    if [ -z "$secret_value" ]; then
        echo -e "${YELLOW}⚠️ No value entered, skipping $secret_name${NC}"
        return
    fi
    
    # Create or update the secret
    if [ "$action" = "create" ]; then
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$secret_description" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION"
        echo -e "${GREEN}✅ Created secret: $secret_name${NC}"
    else
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION"
        echo -e "${GREEN}✅ Updated secret: $secret_name${NC}"
    fi
}

echo ""
echo "🚀 We'll now set up the required secrets for your Legal Document RAG system."
echo "These secrets will be stored securely in AWS Secrets Manager."
echo ""

# Set up each secret
create_or_update_secret \
    "legal-rag/secret-key" \
    "Flask application secret key for session management" \
    "Enter a secure random string for Flask sessions (e.g., generated with 'openssl rand -base64 32'):"

create_or_update_secret \
    "legal-rag/anthropic-api-key" \
    "Anthropic Claude API key for AI processing" \
    "Enter your Anthropic Claude API key (from https://console.anthropic.com/):"

create_or_update_secret \
    "legal-rag/openai-api-key" \
    "OpenAI API key for GPT models" \
    "Enter your OpenAI API key (from https://platform.openai.com/api-keys):"

create_or_update_secret \
    "legal-rag/private-gpt4-api-key" \
    "Private GPT-4 API key for enterprise models" \
    "Enter your Private GPT-4 API key (for DoE Sensai endpoint):"

echo ""
echo -e "${GREEN}✅ AWS Secrets setup completed!${NC}"
echo ""
echo "🔍 You can verify the secrets were created with:"
echo "aws secretsmanager list-secrets --region $AWS_REGION --query 'SecretList[?contains(Name, \`legal-rag\`)].Name' --output table"
echo ""
echo "🎯 Next Steps:"
echo "1. Make sure your EC2 instance has the IAM role attached (from setup-ec2-iam-secrets.sh)"
echo "2. Restart your application: sudo systemctl restart legal-rag"
echo "3. Check logs: sudo journalctl -u legal-rag -f"
echo ""
echo "💡 If you need to update any secrets later, just run this script again."
