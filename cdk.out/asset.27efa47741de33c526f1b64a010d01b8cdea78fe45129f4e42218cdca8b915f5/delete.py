import json
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import logging
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "")

# AWS clients
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
dogs_table = dynamodb.Table(DOGS_TABLE)


class ResponseFormatter:
    @staticmethod
    def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
            },
            "body": json.dumps({
                "success": True,
                "data": data
            })
        }

    @staticmethod
    def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
            },
            "body": json.dumps({
                "success": False,
                "error": message
            })
        }


def decrypt_dog_name(encrypted_name: str) -> str:
    """Decrypt dog name from base64"""
    try:
        return base64.b64decode(encrypted_name).decode()
    except Exception:
        return "Unknown"


def get_dog(dog_id: str) -> Optional[Dict[str, Any]]:
    """Get a dog by ID"""
    try:
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        return response.get("Item")
    except Exception as e:
        logger.error(f"Error getting dog {dog_id}: {str(e)}")
        raise


def delete_dog_images(dog_record: Dict[str, Any]) -> None:
    """Delete associated images from S3"""
    if not IMAGES_BUCKET:
        logger.warning("No images bucket configured, skipping image deletion")
        return
    
    try:
        # List of possible image URLs to delete
        image_urls = [
            dog_record.get("dog_photo_url", ""),
            dog_record.get("dog_photo_400x400_url", ""),
            dog_record.get("dog_photo_50x50_url", "")
        ]
        
        for url in image_urls:
            if url and IMAGES_BUCKET in url:
                # Extract key from URL
                try:
                    key = url.split(f"{IMAGES_BUCKET}/")[-1]
                    s3.delete_object(Bucket=IMAGES_BUCKET, Key=key)
                    logger.info(f"Deleted image: {key}")
                except Exception as e:
                    logger.warning(f"Failed to delete image {url}: {str(e)}")
                    
    except Exception as e:
        logger.warning(f"Error deleting images: {str(e)}")
        # Don't fail the whole operation if image deletion fails


def delete_dog(dog_id: str) -> Dict[str, Any]:
    """Delete a dog record"""
    try:
        # Get the dog record first
        dog_record = get_dog(dog_id)
        if not dog_record:
            raise ValueError("Dog not found")
        
        # Delete associated images
        delete_dog_images(dog_record)
        
        # Delete the dog record
        dogs_table.delete_item(Key={"dog_id": dog_id})
        
        # Prepare response data
        response_data = {
            "dog_id": dog_id,
            "deleted_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Add dog name to response if available
        if "dog_name_encrypted" in dog_record:
            response_data["dog_name"] = decrypt_dog_name(dog_record["dog_name_encrypted"])
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error deleting dog {dog_id}: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler for deleting dogs"""
    start_time = time.time()
    
    try:
        logger.info("Processing delete dog request")
        
        # Get dog ID from path
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if not dog_id:
            return ResponseFormatter.error_response("Dog ID is required", 400)
        
        logger.info(f"Deleting dog: {dog_id}")
        
        # Delete the dog
        result = delete_dog(dog_id)
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Delete request completed in {duration_ms:.2f}ms")
        
        return ResponseFormatter.success_response({
            "message": "Dog successfully deleted from the system",
            **result
        })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return ResponseFormatter.error_response(str(e), 404)

    except Exception as e:
        logger.error(f"Unexpected error deleting dog: {str(e)}")
        return ResponseFormatter.error_response("Internal server error", 500)
