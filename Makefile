# Pupper Project Makefile

.PHONY: help install install-dev format lint type-check test test-cov clean deploy destroy cdk-nag

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run linting with flake8"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  test         - Run unit tests"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  cdk-nag      - Run CDK Nag security checks"
	@echo "  clean        - Clean build artifacts"
	@echo "  deploy       - Deploy CDK stack"
	@echo "  destroy      - Destroy CDK stack"
	@echo "  ci           - Run all CI checks (format, lint, type-check, test)"

# Install dependencies
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Code formatting
format:
	@echo "Formatting code with black..."
	black backend/ infra/ tests/ app.py
	@echo "Sorting imports with isort..."
	isort backend/ infra/ tests/ app.py
	@echo "Code formatting complete!"

# Linting
lint:
	@echo "Running flake8 linting..."
	flake8 backend/ infra/ tests/ app.py
	@echo "Linting complete!"

# Type checking
type-check:
	@echo "Running mypy type checking..."
	mypy backend/ infra/ app.py --ignore-missing-imports
	@echo "Type checking complete!"

# Testing
test:
	@echo "Running unit tests..."
	pytest tests/ -v
	@echo "Tests complete!"

test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=backend --cov=infra --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/"

# CDK Nag security checks
cdk-nag:
	@echo "Running CDK Nag security checks..."
	cdk synth --quiet
	@echo "CDK Nag checks complete!"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage cdk.out/ dist/ build/
	@echo "Clean complete!"

# CDK operations
deploy:
	@echo "Deploying CDK stack..."
	cdk deploy --require-approval never
	@echo "Deployment complete!"

destroy:
	@echo "Destroying CDK stack..."
	cdk destroy --force
	@echo "Stack destroyed!"

# CI pipeline
ci: format lint type-check test
	@echo "All CI checks passed!"

# Development setup
setup-dev: install-dev
	@echo "Development environment setup complete!"

# Run local tests with moto
test-local:
	@echo "Running tests with local AWS mocks..."
	AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing pytest tests/ -v
	@echo "Local tests complete!"

# Format check (for CI)
format-check:
	@echo "Checking code formatting..."
	black --check backend/ infra/ tests/ app.py
	isort --check-only backend/ infra/ tests/ app.py
	@echo "Format check complete!"
