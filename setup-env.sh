#!/bin/bash

# Environment Setup Script for Legal Document RAG System
# This script helps you set up environment variables and AWS Secrets Manager

set -e

# Configuration
AWS_REGION="ap-southeast-2"  # Change to your preferred region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Setting up environment variables and secrets for Legal Document RAG System..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"
echo "🌍 AWS Region: $AWS_REGION"
echo ""

# Function to prompt for secret value
prompt_for_secret() {
    local secret_name=$1
    local prompt_text=$2
    local is_required=$3
    
    echo ""
    if [ "$is_required" = "true" ]; then
        echo "🔑 $prompt_text (REQUIRED):"
    else
        echo "🔑 $prompt_text (OPTIONAL - press Enter to skip):"
    fi
    
    read -s secret_value
    echo ""
    
    if [ -n "$secret_value" ]; then
        echo "✅ $secret_name will be set"
        return 0
    elif [ "$is_required" = "true" ]; then
        echo "❌ $secret_name is required but was not provided"
        return 1
    else
        echo "ℹ️ Skipping $secret_name"
        return 2
    fi
}

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo "ℹ️ Skipping $secret_name (no value provided)"
        return
    fi
    
    echo "🔐 Creating/updating secret: $secret_name"
    
    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region $AWS_REGION > /dev/null 2>&1; then
        echo "📝 Updating existing secret: $secret_name"
        aws secretsmanager update-secret \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region $AWS_REGION
    else
        echo "🆕 Creating new secret: $secret_name"
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --secret-string "$secret_value" \
            --region $AWS_REGION
    fi
    
    echo "✅ Secret $secret_name configured successfully"
}

# Step 1: Set up SECRET_KEY
echo "=== Step 1: Flask Secret Key ==="
echo "The SECRET_KEY is used for Flask session management and security."
echo "It should be a long, random string for production use."

SECRET_KEY=""
prompt_for_secret "SECRET_KEY" "Enter your Flask SECRET_KEY (or press Enter to generate one)" "false"

if [ $? -eq 0 ]; then
    # User provided a secret key
    SECRET_KEY="$secret_value"
elif [ $? -eq 2 ]; then
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    echo "🔐 Generated SECRET_KEY: $SECRET_KEY"
    echo "💡 Save this key for future reference!"
fi

# Step 2: Set up API Keys
echo ""
echo "=== Step 2: API Keys ==="
echo "These are optional but recommended for full functionality."

# Anthropic API Key
ANTHROPIC_API_KEY=""
prompt_for_secret "ANTHROPIC_API_KEY" "Enter your Anthropic (Claude) API key" "false"
if [ $? -eq 0 ]; then
    ANTHROPIC_API_KEY="$secret_value"
fi

# OpenAI API Key
OPENAI_API_KEY=""
prompt_for_secret "OPENAI_API_KEY" "Enter your OpenAI API key" "false"
if [ $? -eq 0 ]; then
    OPENAI_API_KEY="$secret_value"
fi

# Private GPT-4 API Key
PRIVATE_GPT4_API_KEY=""
prompt_for_secret "PRIVATE_GPT4_API_KEY" "Enter your Private GPT-4 API key" "false"
if [ $? -eq 0 ]; then
    PRIVATE_GPT4_API_KEY="$secret_value"
fi

# Step 3: Create/Update Secrets in AWS Secrets Manager
echo ""
echo "=== Step 3: Creating AWS Secrets ==="

# Create secrets
create_or_update_secret "legal-rag/secret-key" "$SECRET_KEY"
create_or_update_secret "legal-rag/anthropic-api-key" "$ANTHROPIC_API_KEY"
create_or_update_secret "legal-rag/openai-api-key" "$OPENAI_API_KEY"
create_or_update_secret "legal-rag/private-gpt4-api-key" "$PRIVATE_GPT4_API_KEY"

# Step 4: Create environment file for local development
echo ""
echo "=== Step 4: Creating Local Environment File ==="

cat > .env.local << EOF
# Local Development Environment Variables
# Copy this file to .env for local development

FLASK_ENV=development
SECRET_KEY=$SECRET_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
PRIVATE_GPT4_API_KEY=$PRIVATE_GPT4_API_KEY
EOF

echo "✅ Created .env.local file for local development"
echo "💡 Copy .env.local to .env to use these variables locally"

# Step 5: Update deployment script with SECRET_KEY
echo ""
echo "=== Step 5: Updating Deployment Script ==="

# Create a deployment script with the SECRET_KEY
cat > deploy-with-env.sh << EOF
#!/bin/bash

# Deployment script with environment variables
export SECRET_KEY="$SECRET_KEY"
export AWS_REGION="$AWS_REGION"

echo "🚀 Deploying with configured environment variables..."
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "AWS_REGION: $AWS_REGION"

# Run the main deployment script
./deploy-aws.sh
EOF

chmod +x deploy-with-env.sh

echo "✅ Created deploy-with-env.sh script"
echo "💡 Use ./deploy-with-env.sh to deploy with your configured environment"

# Step 6: Summary
echo ""
echo "🎉 Environment setup completed!"
echo ""
echo "📋 Summary:"
echo "- SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "- ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "- OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "- PRIVATE_GPT4_API_KEY: ${PRIVATE_GPT4_API_KEY:+SET}"
echo ""
echo "📁 Files created:"
echo "- .env.local (for local development)"
echo "- deploy-with-env.sh (for deployment)"
echo ""
echo "🔗 AWS Secrets created in region: $AWS_REGION"
echo "- legal-rag/secret-key"
echo "- legal-rag/anthropic-api-key"
echo "- legal-rag/openai-api-key"
echo "- legal-rag/private-gpt4-api-key"
echo ""
echo "📋 Next steps:"
echo "1. For local development: cp .env.local .env"
echo "2. For AWS deployment: ./deploy-with-env.sh"
echo "3. To check secrets: ./check-aws-resources.sh" 