#!/bin/bash

# Deployment script with environment variables
export SECRET_KEY="24a82525c4499951dca21a04534e8ab6de8686f0d22fe63fae824ffac7f80e03"
export AWS_REGION="ap-southeast-2"

echo "🚀 Deploying with configured environment variables..."
echo "SECRET_KEY: 24a82525c4..."
echo "AWS_REGION: ap-southeast-2"

# Run the main deployment script
./deploy-aws.sh
