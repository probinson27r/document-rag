#!/bin/bash

# Setup Google API Key in AWS Secrets Manager
# This script helps store the Google API key securely in AWS Secrets Manager

echo "🔐 Google API Key Setup for AWS Secrets Manager"
echo "=============================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

echo "✅ AWS CLI detected and credentials configured"
echo ""

# Prompt for Google API key
echo "📝 Please enter your Google API key:"
echo "   (You can get this from: https://console.cloud.google.com/apis/credentials)"
read -s -p "Google API Key: " GOOGLE_API_KEY
echo ""

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ No API key provided. Exiting."
    exit 1
fi

echo ""
echo "🔄 Storing Google API key in AWS Secrets Manager..."

# Store the secret
SECRET_NAME="legal-rag/google-api-key"
REGION="ap-southeast-2"

if aws secretsmanager create-secret \
    --name "$SECRET_NAME" \
    --description "Google API key for LangExtract integration in Legal Document RAG system" \
    --secret-string "$GOOGLE_API_KEY" \
    --region "$REGION" &> /dev/null; then
    echo "✅ Google API key created successfully in AWS Secrets Manager"
else
    # Try to update if it already exists
    if aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$GOOGLE_API_KEY" \
        --region "$REGION" &> /dev/null; then
        echo "✅ Google API key updated successfully in AWS Secrets Manager"
    else
        echo "❌ Failed to store Google API key in AWS Secrets Manager"
        exit 1
    fi
fi

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo "• Secret name: $SECRET_NAME"
echo "• Region: $REGION"
echo "• The LangExtract integration will now use this secure key"
echo ""
echo "📋 Next steps:"
echo "1. Deploy your application to EC2"
echo "2. Ensure the EC2 instance has IAM permissions to read secrets"
echo "3. Test LangExtract chunking - it should automatically use the AWS secret"
echo ""
echo "🔧 If you need to update the key later, run this script again"
