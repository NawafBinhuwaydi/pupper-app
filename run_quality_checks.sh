#!/bin/bash

# Pupper Project Quality Assurance Script
# This script runs all quality checks for the project

set -e  # Exit on any error

echo "🐕 Pupper Project Quality Assurance Checks"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if virtual environment is activated
check_venv() {
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        print_warning "Virtual environment not detected. Consider activating one."
    else
        print_status "Virtual environment: ${VIRTUAL_ENV}"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    pip install -r requirements-dev.txt > /dev/null 2>&1
    print_success "Dependencies installed"
}

# Code formatting check
check_formatting() {
    print_status "Checking code formatting with Black..."
    if black --check backend/ infra/ tests/ app.py > /dev/null 2>&1; then
        print_success "Code formatting is correct"
    else
        print_error "Code formatting issues found. Run 'make format' to fix."
        return 1
    fi
}

# Import sorting check
check_imports() {
    print_status "Checking import sorting with isort..."
    if isort --check-only backend/ infra/ tests/ app.py > /dev/null 2>&1; then
        print_success "Import sorting is correct"
    else
        print_error "Import sorting issues found. Run 'make format' to fix."
        return 1
    fi
}

# Linting check
check_linting() {
    print_status "Running linting with flake8..."
    if flake8 backend/ infra/ tests/ app.py; then
        print_success "Linting passed"
    else
        print_error "Linting issues found. Please fix the issues above."
        return 1
    fi
}

# Type checking
check_types() {
    print_status "Running type checking with mypy..."
    if mypy backend/ infra/ app.py --ignore-missing-imports > /dev/null 2>&1; then
        print_success "Type checking passed"
    else
        print_warning "Type checking found issues (non-blocking)"
    fi
}

# Unit tests
run_tests() {
    print_status "Running unit tests..."
    if pytest tests/ -v --tb=short; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Test coverage
check_coverage() {
    print_status "Checking test coverage..."
    if pytest tests/ --cov=backend --cov=infra --cov-report=term-missing --cov-report=html > coverage_output.txt 2>&1; then
        coverage_percent=$(grep "TOTAL" coverage_output.txt | awk '{print $4}' | sed 's/%//')
        if [[ -n "$coverage_percent" ]] && [[ "$coverage_percent" -ge 80 ]]; then
            print_success "Test coverage: ${coverage_percent}% (meets 80% threshold)"
        else
            print_warning "Test coverage: ${coverage_percent}% (below 80% threshold)"
        fi
        rm -f coverage_output.txt
    else
        print_error "Coverage check failed"
        rm -f coverage_output.txt
        return 1
    fi
}

# CDK Nag security checks
check_cdk_nag() {
    print_status "Running CDK Nag security checks..."
    export AWS_ACCESS_KEY_ID=testing
    export AWS_SECRET_ACCESS_KEY=testing
    export AWS_DEFAULT_REGION=us-east-1
    
    if cdk synth --quiet > /dev/null 2>&1; then
        print_success "CDK Nag security checks passed"
    else
        print_error "CDK Nag security checks failed"
        return 1
    fi
}

# Security scanning
run_security_scan() {
    print_status "Running security scan with bandit..."
    if command -v bandit > /dev/null 2>&1; then
        if bandit -r backend/ infra/ -q > /dev/null 2>&1; then
            print_success "Security scan passed"
        else
            print_warning "Security scan found potential issues (review manually)"
        fi
    else
        print_warning "Bandit not installed, skipping security scan"
    fi
}

# Clean up artifacts
cleanup() {
    print_status "Cleaning up build artifacts..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf .coverage cdk.out/ 2>/dev/null || true
    print_success "Cleanup completed"
}

# Main execution
main() {
    local start_time=$(date +%s)
    local failed_checks=0
    
    echo ""
    check_venv
    echo ""
    
    # Install dependencies
    install_dependencies || ((failed_checks++))
    echo ""
    
    # Code quality checks
    check_formatting || ((failed_checks++))
    echo ""
    
    check_imports || ((failed_checks++))
    echo ""
    
    check_linting || ((failed_checks++))
    echo ""
    
    check_types || true  # Non-blocking
    echo ""
    
    # Testing
    run_tests || ((failed_checks++))
    echo ""
    
    check_coverage || true  # Non-blocking
    echo ""
    
    # Security checks
    check_cdk_nag || ((failed_checks++))
    echo ""
    
    run_security_scan || true  # Non-blocking
    echo ""
    
    # Cleanup
    cleanup
    echo ""
    
    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "=========================================="
    echo "🐕 Quality Assurance Summary"
    echo "=========================================="
    echo "Duration: ${duration} seconds"
    
    if [[ $failed_checks -eq 0 ]]; then
        print_success "All critical checks passed! ✅"
        echo ""
        echo "Your code is ready for:"
        echo "  • Code review"
        echo "  • Pull request"
        echo "  • Deployment"
        echo ""
        exit 0
    else
        print_error "${failed_checks} critical check(s) failed! ❌"
        echo ""
        echo "Please fix the issues above before:"
        echo "  • Committing code"
        echo "  • Creating pull request"
        echo "  • Deploying to production"
        echo ""
        exit 1
    fi
}

# Handle script interruption
trap 'echo ""; print_warning "Quality checks interrupted"; cleanup; exit 130' INT

# Run main function
main "$@"
