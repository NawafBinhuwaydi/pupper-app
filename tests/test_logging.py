"""
Unit tests for logging utilities
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import structlog

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.logger import (
    setup_logging,
    get_lambda_logger,
    log_api_request,
    log_api_response,
    log_database_operation,
    log_s3_operation,
    LoggingMixin,
)


class TestLoggingSetup:
    """Test cases for logging setup"""

    def test_setup_logging_default(self):
        """Test default logging setup"""
        logger = setup_logging()

        assert isinstance(logger, structlog.BoundLogger)
        # Should have service context bound
        assert hasattr(logger, "_context")

    def test_setup_logging_custom_service(self):
        """Test logging setup with custom service name"""
        service_name = "test-service"
        logger = setup_logging(service_name=service_name)

        assert isinstance(logger, structlog.BoundLogger)

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_setup_logging_debug_level(self):
        """Test logging setup with debug level"""
        logger = setup_logging(log_level="DEBUG")

        assert isinstance(logger, structlog.BoundLogger)

    def test_setup_logging_json_disabled(self):
        """Test logging setup with JSON formatting disabled"""
        logger = setup_logging(enable_json=False)

        assert isinstance(logger, structlog.BoundLogger)


class TestLambdaLogger:
    """Test cases for Lambda logger"""

    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context"""
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        context.function_name = "test-function"
        context.function_version = "1"
        context.memory_limit_in_mb = 128
        context.get_remaining_time_in_millis.return_value = 30000
        return context

    def test_get_lambda_logger(self, mock_context):
        """Test getting Lambda logger with context"""
        logger = get_lambda_logger(mock_context)

        assert isinstance(logger, structlog.BoundLogger)
        # Should have Lambda context bound
        assert hasattr(logger, "_context")

    @patch.dict(os.environ, {"LOG_LEVEL": "ERROR"})
    def test_get_lambda_logger_custom_level(self, mock_context):
        """Test Lambda logger with custom log level"""
        logger = get_lambda_logger(mock_context)

        assert isinstance(logger, structlog.BoundLogger)


class TestAPILogging:
    """Test cases for API logging functions"""

    @pytest.fixture
    def mock_logger(self):
        """Mock structured logger"""
        logger = MagicMock()
        logger.bind.return_value = logger
        logger.info.return_value = None
        return logger

    @pytest.fixture
    def api_event(self):
        """Mock API Gateway event"""
        return {
            "requestContext": {
                "requestId": "test-request-id",
                "identity": {"sourceIp": "127.0.0.1"},
            },
            "headers": {"User-Agent": "test-agent"},
        }

    def test_log_api_request(self, mock_logger, api_event):
        """Test API request logging"""
        request_logger = log_api_request(mock_logger, api_event, "POST", "/dogs")

        # Should bind request context
        mock_logger.bind.assert_called_once()
        # Should log the request
        request_logger.info.assert_called_once_with("API request received")

    def test_log_api_response_success(self, mock_logger):
        """Test API response logging for success"""
        log_api_response(mock_logger, 200, 1024, 150.5)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "API request completed" in call_args[0]

    def test_log_api_response_error(self, mock_logger):
        """Test API response logging for error"""
        log_api_response(mock_logger, 400, 256, 75.2)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "API request failed" in call_args[0]

    def test_log_api_response_minimal(self, mock_logger):
        """Test API response logging with minimal data"""
        log_api_response(mock_logger, 200)

        mock_logger.info.assert_called_once()


class TestDatabaseLogging:
    """Test cases for database logging"""

    @pytest.fixture
    def mock_logger(self):
        """Mock structured logger"""
        logger = MagicMock()
        return logger

    def test_log_database_operation_success(self, mock_logger):
        """Test successful database operation logging"""
        log_database_operation(
            mock_logger,
            operation="get_item",
            table_name="test-table",
            key={"id": "test-id"},
            duration_ms=25.5,
            success=True,
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Database operation completed" in call_args[0]

    def test_log_database_operation_failure(self, mock_logger):
        """Test failed database operation logging"""
        log_database_operation(
            mock_logger, operation="put_item", table_name="test-table", success=False
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Database operation failed" in call_args[0]

    def test_log_database_operation_minimal(self, mock_logger):
        """Test database operation logging with minimal data"""
        log_database_operation(mock_logger, operation="scan", table_name="test-table")

        mock_logger.info.assert_called_once()


class TestS3Logging:
    """Test cases for S3 logging"""

    @pytest.fixture
    def mock_logger(self):
        """Mock structured logger"""
        logger = MagicMock()
        return logger

    def test_log_s3_operation_success(self, mock_logger):
        """Test successful S3 operation logging"""
        log_s3_operation(
            mock_logger,
            operation="put_object",
            bucket="test-bucket",
            key="test-key",
            size_bytes=1024,
            duration_ms=100.0,
            success=True,
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "S3 operation completed" in call_args[0]

    def test_log_s3_operation_failure(self, mock_logger):
        """Test failed S3 operation logging"""
        log_s3_operation(
            mock_logger,
            operation="get_object",
            bucket="test-bucket",
            key="test-key",
            success=False,
        )

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "S3 operation failed" in call_args[0]

    def test_log_s3_operation_minimal(self, mock_logger):
        """Test S3 operation logging with minimal data"""
        log_s3_operation(
            mock_logger, operation="delete_object", bucket="test-bucket", key="test-key"
        )

        mock_logger.info.assert_called_once()


class TestLoggingMixin:
    """Test cases for LoggingMixin"""

    class TestClass(LoggingMixin):
        """Test class using LoggingMixin"""

        def __init__(self):
            super().__init__()

        def test_method(self, param1, param2=None):
            self.log_method_call("test_method", param1=param1, param2=param2)
            return "success"

    def test_logging_mixin_initialization(self):
        """Test LoggingMixin initialization"""
        test_obj = self.TestClass()

        assert hasattr(test_obj, "logger")
        assert isinstance(test_obj.logger, structlog.BoundLogger)

    def test_log_method_call(self):
        """Test method call logging"""
        test_obj = self.TestClass()

        with patch.object(test_obj.logger, "info") as mock_info:
            test_obj.test_method("value1", param2="value2")

            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Method called: test_method" in call_args[0]

    def test_log_error(self):
        """Test error logging"""
        test_obj = self.TestClass()

        test_error = ValueError("Test error")
        test_context = {"key": "value"}

        with patch.object(test_obj.logger, "error") as mock_error:
            test_obj.log_error(test_error, test_context)

            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Error occurred: Test error" in call_args[0]

    def test_log_error_no_context(self):
        """Test error logging without context"""
        test_obj = self.TestClass()

        test_error = RuntimeError("Runtime error")

        with patch.object(test_obj.logger, "error") as mock_error:
            test_obj.log_error(test_error)

            mock_error.assert_called_once()


class TestLoggingIntegration:
    """Integration tests for logging"""

    @patch.dict(
        os.environ,
        {"SERVICE_VERSION": "1.2.3", "ENVIRONMENT": "test", "AWS_REGION": "us-west-2"},
    )
    def test_logging_with_environment_variables(self):
        """Test logging setup with environment variables"""
        logger = setup_logging("test-service")

        assert isinstance(logger, structlog.BoundLogger)
        # Environment variables should be bound to logger context

    def test_logging_json_serialization(self):
        """Test that logged data can be JSON serialized"""
        logger = setup_logging(enable_json=True)

        # This should not raise any serialization errors
        logger.info("Test message", data={"key": "value", "number": 123})

    def test_logging_performance(self):
        """Test logging performance with large data"""
        logger = setup_logging()

        large_data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(100)]}

        # Should handle large data without issues
        logger.info("Large data test", data=large_data)
