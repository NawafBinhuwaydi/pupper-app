import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "")
SHELTERS_TABLE = os.environ.get("SHELTERS_TABLE", "pupper-shelters")
IMAGES_TABLE = os.environ.get("IMAGES_TABLE", "pupper-images")

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


def calculate_age_years(birthday_str: str) -> Decimal:
    """Calculate age in years from birthday string (MM/DD/YYYY)"""
    try:
        birthday = datetime.strptime(birthday_str, "%m/%d/%Y")
        today = datetime.now()
        age_years = (today - birthday).days / 365.25
        return Decimal(str(round(age_years, 1)))
    except ValueError:
        return Decimal('0.0')


def encrypt_dog_name(name: str) -> str:
    """Simple base64 encoding for dog name (replace with proper encryption in production)"""
    import base64
    return base64.b64encode(name.encode()).decode()


def create_dog_record(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a dog record with all required fields"""
    dog_id = str(uuid.uuid4())
    current_time = datetime.utcnow().isoformat() + "Z"
    
    # Calculate age from birthday
    age_years = calculate_age_years(body.get("dog_birthday", "1/1/2020"))
    
    # Determine if it's a Labrador
    species = body.get("dog_species", "").lower()
    is_labrador = "labrador" in species
    
    dog_record = {
        "dog_id": dog_id,
        "shelter_name": body.get("shelter_name", ""),
        "city": body.get("city", ""),
        "state": body.get("state", "").upper(),
        "dog_name_encrypted": encrypt_dog_name(body.get("dog_name", "")),
        "dog_species": body.get("dog_species", ""),
        "shelter_entry_date": body.get("shelter_entry_date", ""),
        "dog_description": body.get("dog_description", ""),
        "dog_birthday": body.get("dog_birthday", ""),
        "dog_weight": int(body.get("dog_weight", 0)),
        "dog_color": body.get("dog_color", "").lower(),
        "dog_age_years": age_years,
        "dog_photo_url": body.get("dog_photo_url", ""),
        "dog_photo_400x400_url": "",
        "dog_photo_50x50_url": "",
        "shelter_id": body.get("shelter_id", ""),
        "created_at": current_time,
        "updated_at": current_time,
        "is_labrador": is_labrador,
        "wag_count": 0,
        "growl_count": 0,
        "status": "available"
    }
    
    return dog_record


def validate_dog_data(body: Dict[str, Any]) -> Optional[str]:
    """Validate required dog data"""
    required_fields = [
        "shelter_name", "city", "state", "dog_name", "dog_species",
        "shelter_entry_date", "dog_birthday", "dog_weight", "dog_color"
    ]
    
    for field in required_fields:
        if not body.get(field):
            return f"Missing required field: {field}"
    
    # Validate species (only Labradors allowed)
    species = body.get("dog_species", "").lower()
    if "labrador" not in species:
        return "Only Labrador Retrievers are allowed"
    
    # Validate weight
    try:
        weight = int(body.get("dog_weight", 0))
        if weight <= 0:
            return "Weight must be a positive number"
    except (ValueError, TypeError):
        return "Weight must be a valid number"
    
    return None


def save_dog_to_db(dog_record: Dict[str, Any]) -> None:
    """Save dog record to DynamoDB"""
    try:
        dogs_table.put_item(Item=dog_record)
        logger.info(f"Dog saved to database: {dog_record['dog_id']}")
    except ClientError as e:
        logger.error(f"Failed to save dog to database: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler for creating dogs"""
    start_time = time.time()
    
    try:
        logger.info("Processing create dog request")
        
        # Parse request body
        if not event.get("body"):
            return ResponseFormatter.error_response("Request body is required", 400)
        
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return ResponseFormatter.error_response("Invalid JSON in request body", 400)
        
        logger.info(f"Validating dog data for species: {body.get('dog_species')}")
        
        # Validate input data
        validation_error = validate_dog_data(body)
        if validation_error:
            logger.warning(f"Validation failed: {validation_error}")
            return ResponseFormatter.error_response(validation_error, 400)
        
        logger.info("Creating dog record")
        
        # Create dog record
        dog_record = create_dog_record(body)
        
        logger.info(f"Saving dog to database: {dog_record['dog_id']}")
        
        # Save to database
        save_dog_to_db(dog_record)
        
        # Prepare response (decrypt name for response)
        import base64
        response_data = dog_record.copy()
        response_data["dog_name"] = base64.b64decode(dog_record["dog_name_encrypted"]).decode()
        del response_data["dog_name_encrypted"]
        
        logger.info(f"Dog created successfully: {dog_record['dog_id']}")
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Request completed in {duration_ms:.2f}ms")
        
        return ResponseFormatter.success_response({
            "message": "Dog successfully added to the system",
            **response_data
        }, 201)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return ResponseFormatter.error_response("Invalid JSON in request body", 400)

    except Exception as e:
        logger.error(f"Unexpected error creating dog: {str(e)}")
        return ResponseFormatter.error_response("Internal server error", 500)
