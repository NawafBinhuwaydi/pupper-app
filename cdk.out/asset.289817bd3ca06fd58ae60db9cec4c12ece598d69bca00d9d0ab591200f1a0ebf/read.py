import json
import os
import time
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
import logging
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")

# AWS clients
dynamodb = boto3.resource("dynamodb")
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


def process_dog_record(dog: Dict[str, Any]) -> Dict[str, Any]:
    """Process a dog record for response"""
    processed_dog = dog.copy()
    
    # Decrypt dog name
    if "dog_name_encrypted" in processed_dog:
        processed_dog["dog_name"] = decrypt_dog_name(processed_dog["dog_name_encrypted"])
        del processed_dog["dog_name_encrypted"]
    
    return processed_dog


def get_all_dogs(filters: Dict[str, str]) -> Dict[str, Any]:
    """Get all dogs with optional filters"""
    try:
        # Start with scan operation
        scan_kwargs = {}
        filter_expressions = []
        expression_values = {}
        
        # Apply filters
        if filters.get("state"):
            filter_expressions.append("#state = :state")
            expression_values[":state"] = filters["state"].upper()
            scan_kwargs["ExpressionAttributeNames"] = {"#state": "state"}
        
        if filters.get("min_weight"):
            filter_expressions.append("dog_weight >= :min_weight")
            expression_values[":min_weight"] = int(filters["min_weight"])
        
        if filters.get("max_weight"):
            filter_expressions.append("dog_weight <= :max_weight")
            expression_values[":max_weight"] = int(filters["max_weight"])
        
        if filters.get("color"):
            filter_expressions.append("dog_color = :color")
            expression_values[":color"] = filters["color"].lower()
        
        if filters.get("min_age"):
            filter_expressions.append("dog_age_years >= :min_age")
            expression_values[":min_age"] = float(filters["min_age"])
        
        if filters.get("max_age"):
            filter_expressions.append("dog_age_years <= :max_age")
            expression_values[":max_age"] = float(filters["max_age"])
        
        # Add filter expression if we have filters
        if filter_expressions:
            scan_kwargs["FilterExpression"] = " AND ".join(filter_expressions)
            scan_kwargs["ExpressionAttributeValues"] = expression_values
        
        # Perform scan
        response = dogs_table.scan(**scan_kwargs)
        dogs = response.get("Items", [])
        
        # Process dogs (decrypt names, etc.)
        processed_dogs = [process_dog_record(dog) for dog in dogs]
        
        return {
            "dogs": processed_dogs,
            "count": len(processed_dogs),
            "filters_applied": filters
        }
        
    except Exception as e:
        logger.error(f"Error getting dogs: {str(e)}")
        raise


def get_single_dog(dog_id: str) -> Optional[Dict[str, Any]]:
    """Get a single dog by ID"""
    try:
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        
        if "Item" not in response:
            return None
        
        return process_dog_record(response["Item"])
        
    except Exception as e:
        logger.error(f"Error getting dog {dog_id}: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler for reading dogs"""
    start_time = time.time()
    
    try:
        logger.info("Processing read dog request")
        
        # Check if this is a single dog request
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if dog_id:
            # Get single dog
            logger.info(f"Getting single dog: {dog_id}")
            dog = get_single_dog(dog_id)
            
            if not dog:
                return ResponseFormatter.error_response("Dog not found", 404)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Single dog request completed in {duration_ms:.2f}ms")
            
            return ResponseFormatter.success_response({
                "message": "Dog retrieved successfully",
                **dog
            })
        
        else:
            # Get all dogs with filters
            query_parameters = event.get("queryStringParameters") or {}
            filters = {k: v for k, v in query_parameters.items() if v is not None}
            
            logger.info(f"Getting all dogs with filters: {filters}")
            result = get_all_dogs(filters)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"All dogs request completed in {duration_ms:.2f}ms, found {result['count']} dogs")
            
            return ResponseFormatter.success_response({
                "message": "Dogs retrieved successfully",
                **result
            })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return ResponseFormatter.error_response(str(e), 400)

    except Exception as e:
        logger.error(f"Unexpected error reading dogs: {str(e)}")
        return ResponseFormatter.error_response("Internal server error", 500)
