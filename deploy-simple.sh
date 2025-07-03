#!/bin/bash

# Simple Pupper CDK Deployment Script (No Quality Checks)
set -e

echo "🐕 Simple Pupper CDK Deployment"
echo "==============================="

# Check if we're in the right directory
if [ ! -f "app.py" ] || [ ! -f "cdk.json" ]; then
    echo "❌ This script must be run from the pupper-app root directory"
    exit 1
fi

# Get AWS info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "✅ AWS Account: $AWS_ACCOUNT"
echo "✅ AWS Region: $AWS_REGION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install minimal dependencies
echo "📦 Installing CDK dependencies..."
pip install --upgrade pip > /dev/null
pip install aws-cdk-lib==2.100.0 constructs>=10.0.0 cdk-nag>=2.27.0 > /dev/null

# Bootstrap CDK if needed
echo "🚀 Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "🔧 Bootstrapping CDK..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
else
    echo "✅ CDK already bootstrapped"
fi

# Synthesize the stack
echo "🔨 Synthesizing CDK stack..."
cdk synth > /dev/null

# Deploy the stack
echo "🚀 Deploying CDK stack..."
echo ""
echo "⚠️  This will create AWS resources that may incur costs."
read -p "Continue with deployment? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting deployment..."
    cdk deploy --require-approval never --outputs-file cdk-outputs.json
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Deployment completed successfully!"
        
        # Display outputs
        if [ -f "cdk-outputs.json" ]; then
            echo ""
            echo "📋 Stack Outputs:"
            cat cdk-outputs.json | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
        fi
        
        echo ""
        echo "✅ Your Pupper backend is now live!"
        echo "📝 Next steps:"
        echo "   1. Test the API endpoints"
        echo "   2. Run: python3 scripts/verify_deployment.py"
        echo "   3. Run: python3 scripts/populate_test_data.py"
        
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "🛑 Deployment cancelled"
    exit 0
fi
