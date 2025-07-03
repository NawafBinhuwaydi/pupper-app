"""
Structured logging utilities for the Pupper application
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(
    service_name: str = "pupper-api", log_level: str = "INFO", enable_json: bool = True
) -> structlog.BoundLogger:
    """
    Set up structured logging for the application

    Args:
        service_name: Name of the service for logging context
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_json: Whether to use JSON formatting

    Returns:
        Configured structlog logger
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create logger with service context
    logger = structlog.get_logger(service_name)

    # Add common context
    logger = logger.bind(
        service=service_name,
        version=os.environ.get("SERVICE_VERSION", "1.0.0"),
        environment=os.environ.get("ENVIRONMENT", "development"),
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
    )

    return logger


def get_lambda_logger(context: Any) -> structlog.BoundLogger:
    """
    Get a logger configured for AWS Lambda with request context

    Args:
        context: AWS Lambda context object

    Returns:
        Logger with Lambda context bound
    """
    logger = setup_logging(
        service_name="pupper-lambda",
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        enable_json=True,
    )

    # Add Lambda context
    logger = logger.bind(
        request_id=context.aws_request_id,
        function_name=context.function_name,
        function_version=context.function_version,
        memory_limit=context.memory_limit_in_mb,
        remaining_time=context.get_remaining_time_in_millis(),
    )

    return logger


def log_api_request(
    logger: structlog.BoundLogger, event: Dict[str, Any], method: str, path: str
) -> structlog.BoundLogger:
    """
    Log API request details

    Args:
        logger: Structured logger instance
        event: API Gateway event
        method: HTTP method
        path: Request path

    Returns:
        Logger with request context bound
    """
    request_logger = logger.bind(
        http_method=method,
        http_path=path,
        source_ip=event.get("requestContext", {}).get("identity", {}).get("sourceIp"),
        user_agent=event.get("headers", {}).get("User-Agent"),
        request_id=event.get("requestContext", {}).get("requestId"),
    )

    request_logger.info("API request received")
    return request_logger


def log_api_response(
    logger: structlog.BoundLogger,
    status_code: int,
    response_size: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """
    Log API response details

    Args:
        logger: Structured logger instance
        status_code: HTTP status code
        response_size: Size of response body in bytes
        duration_ms: Request duration in milliseconds
    """
    log_data = {
        "http_status": status_code,
        "response_size_bytes": response_size,
        "duration_ms": duration_ms,
    }

    # Remove None values
    log_data = {k: v for k, v in log_data.items() if v is not None}

    if status_code >= 400:
        logger.error("API request failed", **log_data)
    else:
        logger.info("API request completed", **log_data)


def log_database_operation(
    logger: structlog.BoundLogger,
    operation: str,
    table_name: str,
    key: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
) -> None:
    """
    Log database operation details

    Args:
        logger: Structured logger instance
        operation: Database operation (get, put, update, delete, scan, query)
        table_name: DynamoDB table name
        key: Primary key of the item (if applicable)
        duration_ms: Operation duration in milliseconds
        success: Whether the operation was successful
    """
    log_data = {
        "db_operation": operation,
        "db_table": table_name,
        "db_key": key,
        "duration_ms": duration_ms,
        "success": success,
    }

    # Remove None values
    log_data = {k: v for k, v in log_data.items() if v is not None}

    if success:
        logger.info("Database operation completed", **log_data)
    else:
        logger.error("Database operation failed", **log_data)


def log_s3_operation(
    logger: structlog.BoundLogger,
    operation: str,
    bucket: str,
    key: str,
    size_bytes: Optional[int] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
) -> None:
    """
    Log S3 operation details

    Args:
        logger: Structured logger instance
        operation: S3 operation (get, put, delete, list)
        bucket: S3 bucket name
        key: S3 object key
        size_bytes: Object size in bytes
        duration_ms: Operation duration in milliseconds
        success: Whether the operation was successful
    """
    log_data = {
        "s3_operation": operation,
        "s3_bucket": bucket,
        "s3_key": key,
        "object_size_bytes": size_bytes,
        "duration_ms": duration_ms,
        "success": success,
    }

    # Remove None values
    log_data = {k: v for k, v in log_data.items() if v is not None}

    if success:
        logger.info("S3 operation completed", **log_data)
    else:
        logger.error("S3 operation failed", **log_data)


class LoggingMixin:
    """
    Mixin class to add structured logging to other classes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = setup_logging(
            service_name=self.__class__.__name__.lower(),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )

    def log_method_call(self, method_name: str, **kwargs) -> None:
        """Log method call with parameters"""
        self.logger.info(
            f"Method called: {method_name}", method=method_name, parameters=kwargs
        )

    def log_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error with context"""
        self.logger.error(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
        )
