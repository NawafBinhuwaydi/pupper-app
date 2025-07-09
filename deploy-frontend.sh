#!/bin/bash

# Deploy Pupper Frontend Infrastructure
# This script deploys S3 bucket and CloudFront distribution for static website hosting

set -e

echo "🐕 Deploying Pupper Frontend Infrastructure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ AWS CDK is not installed. Please install it first:${NC}"
    echo "npm install -g aws-cdk"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Build frontend if package.json exists
if [ -f "frontend/package.json" ]; then
    echo -e "${BLUE}🔨 Building frontend...${NC}"
    cd frontend
    
    # Install frontend dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Build the frontend
    echo -e "${BLUE}🏗️ Building React app...${NC}"
    npm run build
    
    cd ..
    echo -e "${GREEN}✅ Frontend build completed${NC}"
else
    echo -e "${YELLOW}⚠️ No frontend package.json found. Skipping frontend build.${NC}"
fi

# Bootstrap CDK if needed
echo -e "${BLUE}🚀 Checking CDK bootstrap...${NC}"
if ! cdk bootstrap 2>/dev/null; then
    echo -e "${YELLOW}⚠️ CDK bootstrap may be needed. Attempting to bootstrap...${NC}"
    cdk bootstrap
fi

# Deploy the frontend stack
echo -e "${BLUE}🚀 Deploying frontend infrastructure...${NC}"
cdk deploy PupperFrontendStack --app "python app_with_frontend.py" --require-approval never

# Get the outputs
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${BLUE}📋 Getting deployment outputs...${NC}"

# Extract outputs from CDK
OUTPUTS=$(cdk list --app "python app_with_frontend.py" 2>/dev/null || echo "")

if [ -f "cdk-outputs.json" ]; then
    echo -e "${GREEN}🎉 Frontend Infrastructure Deployed Successfully!${NC}"
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    
    # Parse and display key outputs
    if command -v jq &> /dev/null; then
        CLOUDFRONT_URL=$(jq -r '.PupperFrontendStack.CloudFrontURL // empty' cdk-outputs.json 2>/dev/null || echo "")
        BUCKET_NAME=$(jq -r '.PupperFrontendStack.FrontendBucketName // empty' cdk-outputs.json 2>/dev/null || echo "")
        DISTRIBUTION_ID=$(jq -r '.PupperFrontendStack.CloudFrontDistributionId // empty' cdk-outputs.json 2>/dev/null || echo "")
        
        if [ ! -z "$CLOUDFRONT_URL" ]; then
            echo -e "${GREEN}🌐 CloudFront URL: ${CLOUDFRONT_URL}${NC}"
        fi
        if [ ! -z "$BUCKET_NAME" ]; then
            echo -e "${GREEN}🪣 S3 Bucket: ${BUCKET_NAME}${NC}"
        fi
        if [ ! -z "$DISTRIBUTION_ID" ]; then
            echo -e "${GREEN}📡 Distribution ID: ${DISTRIBUTION_ID}${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ jq not installed. Install jq to see parsed outputs.${NC}"
        echo -e "${BLUE}Raw outputs in cdk-outputs.json${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ No outputs file found. Check CDK deployment logs above.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Frontend deployment completed!${NC}"
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Your frontend is now hosted on CloudFront"
echo "2. Static assets are served from S3 with global caching"
echo "3. HTTPS is automatically enabled"
echo "4. To update the frontend, rebuild and run this script again"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "- CloudFront distributions take 10-15 minutes to fully deploy"
echo "- Use the CloudFront URL for production access"
echo "- S3 website URL is also available for direct access"
echo "- Check AWS Console for detailed monitoring and logs"
