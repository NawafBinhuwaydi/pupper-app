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
VOTES_TABLE = os.environ.get("VOTES_TABLE", "pupper-votes")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)
votes_table = dynamodb.Table(VOTES_TABLE)


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


def encrypt_dog_name(name: str) -> str:
    """Simple base64 encoding for dog name"""
    return base64.b64encode(name.encode()).decode()


def decrypt_dog_name(encrypted_name: str) -> str:
    """Decrypt dog name from base64"""
    try:
        return base64.b64decode(encrypted_name).decode()
    except Exception:
        return "Unknown"


def calculate_age_years(birthday_str: str) -> float:
    """Calculate age in years from birthday string (MM/DD/YYYY)"""
    try:
        birthday = datetime.strptime(birthday_str, "%m/%d/%Y")
        today = datetime.now()
        age_years = (today - birthday).days / 365.25
        return round(age_years, 1)
    except ValueError:
        return 0.0


def get_dog(dog_id: str) -> Optional[Dict[str, Any]]:
    """Get a dog by ID"""
    try:
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        return response.get("Item")
    except Exception as e:
        logger.error(f"Error getting dog {dog_id}: {str(e)}")
        raise


def update_dog(dog_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a dog record"""
    try:
        # Get current dog record
        current_dog = get_dog(dog_id)
        if not current_dog:
            raise ValueError("Dog not found")
        
        # Prepare update expression
        update_expression_parts = []
        expression_values = {}
        expression_names = {}
        
        # Handle special fields
        if "dog_name" in updates:
            updates["dog_name_encrypted"] = encrypt_dog_name(updates["dog_name"])
            del updates["dog_name"]
        
        if "dog_birthday" in updates:
            updates["dog_age_years"] = calculate_age_years(updates["dog_birthday"])
        
        if "dog_species" in updates:
            species = updates["dog_species"].lower()
            updates["is_labrador"] = "labrador" in species
        
        if "dog_color" in updates:
            updates["dog_color"] = updates["dog_color"].lower()
        
        if "state" in updates:
            updates["state"] = updates["state"].upper()
        
        # Always update the updated_at timestamp
        updates["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Build update expression
        for key, value in updates.items():
            if key in ["dog_id"]:  # Skip immutable fields
                continue
                
            update_expression_parts.append(f"#{key} = :{key}")
            expression_names[f"#{key}"] = key
            expression_values[f":{key}"] = value
        
        if not update_expression_parts:
            raise ValueError("No valid fields to update")
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        # Perform update
        response = dogs_table.update_item(
            Key={"dog_id": dog_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW"
        )
        
        updated_dog = response["Attributes"]
        
        # Decrypt name for response
        if "dog_name_encrypted" in updated_dog:
            updated_dog["dog_name"] = decrypt_dog_name(updated_dog["dog_name_encrypted"])
            del updated_dog["dog_name_encrypted"]
        
        return updated_dog
        
    except Exception as e:
        logger.error(f"Error updating dog {dog_id}: {str(e)}")
        raise


def record_vote(dog_id: str, user_id: str, vote_type: str) -> Dict[str, Any]:
    """Record a vote for a dog"""
    try:
        # Validate vote type
        if vote_type not in ["wag", "growl"]:
            raise ValueError("Vote type must be 'wag' or 'growl'")
        
        # Check if user already voted for this dog
        try:
            existing_vote = votes_table.get_item(
                Key={"user_id": user_id, "dog_id": dog_id}
            )
            if "Item" in existing_vote:
                # Update existing vote
                current_time = datetime.utcnow().isoformat() + "Z"
                votes_table.update_item(
                    Key={"user_id": user_id, "dog_id": dog_id},
                    UpdateExpression="SET vote_type = :vote_type, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":vote_type": vote_type,
                        ":updated_at": current_time
                    }
                )
            else:
                # Create new vote
                current_time = datetime.utcnow().isoformat() + "Z"
                votes_table.put_item(Item={
                    "user_id": user_id,
                    "dog_id": dog_id,
                    "vote_type": vote_type,
                    "created_at": current_time,
                    "updated_at": current_time
                })
        except Exception as e:
            logger.error(f"Error recording vote: {str(e)}")
            # Continue even if vote recording fails
        
        # Update dog's vote counts
        if vote_type == "wag":
            dogs_table.update_item(
                Key={"dog_id": dog_id},
                UpdateExpression="ADD wag_count :inc",
                ExpressionAttributeValues={":inc": 1}
            )
        else:
            dogs_table.update_item(
                Key={"dog_id": dog_id},
                UpdateExpression="ADD growl_count :inc",
                ExpressionAttributeValues={":inc": 1}
            )
        
        return {
            "dog_id": dog_id,
            "user_id": user_id,
            "vote_type": vote_type,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error recording vote: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler for updating dogs and recording votes"""
    start_time = time.time()
    
    try:
        logger.info("Processing update dog request")
        
        # Get dog ID from path
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if not dog_id:
            return ResponseFormatter.error_response("Dog ID is required", 400)
        
        # Parse request body
        if not event.get("body"):
            return ResponseFormatter.error_response("Request body is required", 400)
        
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return ResponseFormatter.error_response("Invalid JSON in request body", 400)
        
        # Check if this is a vote request
        if "vote_type" in body and "user_id" in body:
            logger.info(f"Recording vote for dog {dog_id}")
            
            vote_result = record_vote(dog_id, body["user_id"], body["vote_type"])
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Vote request completed in {duration_ms:.2f}ms")
            
            vote_type_display = "wag" if body["vote_type"] == "wag" else "growl"
            return ResponseFormatter.success_response({
                "message": f"Successfully recorded {vote_type_display} for dog",
                **vote_result
            })
        
        else:
            # Regular update request
            logger.info(f"Updating dog {dog_id}")
            
            updated_dog = update_dog(dog_id, body)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"Update request completed in {duration_ms:.2f}ms")
            
            return ResponseFormatter.success_response({
                "message": "Dog updated successfully",
                **updated_dog
            })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return ResponseFormatter.error_response(str(e), 400)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return ResponseFormatter.error_response("Invalid JSON in request body", 400)

    except Exception as e:
        logger.error(f"Unexpected error updating dog: {str(e)}")
        return ResponseFormatter.error_response("Internal server error", 500)
