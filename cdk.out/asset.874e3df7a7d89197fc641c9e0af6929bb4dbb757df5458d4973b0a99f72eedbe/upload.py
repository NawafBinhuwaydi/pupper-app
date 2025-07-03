"""
Lambda function for handling image uploads
Supports large images (>10MB) and triggers automatic processing
"""

import base64
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

# Add the backend directory to the path to import utilities
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from utils.logger import (
        get_lambda_logger,
        log_api_request,
        log_api_response,
        log_s3_operation,
    )
    from utils.tracing import trace_lambda_handler, trace_s3_operation
    from schemas import ResponseFormatter
except ImportError:
    # Fallback for when modules are not available
    def get_lambda_logger(context):
        import logging

        return logging.getLogger()

    def log_api_request(logger, event, method, path):
        return logger

    def log_api_response(logger, status_code, response_size=None, duration_ms=None):
        pass

    def log_s3_operation(
        logger, operation, bucket, key, size_bytes=None, duration_ms=None, success=True
    ):
        pass

    def trace_lambda_handler(func):
        return func

    def trace_s3_operation(operation, bucket, key):
        def decorator(func):
            return func

        return decorator

    class ResponseFormatter:
        @staticmethod
        def success_response(data, message="Success"):
            return {
                "statusCode": 200,
                "body": json.dumps({"success": True, "data": data}),
            }

        @staticmethod
        def error_response(error, status_code=400):
            return {"statusCode": status_code, "body": json.dumps({"error": error})}


# Initialize AWS clients
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Get environment variables
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images")
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_TABLE = os.environ.get("IMAGES_TABLE", "pupper-images")
IMAGE_PROCESSING_FUNCTION = os.environ.get(
    "IMAGE_PROCESSING_FUNCTION", "pupper-image-processing"
)

# Supported image formats and max sizes
SUPPORTED_FORMATS = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB limit
MIN_IMAGE_SIZE = 1024  # 1KB minimum


@trace_lambda_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle image uploads and metadata retrieval
    """
    start_time = time.time()
    logger = get_lambda_logger(context)

    try:
        # Determine the operation based on HTTP method
        method = event.get("httpMethod", "POST")
        path = event.get("path", "/images")

        request_logger = log_api_request(logger, event, method, path)

        if method == "POST":
            return handle_image_upload(event, request_logger, start_time)
        elif method == "GET":
            return handle_image_metadata_retrieval(event, request_logger, start_time)
        else:
            response = ResponseFormatter.error_response("Method not allowed", 405)
            log_api_response(
                request_logger, 405, duration_ms=(time.time() - start_time) * 1000
            )
            return response

    except Exception as e:
        logger.error(
            "Unexpected error in image handler",
            error=str(e),
            error_type=type(e).__name__,
        )
        response = ResponseFormatter.error_response("Internal server error", 500)
        log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
        return response


def handle_image_upload(
    event: Dict[str, Any], logger, start_time: float
) -> Dict[str, Any]:
    """
    Handle image upload requests
    """
    try:
        # Parse request body
        if "body" in event:
            if event.get("isBase64Encoded", False):
                body_str = base64.b64decode(event["body"]).decode("utf-8")
            else:
                body_str = event["body"]

            if isinstance(body_str, str):
                body = json.loads(body_str)
            else:
                body = body_str
        else:
            body = event

        # Validate required fields
        required_fields = ["image_data", "content_type"]
        for field in required_fields:
            if field not in body:
                response = ResponseFormatter.error_response(
                    f"Missing required field: {field}", 400
                )
                log_api_response(
                    logger, 400, duration_ms=(time.time() - start_time) * 1000
                )
                return response

        # Validate content type
        content_type = body["content_type"].lower()
        if content_type not in SUPPORTED_FORMATS:
            response = ResponseFormatter.error_response(
                f"Unsupported image format. Supported formats: {', '.join(SUPPORTED_FORMATS)}",
                400,
            )
            log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
            return response

        # Decode image data
        try:
            image_data = base64.b64decode(body["image_data"])
        except Exception as e:
            logger.error("Failed to decode image data", error=str(e))
            response = ResponseFormatter.error_response(
                "Invalid base64 image data", 400
            )
            log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
            return response

        # Validate image size
        image_size = len(image_data)
        if image_size < MIN_IMAGE_SIZE:
            response = ResponseFormatter.error_response(
                "Image too small (minimum 1KB)", 400
            )
            log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
            return response

        if image_size > MAX_IMAGE_SIZE:
            response = ResponseFormatter.error_response(
                f"Image too large (maximum {MAX_IMAGE_SIZE // (1024*1024)}MB)", 400
            )
            log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
            return response

        logger.info(
            "Image validation passed",
            content_type=content_type,
            size_bytes=image_size,
            size_mb=round(image_size / (1024 * 1024), 2),
        )

        # Generate unique image ID
        image_id = str(uuid.uuid4())

        # Determine file extension
        extension_map = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        file_extension = extension_map.get(content_type, "jpg")

        # Upload original image to S3
        original_key = f"uploads/{image_id}/original.{file_extension}"
        upload_result = upload_image_to_s3(
            image_data, original_key, content_type, logger
        )

        if not upload_result["success"]:
            response = ResponseFormatter.error_response(upload_result["error"], 500)
            log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
            return response

        # Create image metadata record
        image_metadata = create_image_metadata(
            image_id=image_id,
            original_key=original_key,
            content_type=content_type,
            size_bytes=image_size,
            dog_id=body.get("dog_id"),
            description=body.get("description", ""),
            tags=body.get("tags", []),
        )

        # Save metadata to DynamoDB
        save_result = save_image_metadata(image_metadata, logger)
        if not save_result["success"]:
            # Clean up uploaded image
            cleanup_s3_object(original_key, logger)
            response = ResponseFormatter.error_response(save_result["error"], 500)
            log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
            return response

        # Trigger image processing asynchronously
        trigger_result = trigger_image_processing(image_id, original_key, logger)
        if not trigger_result["success"]:
            logger.warning(
                "Failed to trigger image processing", error=trigger_result["error"]
            )

        # Prepare response data
        response_data = {
            "image_id": image_id,
            "original_url": f"https://{IMAGES_BUCKET}.s3.amazonaws.com/{original_key}",
            "status": "uploaded",
            "processing_status": "queued" if trigger_result["success"] else "failed",
            "size_bytes": image_size,
            "content_type": content_type,
            "created_at": image_metadata["created_at"],
        }

        logger.info(
            "Image upload completed successfully",
            image_id=image_id,
            size_bytes=image_size,
            processing_triggered=trigger_result["success"],
        )

        response = ResponseFormatter.success_response(
            response_data, "Image uploaded successfully"
        )

        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, 200, len(json.dumps(response_data)), duration_ms)

        return response

    except json.JSONDecodeError as e:
        logger.error("JSON decode error", error=str(e))
        response = ResponseFormatter.error_response("Invalid JSON in request body", 400)
        log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.error(
            "Error handling image upload", error=str(e), error_type=type(e).__name__
        )
        response = ResponseFormatter.error_response(
            "Internal server error during upload", 500
        )
        log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
        return response


def handle_image_metadata_retrieval(
    event: Dict[str, Any], logger, start_time: float
) -> Dict[str, Any]:
    """
    Handle image metadata retrieval requests
    """
    try:
        # Get image ID from path parameters
        path_parameters = event.get("pathParameters", {})
        image_id = path_parameters.get("image_id")

        if not image_id:
            response = ResponseFormatter.error_response("Image ID is required", 400)
            log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
            return response

        # Retrieve image metadata from DynamoDB
        metadata_result = get_image_metadata(image_id, logger)

        if not metadata_result["success"]:
            status_code = (
                404 if "not found" in metadata_result["error"].lower() else 500
            )
            response = ResponseFormatter.error_response(
                metadata_result["error"], status_code
            )
            log_api_response(
                logger, status_code, duration_ms=(time.time() - start_time) * 1000
            )
            return response

        image_metadata = metadata_result["data"]

        # Prepare response data
        response_data = {
            "image_id": image_metadata["image_id"],
            "original_url": image_metadata.get("original_url"),
            "resized_urls": image_metadata.get("resized_urls", {}),
            "status": image_metadata.get("status", "unknown"),
            "processing_status": image_metadata.get("processing_status", "unknown"),
            "content_type": image_metadata.get("content_type"),
            "size_bytes": image_metadata.get("size_bytes"),
            "dimensions": image_metadata.get("dimensions", {}),
            "dog_id": image_metadata.get("dog_id"),
            "description": image_metadata.get("description", ""),
            "tags": image_metadata.get("tags", []),
            "created_at": image_metadata.get("created_at"),
            "updated_at": image_metadata.get("updated_at"),
        }

        logger.info("Image metadata retrieved successfully", image_id=image_id)

        response = ResponseFormatter.success_response(
            response_data, "Image metadata retrieved successfully"
        )

        duration_ms = (time.time() - start_time) * 1000
        log_api_response(logger, 200, len(json.dumps(response_data)), duration_ms)

        return response

    except Exception as e:
        logger.error(
            "Error retrieving image metadata", error=str(e), error_type=type(e).__name__
        )
        response = ResponseFormatter.error_response(
            "Internal server error during retrieval", 500
        )
        log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
        return response


@trace_s3_operation("put_object", IMAGES_BUCKET, "")
def upload_image_to_s3(
    image_data: bytes, key: str, content_type: str, logger
) -> Dict[str, Any]:
    """
    Upload image data to S3
    """
    start_time = time.time()

    try:
        s3_client.put_object(
            Bucket=IMAGES_BUCKET,
            Key=key,
            Body=image_data,
            ContentType=content_type,
            Metadata={
                "uploaded_at": datetime.utcnow().isoformat(),
                "original_size": str(len(image_data)),
            },
        )

        duration_ms = (time.time() - start_time) * 1000
        log_s3_operation(
            logger,
            "put_object",
            IMAGES_BUCKET,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=True,
        )

        return {"success": True, "key": key}

    except ClientError as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"S3 upload failed: {str(e)}"
        logger.error("S3 upload error", error=error_msg, key=key)
        log_s3_operation(
            logger,
            "put_object",
            IMAGES_BUCKET,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=False,
        )

        return {"success": False, "error": error_msg}

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Unexpected error during S3 upload: {str(e)}"
        logger.error("Unexpected S3 error", error=error_msg, key=key)
        log_s3_operation(
            logger,
            "put_object",
            IMAGES_BUCKET,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=False,
        )

        return {"success": False, "error": error_msg}


def create_image_metadata(
    image_id: str,
    original_key: str,
    content_type: str,
    size_bytes: int,
    dog_id: Optional[str] = None,
    description: str = "",
    tags: list = None,
) -> Dict[str, Any]:
    """
    Create image metadata record
    """
    current_time = datetime.utcnow().isoformat()

    return {
        "image_id": image_id,
        "original_key": original_key,
        "original_url": f"https://{IMAGES_BUCKET}.s3.amazonaws.com/{original_key}",
        "content_type": content_type,
        "size_bytes": size_bytes,
        "status": "uploaded",
        "processing_status": "pending",
        "dog_id": dog_id,
        "description": description,
        "tags": tags or [],
        "resized_urls": {},
        "dimensions": {},
        "created_at": current_time,
        "updated_at": current_time,
    }


def save_image_metadata(metadata: Dict[str, Any], logger) -> Dict[str, Any]:
    """
    Save image metadata to DynamoDB
    """
    start_time = time.time()

    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        images_table.put_item(Item=metadata)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Image metadata saved successfully",
            image_id=metadata["image_id"],
            duration_ms=duration_ms,
        )

        return {"success": True}

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to save image metadata: {str(e)}"
        logger.error(
            "DynamoDB save error",
            error=error_msg,
            image_id=metadata["image_id"],
            duration_ms=duration_ms,
        )

        return {"success": False, "error": error_msg}


def get_image_metadata(image_id: str, logger) -> Dict[str, Any]:
    """
    Retrieve image metadata from DynamoDB
    """
    start_time = time.time()

    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        response = images_table.get_item(Key={"image_id": image_id})

        duration_ms = (time.time() - start_time) * 1000

        if "Item" not in response:
            logger.warning(
                "Image metadata not found", image_id=image_id, duration_ms=duration_ms
            )
            return {"success": False, "error": "Image not found"}

        logger.info(
            "Image metadata retrieved successfully",
            image_id=image_id,
            duration_ms=duration_ms,
        )

        return {"success": True, "data": response["Item"]}

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to retrieve image metadata: {str(e)}"
        logger.error(
            "DynamoDB get error",
            error=error_msg,
            image_id=image_id,
            duration_ms=duration_ms,
        )

        return {"success": False, "error": error_msg}


def trigger_image_processing(
    image_id: str, original_key: str, logger
) -> Dict[str, Any]:
    """
    Trigger asynchronous image processing
    """
    try:
        payload = {
            "image_id": image_id,
            "original_key": original_key,
            "trigger_source": "upload_api",
        }

        lambda_client.invoke(
            FunctionName=IMAGE_PROCESSING_FUNCTION,
            InvocationType="Event",  # Asynchronous invocation
            Payload=json.dumps(payload),
        )

        logger.info(
            "Image processing triggered successfully",
            image_id=image_id,
            function=IMAGE_PROCESSING_FUNCTION,
        )

        return {"success": True}

    except Exception as e:
        error_msg = f"Failed to trigger image processing: {str(e)}"
        logger.error(
            "Lambda invoke error",
            error=error_msg,
            image_id=image_id,
            function=IMAGE_PROCESSING_FUNCTION,
        )

        return {"success": False, "error": error_msg}


def cleanup_s3_object(key: str, logger) -> None:
    """
    Clean up S3 object in case of error
    """
    try:
        s3_client.delete_object(Bucket=IMAGES_BUCKET, Key=key)
        logger.info("S3 object cleaned up", key=key)
    except Exception as e:
        logger.error("Failed to cleanup S3 object", error=str(e), key=key)
