#!/bin/bash

# Pupper CDK Deployment Script
set -e  # Exit on any error

echo "🐕 Pupper CDK Deployment"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app.py" ] || [ ! -f "cdk.json" ]; then
    print_error "This script must be run from the pupper-app root directory"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python version: $PYTHON_VERSION"

# Check Node.js and npm for CDK
print_status "Checking Node.js and CDK..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is required for AWS CDK"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm is required for AWS CDK"
    exit 1
fi

NODE_VERSION=$(node -v)
print_success "Node.js version: $NODE_VERSION"

# Check if AWS CDK is installed
if ! command -v cdk &> /dev/null; then
    print_warning "AWS CDK not found. Installing globally..."
    npm install -g aws-cdk
    if [ $? -ne 0 ]; then
        print_error "Failed to install AWS CDK"
        exit 1
    fi
    print_success "AWS CDK installed successfully"
fi

CDK_VERSION=$(cdk --version)
print_success "CDK version: $CDK_VERSION"

# Check AWS CLI
print_status "Checking AWS CLI configuration..."
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is required but not installed"
    print_error "Please install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid"
    print_error "Please run 'aws configure' to set up your credentials"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
print_success "AWS Account: $AWS_ACCOUNT"
print_success "AWS Region: $AWS_REGION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
print_success "Python dependencies installed"

# Run quality checks
print_status "Running quality checks..."
if [ -f "run_quality_checks.sh" ]; then
    ./run_quality_checks.sh
    if [ $? -ne 0 ]; then
        print_warning "Quality checks failed, but continuing with deployment"
    fi
else
    print_warning "Quality check script not found, skipping"
fi

# Bootstrap CDK (if needed)
print_status "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    print_status "Bootstrapping CDK for account $AWS_ACCOUNT in region $AWS_REGION..."
    cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION
    if [ $? -ne 0 ]; then
        print_error "CDK bootstrap failed"
        exit 1
    fi
    print_success "CDK bootstrap completed"
else
    print_success "CDK already bootstrapped"
fi

# Synthesize CDK stack
print_status "Synthesizing CDK stack..."
cdk synth
if [ $? -ne 0 ]; then
    print_error "CDK synthesis failed"
    exit 1
fi
print_success "CDK synthesis completed"

# Deploy the stack
print_status "Deploying CDK stack..."
echo ""
print_warning "This will deploy AWS resources that may incur costs."
read -p "Do you want to continue? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting deployment..."
    cdk deploy --require-approval never --outputs-file cdk-outputs.json
    
    if [ $? -eq 0 ]; then
        print_success "🎉 Deployment completed successfully!"
        echo ""
        
        # Display outputs if available
        if [ -f "cdk-outputs.json" ]; then
            print_status "Stack outputs:"
            cat cdk-outputs.json | python3 -m json.tool
        fi
        
        echo ""
        print_status "Next steps:"
        echo "1. Test the API endpoints"
        echo "2. Upload some test dog data"
        echo "3. Deploy the frontend application"
        echo ""
        print_success "Your Pupper backend is now live! 🐕"
        
    else
        print_error "Deployment failed"
        exit 1
    fi
else
    print_status "Deployment cancelled by user"
    exit 0
fi
