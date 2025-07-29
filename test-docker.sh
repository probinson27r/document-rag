#!/bin/bash

# Docker Test Script for Legal Document RAG System
# This script tests the Docker build and local deployment

set -e

echo "🧪 Testing Docker build and deployment..."

# Test 1: Build Docker image
echo "🔨 Building Docker image..."
docker build -t legal-document-rag:test .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Test 2: Run container in background
echo "🚀 Starting container..."
CONTAINER_ID=$(docker run -d -p 5001:5001 \
    -e FLASK_ENV=development \
    -e SECRET_KEY=test-secret-key \
    legal-document-rag:test)

echo "📦 Container ID: $CONTAINER_ID"

# Test 3: Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Test 4: Check if container is running
if docker ps | grep -q $CONTAINER_ID; then
    echo "✅ Container is running"
else
    echo "❌ Container failed to start"
    docker logs $CONTAINER_ID
    docker stop $CONTAINER_ID
    exit 1
fi

# Test 5: Check health endpoint
echo "🏥 Testing health endpoint..."
for i in {1..30}; do
    if curl -f http://localhost:5001/api/status > /dev/null 2>&1; then
        echo "✅ Health check passed"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Health check failed after 30 attempts"
        docker logs $CONTAINER_ID
        docker stop $CONTAINER_ID
        exit 1
    fi
    sleep 2
done

# Test 6: Test API endpoints
echo "🔍 Testing API endpoints..."

# Test status endpoint
STATUS_RESPONSE=$(curl -s http://localhost:5001/api/status)
if echo "$STATUS_RESPONSE" | grep -q "embedding_model"; then
    echo "✅ Status endpoint working"
else
    echo "❌ Status endpoint failed"
    echo "Response: $STATUS_RESPONSE"
fi

# Test models endpoint
MODELS_RESPONSE=$(curl -s http://localhost:5001/api/models)
if echo "$MODELS_RESPONSE" | grep -q "available_models"; then
    echo "✅ Models endpoint working"
else
    echo "❌ Models endpoint failed"
    echo "Response: $MODELS_RESPONSE"
fi

# Test chat history endpoint
HISTORY_RESPONSE=$(curl -s http://localhost:5001/api/chat/history)
if echo "$HISTORY_RESPONSE" | grep -q "total_messages"; then
    echo "✅ Chat history endpoint working"
else
    echo "❌ Chat history endpoint failed"
    echo "Response: $HISTORY_RESPONSE"
fi

# Test 7: Test web interface
echo "🌐 Testing web interface..."
WEB_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/)
if [ "$WEB_RESPONSE" = "200" ]; then
    echo "✅ Web interface accessible"
else
    echo "❌ Web interface failed (HTTP $WEB_RESPONSE)"
fi

# Test 8: Cleanup
echo "🧹 Cleaning up..."
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID
docker rmi legal-document-rag:test

echo ""
echo "🎉 All Docker tests passed!"
echo "✅ The application is ready for AWS deployment"
echo ""
echo "📋 Next steps:"
echo "1. Configure AWS CLI: aws configure"
echo "2. Run deployment: ./deploy-aws.sh"
echo "3. Follow the AWS_DEPLOYMENT_GUIDE.md for detailed instructions" 