# Testing and Quality Assurance Guide

This document outlines the testing strategy, quality assurance processes, and development tools for the Pupper application.

## Overview

The project implements comprehensive testing and quality assurance including:

- **Unit Tests**: REST API and CDK infrastructure tests
- **Structured Logging**: JSON-formatted logs with context
- **Distributed Tracing**: AWS X-Ray integration
- **Security Scanning**: CDK Nag compliance checks
- **Code Quality**: Linting, formatting, and type checking
- **CI/CD Pipeline**: Automated testing and deployment

## Testing Strategy

### Unit Tests

#### REST API Tests (`tests/test_api_*.py`)
- **Create Dog API**: Tests for dog creation, validation, and error handling
- **Read Dog API**: Tests for dog retrieval, filtering, and data transformation
- **Update Dog API**: Tests for dog updates and voting functionality
- **Delete Dog API**: Tests for dog deletion and cleanup

#### CDK Infrastructure Tests (`tests/test_cdk_stack.py`)
- **Resource Creation**: Validates all AWS resources are created
- **Configuration**: Checks resource properties and settings
- **Security**: Verifies security configurations and policies
- **Integration**: Tests resource relationships and dependencies

#### Schema Tests (`tests/test_schemas.py`)
- **Data Validation**: Tests input validation and sanitization
- **Encryption**: Tests dog name encryption/decryption
- **Response Formatting**: Tests API response structure
- **Filter Parsing**: Tests query parameter handling

#### Logging Tests (`tests/test_logging.py`)
- **Structured Logging**: Tests log format and context
- **Performance Logging**: Tests timing and metrics
- **Error Logging**: Tests exception handling and reporting

### Running Tests

```bash
# Install test dependencies
make install-dev

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_api_create_dog.py -v

# Run tests with local AWS mocks
make test-local
```

## Structured Logging

### Implementation (`backend/utils/logger.py`)

The application uses `structlog` for structured JSON logging with:

- **Service Context**: Service name, version, environment
- **Request Context**: Request ID, user agent, source IP
- **Performance Metrics**: Duration, response size, status codes
- **Error Context**: Error type, message, stack trace

### Usage Examples

```python
from utils.logger import get_lambda_logger, log_api_request

# In Lambda function
logger = get_lambda_logger(context)
request_logger = log_api_request(logger, event, "POST", "/dogs")

# Log with context
logger.info("Processing dog creation", dog_id="123", shelter="Arlington")

# Log errors with context
logger.error("Database error", error=str(e), table="pupper-dogs")
```

### Log Format

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "info",
  "service": "pupper-api",
  "version": "1.0.0",
  "environment": "production",
  "aws_region": "us-east-1",
  "request_id": "abc-123",
  "message": "Dog created successfully",
  "dog_id": "dog-456",
  "duration_ms": 150.5
}
```

## Distributed Tracing

### Implementation (`backend/utils/tracing.py`)

AWS X-Ray tracing is implemented with:

- **Lambda Handler Tracing**: Automatic request/response tracing
- **Function Tracing**: Custom subsegment creation
- **Database Tracing**: DynamoDB operation tracking
- **S3 Tracing**: File operation monitoring

### Usage Examples

```python
from utils.tracing import trace_lambda_handler, trace_function

# Trace Lambda handler
@trace_lambda_handler
def lambda_handler(event, context):
    return process_request(event)

# Trace custom functions
@trace_function(name="process_dog_data")
def process_dog(dog_data):
    return validate_and_save(dog_data)

# Trace database operations
@trace_database_operation("put_item", "pupper-dogs")
def save_dog(dog_record):
    table.put_item(Item=dog_record)
```

### Trace Metadata

Traces include:
- **Request Information**: HTTP method, path, headers
- **Performance Metrics**: Duration, memory usage
- **Database Operations**: Table name, operation type, item count
- **Error Information**: Exception type, message, stack trace

## Security and Compliance

### CDK Nag Integration

CDK Nag performs security and compliance checks:

```bash
# Run CDK Nag checks
make cdk-nag

# Deploy with security validation
cdk deploy --require-approval never
```

### Security Features Implemented

- **S3 Security**: SSL enforcement, public access blocking
- **IAM Policies**: Least privilege access, explicit permissions
- **DynamoDB**: Point-in-time recovery, encryption at rest
- **Lambda**: Reserved concurrency, X-Ray tracing enabled
- **API Gateway**: CORS configuration, logging enabled

### Suppressions

Security findings are suppressed with justification:

```python
NagSuppressions.add_resource_suppressions(
    resource,
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Wildcard permissions needed for X-Ray tracing"
        }
    ]
)
```

## Code Quality

### Linting and Formatting

#### Black (Code Formatting)
```bash
# Format code
make format

# Check formatting
black --check backend/ infra/ tests/
```

#### isort (Import Sorting)
```bash
# Sort imports
isort backend/ infra/ tests/

# Check import order
isort --check-only backend/ infra/ tests/
```

#### Flake8 (Linting)
```bash
# Run linting
make lint

# Custom configuration in .flake8
flake8 backend/ infra/ tests/
```

#### MyPy (Type Checking)
```bash
# Run type checking
make type-check

# Configuration in pyproject.toml
mypy backend/ infra/ --ignore-missing-imports
```

### Configuration Files

- **pyproject.toml**: Tool configuration (Black, isort, pytest, coverage)
- **.flake8**: Linting rules and exclusions
- **Makefile**: Development commands and workflows

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

The pipeline includes:

1. **Lint and Format Check**
   - Code formatting validation
   - Import sorting check
   - Linting with flake8
   - Type checking with mypy

2. **Unit Tests**
   - Test execution with pytest
   - Coverage reporting
   - AWS service mocking with moto

3. **CDK Nag Security Checks**
   - Infrastructure security validation
   - Compliance checking
   - Security best practices

4. **Integration Tests** (on main branch)
   - Deploy test stack
   - Run integration tests
   - Cleanup resources

5. **Deployment**
   - Staging deployment (develop branch)
   - Production deployment (main branch)
   - Smoke tests

### Pre-commit Hooks

Automated quality checks before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Development Workflow

### Local Development

```bash
# Setup development environment
make setup-dev

# Run quality checks
make ci

# Run tests with coverage
make test-cov

# Clean build artifacts
make clean
```

### Code Review Checklist

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Linting passes
- [ ] Type checking passes
- [ ] CDK Nag checks pass
- [ ] Structured logging implemented
- [ ] Tracing added to new functions
- [ ] Security considerations addressed
- [ ] Documentation updated

### Performance Monitoring

#### Metrics Tracked

- **API Response Times**: Request duration and latency
- **Database Performance**: Query execution time
- **Error Rates**: Success/failure ratios
- **Resource Utilization**: Memory and CPU usage

#### Alerting

CloudWatch alarms for:
- High error rates (>5%)
- Slow response times (>2s)
- Database throttling
- Lambda timeout errors

## Troubleshooting

### Common Issues

#### Test Failures
```bash
# Run specific test with verbose output
pytest tests/test_api_create_dog.py::TestCreateDogAPI::test_create_dog_success -v -s

# Debug with pdb
pytest --pdb tests/test_api_create_dog.py
```

#### CDK Nag Failures
```bash
# View detailed CDK Nag output
cdk synth --verbose

# Check suppression rules
grep -r "NagSuppressions" infra/
```

#### Logging Issues
```bash
# Test logging locally
python -c "from backend.utils.logger import setup_logging; logger = setup_logging(); logger.info('test')"

# Check log format
AWS_LAMBDA_FUNCTION_NAME=test python -c "from backend.utils.logger import get_lambda_logger; logger = get_lambda_logger(type('Context', (), {'aws_request_id': 'test'})()); logger.info('test')"
```

### Performance Optimization

- **Lambda Cold Starts**: Use provisioned concurrency for critical functions
- **Database Queries**: Optimize with appropriate indexes
- **Image Processing**: Use appropriate memory allocation
- **API Gateway**: Enable caching for read operations

## Best Practices

### Testing
- Write tests before implementation (TDD)
- Maintain >80% code coverage
- Use descriptive test names
- Mock external dependencies
- Test error conditions

### Logging
- Use structured logging consistently
- Include relevant context
- Log at appropriate levels
- Avoid logging sensitive data
- Use correlation IDs

### Security
- Follow least privilege principle
- Encrypt sensitive data
- Validate all inputs
- Use CDK Nag suppressions sparingly
- Regular security reviews

### Code Quality
- Follow PEP 8 style guide
- Use type hints
- Write clear documentation
- Keep functions small and focused
- Handle errors gracefully
