#!/bin/bash

# Complete Pupper Application Deployment
# Deploys both backend and frontend infrastructure

set -e

echo "🐕 Complete Pupper Application Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v cdk &> /dev/null; then
    echo -e "${RED}❌ AWS CDK is not installed. Please install it first:${NC}"
    echo "npm install -g aws-cdk"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Build frontend
echo -e "${BLUE}🔨 Building frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    
    # Install frontend dependencies
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
    echo -e "${YELLOW}⚠️ Frontend directory not found. Skipping frontend build.${NC}"
fi

# Bootstrap CDK if needed
echo -e "${BLUE}🚀 Checking CDK bootstrap...${NC}"
if ! cdk bootstrap 2>/dev/null; then
    echo -e "${YELLOW}⚠️ CDK bootstrap may be needed. Attempting to bootstrap...${NC}"
    cdk bootstrap
fi

# Deploy backend stack
echo -e "${BLUE}🚀 Deploying backend infrastructure...${NC}"
cdk deploy PupperBackendStack --app "python app_with_frontend.py" --require-approval never

# Deploy frontend stack
echo -e "${BLUE}🚀 Deploying frontend infrastructure...${NC}"
cdk deploy PupperFrontendStack --app "python app_with_frontend.py" --require-approval never

# Get deployment outputs
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${BLUE}📋 Getting deployment outputs...${NC}"

if [ -f "cdk-outputs.json" ]; then
    echo -e "${GREEN}🎉 Complete Application Deployed Successfully!${NC}"
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    
    if command -v jq &> /dev/null; then
        # Backend outputs
        API_URL=$(jq -r '.PupperBackendStack.ApiGatewayUrl // empty' cdk-outputs.json 2>/dev/null || echo "")
        IMAGES_BUCKET=$(jq -r '.PupperBackendStack.ImagesBucketName // empty' cdk-outputs.json 2>/dev/null || echo "")
        
        # Frontend outputs
        CLOUDFRONT_URL=$(jq -r '.PupperFrontendStack.CloudFrontURL // empty' cdk-outputs.json 2>/dev/null || echo "")
        FRONTEND_BUCKET=$(jq -r '.PupperFrontendStack.FrontendBucketName // empty' cdk-outputs.json 2>/dev/null || echo "")
        DISTRIBUTION_ID=$(jq -r '.PupperFrontendStack.CloudFrontDistributionId // empty' cdk-outputs.json 2>/dev/null || echo "")
        
        echo ""
        echo -e "${GREEN}🔗 Backend Infrastructure:${NC}"
        if [ ! -z "$API_URL" ]; then
            echo -e "  API Gateway URL: ${API_URL}"
        fi
        if [ ! -z "$IMAGES_BUCKET" ]; then
            echo -e "  Images Bucket: ${IMAGES_BUCKET}"
        fi
        
        echo ""
        echo -e "${GREEN}🌐 Frontend Infrastructure:${NC}"
        if [ ! -z "$CLOUDFRONT_URL" ]; then
            echo -e "  CloudFront URL: ${CLOUDFRONT_URL}"
        fi
        if [ ! -z "$FRONTEND_BUCKET" ]; then
            echo -e "  Frontend Bucket: ${FRONTEND_BUCKET}"
        fi
        if [ ! -z "$DISTRIBUTION_ID" ]; then
            echo -e "  Distribution ID: ${DISTRIBUTION_ID}"
        fi
        
        # Update frontend environment with API URL
        if [ ! -z "$API_URL" ] && [ -f "frontend/.env" ]; then
            echo -e "${BLUE}🔧 Updating frontend environment...${NC}"
            if grep -q "REACT_APP_API_URL" frontend/.env; then
                sed -i "s|REACT_APP_API_URL=.*|REACT_APP_API_URL=${API_URL}|" frontend/.env
            else
                echo "REACT_APP_API_URL=${API_URL}" >> frontend/.env
            fi
            echo -e "${GREEN}✅ Frontend environment updated${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️ jq not installed. Install jq to see parsed outputs.${NC}"
        echo -e "${BLUE}Raw outputs in cdk-outputs.json${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ No outputs file found. Check CDK deployment logs above.${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Complete deployment finished!${NC}"
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Your Pupper application is now fully deployed"
echo "2. Backend API is available via API Gateway"
echo "3. Frontend is hosted on CloudFront with global distribution"
echo "4. Both HTTP and HTTPS are supported (HTTPS recommended)"
echo "5. CloudFront distribution may take 10-15 minutes to fully propagate"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo "- Test API: curl \$API_GATEWAY_URL/dogs"
echo "- Invalidate CloudFront: python scripts/frontend-utils.py invalidate"
echo "- Check status: python scripts/frontend-utils.py status"
echo "- View logs: aws logs tail /aws/lambda/pupper-api --follow"
echo ""
echo -e "${GREEN}🚀 Your Pupper Dog Adoption App is ready!${NC}"
