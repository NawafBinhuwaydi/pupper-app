import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

import boto3

# Add the backend directory to the path to import schemas
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from schemas import DogSchema, ResponseFormatter, EncryptionUtils
    from utils.logger import (
        get_lambda_logger,
        log_api_request,
        log_api_response,
        log_database_operation,
    )
    from utils.tracing import trace_lambda_handler, trace_database_operation
except ImportError:
    # Fallback for when modules are not available
    class DogSchema:
        @staticmethod
        def create_dog_record(**kwargs):
            return kwargs

        @staticmethod
        def validate_dog_data(data):
            return True, "Valid"

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

    class EncryptionUtils:
        @staticmethod
        def encrypt_dog_name(name):
            import base64

            return base64.b64encode(name.encode()).decode()

    # Fallback logging and tracing
    def get_lambda_logger(context):
        import logging

        return logging.getLogger()

    def log_api_request(logger, event, method, path):
        return logger

    def log_api_response(logger, status_code, response_size=None, duration_ms=None):
        pass

    def log_database_operation(
        logger, operation, table_name, key=None, duration_ms=None, success=True
    ):
        pass

    def trace_lambda_handler(func):
        return func

    def trace_database_operation(operation, table_name, key=None):
        def decorator(func):
            return func

        return decorator


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

# Get environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images")
SHELTERS_TABLE = os.environ.get("SHELTERS_TABLE", "pupper-shelters")


@trace_lambda_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to create a new dog entry
    """
    start_time = time.time()
    logger = get_lambda_logger(context)

    try:
        # Log API request
        method = event.get("httpMethod", "POST")
        path = event.get("path", "/dogs")
        request_logger = log_api_request(logger, event, method, path)

        # Parse the request body
        if "body" in event:
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]
        else:
            body = event

        request_logger.info("Validating dog data", dog_species=body.get("dog_species"))

        # Validate required data
        is_valid, validation_message = DogSchema.validate_dog_data(body)
        if not is_valid:
            request_logger.warning(
                "Dog data validation failed", error=validation_message
            )
            response = ResponseFormatter.error_response(validation_message, 400)
            log_api_response(
                request_logger, 400, duration_ms=(time.time() - start_time) * 1000
            )
            return response

        request_logger.info("Creating dog record")

        # Create dog record
        dog_record = DogSchema.create_dog_record(
            shelter_name=body["shelter_name"],
            city=body["city"],
            state=body["state"],
            dog_name=body["dog_name"],
            dog_species=body["dog_species"],
            shelter_entry_date=body["shelter_entry_date"],
            dog_description=body["dog_description"],
            dog_birthday=body["dog_birthday"],
            dog_weight=body["dog_weight"],
            dog_color=body["dog_color"],
            dog_photo_url=body.get("dog_photo_url"),
            shelter_id=body.get("shelter_id"),
        )

        # Encrypt dog name
        dog_record["dog_name_encrypted"] = EncryptionUtils.encrypt_dog_name(
            body["dog_name"]
        )

        # Remove plaintext dog name
        if "dog_name" in dog_record:
            del dog_record["dog_name"]

        request_logger.info("Saving dog to database", dog_id=dog_record["dog_id"])

        # Save to DynamoDB
        save_dog_to_db(dog_record, request_logger)

        # If image URL is provided, trigger image processing
        if body.get("dog_photo_url"):
            request_logger.info("Image URL provided, processing will be triggered")
            # TODO: Trigger image processing Lambda

        # Return success response (without encrypted name for security)
        response_data = dog_record.copy()
        if "dog_name_encrypted" in response_data:
            del response_data["dog_name_encrypted"]

        request_logger.info("Dog created successfully", dog_id=dog_record["dog_id"])

        response = ResponseFormatter.success_response(
            response_data, "Dog successfully added to the system"
        )

        duration_ms = (time.time() - start_time) * 1000
        log_api_response(
            request_logger, 200, len(json.dumps(response_data)), duration_ms
        )

        return response

    except json.JSONDecodeError as e:
        logger.error("JSON decode error", error=str(e))
        response = ResponseFormatter.error_response("Invalid JSON in request body", 400)
        log_api_response(logger, 400, duration_ms=(time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.error(
            "Unexpected error creating dog", error=str(e), error_type=type(e).__name__
        )
        response = ResponseFormatter.error_response(
            "Internal server error occurred while creating dog", 500
        )
        log_api_response(logger, 500, duration_ms=(time.time() - start_time) * 1000)
        return response


@trace_database_operation("put_item", DOGS_TABLE)
def save_dog_to_db(dog_record: Dict[str, Any], logger) -> None:
    """
    Save dog record to DynamoDB with tracing and logging
    """
    start_time = time.time()

    try:
        dogs_table = dynamodb.Table(DOGS_TABLE)
        dogs_table.put_item(Item=dog_record)

        duration_ms = (time.time() - start_time) * 1000
        log_database_operation(
            logger,
            "put_item",
            DOGS_TABLE,
            key={"dog_id": dog_record["dog_id"]},
            duration_ms=duration_ms,
            success=True,
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_database_operation(
            logger,
            "put_item",
            DOGS_TABLE,
            key={"dog_id": dog_record["dog_id"]},
            duration_ms=duration_ms,
            success=False,
        )
        raise e
