"""
AWS X-Ray tracing utilities for the Pupper application
"""

import functools
import os
import time
from typing import Any, Callable, Dict, Optional

from aws_xray_sdk.core import patch_all, xray_recorder
from aws_xray_sdk.core.context import Context
from aws_xray_sdk.core.models.segment import Segment
from aws_xray_sdk.core.models.subsegment import Subsegment


def setup_xray_tracing() -> None:
    """
    Set up AWS X-Ray tracing for the application
    """
    # Only enable tracing in AWS Lambda environment
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        # Patch AWS SDK calls
        patch_all()

        # Configure X-Ray recorder
        xray_recorder.configure(
            context_missing="LOG_ERROR",
            plugins=("EC2Plugin", "ECSPlugin"),
            daemon_address=os.environ.get("_X_AMZN_TRACE_ID"),
        )


def trace_lambda_handler(func: Callable) -> Callable:
    """
    Decorator to add X-Ray tracing to Lambda handlers

    Args:
        func: Lambda handler function

    Returns:
        Wrapped function with tracing
    """

    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Any:
        # Set up tracing
        setup_xray_tracing()

        # Add metadata to the segment
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_metadata(
                "lambda",
                {
                    "function_name": context.function_name,
                    "function_version": context.function_version,
                    "memory_limit": context.memory_limit_in_mb,
                    "remaining_time": context.get_remaining_time_in_millis(),
                },
            )

            # Add HTTP request info if available
            if "httpMethod" in event:
                segment.put_http_meta("method", event["httpMethod"])
                segment.put_http_meta("url", event.get("path", ""))

                # Add request headers
                headers = event.get("headers", {})
                if headers:
                    segment.put_metadata(
                        "http_request",
                        {
                            "headers": headers,
                            "query_parameters": event.get("queryStringParameters"),
                            "path_parameters": event.get("pathParameters"),
                        },
                    )

        try:
            result = func(event, context)

            # Add response metadata
            if segment and isinstance(result, dict):
                status_code = result.get("statusCode", 200)
                segment.put_http_meta("status", status_code)

                if status_code >= 400:
                    segment.add_error_flag()

            return result

        except Exception as e:
            if segment:
                segment.add_exception(e)
            raise

    return wrapper


def trace_function(
    name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator to add X-Ray tracing to functions

    Args:
        name: Custom name for the subsegment
        metadata: Additional metadata to add to the trace

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            subsegment_name = name or f"{func.__module__}.{func.__name__}"

            with xray_recorder.in_subsegment(subsegment_name) as subsegment:
                if subsegment:
                    # Add function metadata
                    subsegment.put_metadata(
                        "function",
                        {
                            "name": func.__name__,
                            "module": func.__module__,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys()),
                        },
                    )

                    # Add custom metadata
                    if metadata:
                        subsegment.put_metadata("custom", metadata)

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)

                    if subsegment:
                        duration = (time.time() - start_time) * 1000
                        subsegment.put_metadata(
                            "performance", {"duration_ms": duration}
                        )

                    return result

                except Exception as e:
                    if subsegment:
                        subsegment.add_exception(e)
                    raise

        return wrapper

    return decorator


def trace_database_operation(
    operation: str, table_name: str, key: Optional[Dict[str, Any]] = None
):
    """
    Decorator to trace DynamoDB operations

    Args:
        operation: Database operation name
        table_name: DynamoDB table name
        key: Primary key of the item

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with xray_recorder.in_subsegment(f"dynamodb_{operation}") as subsegment:
                if subsegment:
                    subsegment.put_metadata(
                        "dynamodb",
                        {
                            "operation": operation,
                            "table_name": table_name,
                            "key": key,
                        },
                    )

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)

                    if subsegment:
                        duration = (time.time() - start_time) * 1000
                        subsegment.put_metadata(
                            "performance", {"duration_ms": duration}
                        )

                        # Add result metadata (without sensitive data)
                        if isinstance(result, dict):
                            item_count = 0
                            if "Items" in result:
                                item_count = len(result["Items"])
                            elif "Item" in result:
                                item_count = 1

                            subsegment.put_metadata(
                                "result",
                                {
                                    "item_count": item_count,
                                    "consumed_capacity": result.get("ConsumedCapacity"),
                                },
                            )

                    return result

                except Exception as e:
                    if subsegment:
                        subsegment.add_exception(e)
                    raise

        return wrapper

    return decorator


def trace_s3_operation(operation: str, bucket: str, key: str):
    """
    Decorator to trace S3 operations

    Args:
        operation: S3 operation name
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with xray_recorder.in_subsegment(f"s3_{operation}") as subsegment:
                if subsegment:
                    subsegment.put_metadata(
                        "s3",
                        {
                            "operation": operation,
                            "bucket": bucket,
                            "key": key,
                        },
                    )

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)

                    if subsegment:
                        duration = (time.time() - start_time) * 1000
                        subsegment.put_metadata(
                            "performance", {"duration_ms": duration}
                        )

                        # Add result metadata
                        if isinstance(result, dict) and "ContentLength" in result:
                            subsegment.put_metadata(
                                "result",
                                {
                                    "content_length": result["ContentLength"],
                                    "content_type": result.get("ContentType"),
                                },
                            )

                    return result

                except Exception as e:
                    if subsegment:
                        subsegment.add_exception(e)
                    raise

        return wrapper

    return decorator


class TracingMixin:
    """
    Mixin class to add tracing capabilities to other classes
    """

    def trace_method(self, method_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracing method calls

        Args:
            method_name: Name of the method being traced
            metadata: Additional metadata to include
        """
        return xray_recorder.in_subsegment(
            f"{self.__class__.__name__}.{method_name}", metadata=metadata or {}
        )

    def add_trace_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the current trace segment

        Args:
            key: Metadata key
            value: Metadata value
        """
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_metadata(key, value)

    def add_trace_annotation(self, key: str, value: str) -> None:
        """
        Add annotation to the current trace segment

        Args:
            key: Annotation key
            value: Annotation value
        """
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_annotation(key, value)
