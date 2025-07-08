#!/bin/bash

# Deploy Pupper App with Image Classification
# This script deploys the CDK stack with the new image classification feature

set -e

echo "🐕 Deploying Pupper App with Image Classification"
echo "=================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ Error: AWS CDK not installed. Please install it first:"
    echo "npm install -g aws-cdk"
    exit 1
fi

# Check if Python dependencies are installed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Bootstrap CDK if needed
echo "🚀 Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit > /dev/null 2>&1; then
    echo "🚀 Bootstrapping CDK..."
    cdk bootstrap
else
    echo "✅ CDK already bootstrapped"
fi

# Synthesize the stack to check for errors
echo "🔍 Synthesizing CDK stack..."
cdk synth

# Deploy the stack
echo "🚀 Deploying CDK stack..."
cdk deploy --require-approval never

# Get the API Gateway URL
echo "📋 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name PupperCdkStack \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text 2>/dev/null || echo "")

if [ -n "$API_URL" ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 API Gateway URL: $API_URL"
    echo ""
    echo "📝 Next steps:"
    echo "1. Update test_image_classification.py with your API URL:"
    echo "   API_BASE_URL = \"$API_URL\""
    echo ""
    echo "2. Create test images directory:"
    echo "   mkdir -p test_images"
    echo ""
    echo "3. Add test images (Labrador and non-Labrador photos)"
    echo ""
    echo "4. Run the test script:"
    echo "   python test_image_classification.py"
    echo ""
    echo "📚 For more information, see IMAGE_CLASSIFICATION.md"
else
    echo "⚠️  Deployment completed but couldn't retrieve API URL"
    echo "Check AWS Console for CloudFormation stack outputs"
fi

echo ""
echo "🎉 Deployment complete!"
