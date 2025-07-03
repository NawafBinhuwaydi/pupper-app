import json
import os
import uuid
from datetime import datetime
from decimal import Decimal
import boto3

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def lambda_handler(event, context):
    """Simple Lambda handler for creating dogs"""
    
    try:
        print("Processing create dog request")
        
        # Parse request body
        if not event.get("body"):
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "Request body is required"
                })
            }
        
        body = json.loads(event["body"])
        print(f"Request body: {body}")
        
        # Validate required fields
        required_fields = ["shelter_name", "city", "state", "dog_name", "dog_species", "dog_weight"]
        for field in required_fields:
            if not body.get(field):
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                        "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                    },
                    "body": json.dumps({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    })
                }
        
        # Create dog record
        dog_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + "Z"
        
        # Calculate age (simple version)
        try:
            birthday = datetime.strptime(body.get("dog_birthday", "1/1/2020"), "%m/%d/%Y")
            age_years = (datetime.now() - birthday).days / 365.25
            age_decimal = Decimal(str(round(age_years, 1)))
        except:
            age_decimal = Decimal('1.0')
        
        # Encrypt dog name (simple base64)
        import base64
        dog_name_encrypted = base64.b64encode(body["dog_name"].encode()).decode()
        
        dog_record = {
            "dog_id": dog_id,
            "shelter_name": body["shelter_name"],
            "city": body["city"],
            "state": body["state"].upper(),
            "dog_name_encrypted": dog_name_encrypted,
            "dog_species": body["dog_species"],
            "shelter_entry_date": body.get("shelter_entry_date", "1/1/2024"),
            "dog_description": body.get("dog_description", ""),
            "dog_birthday": body.get("dog_birthday", "1/1/2020"),
            "dog_weight": int(body["dog_weight"]),
            "dog_color": body.get("dog_color", "brown").lower(),
            "dog_age_years": age_decimal,
            "dog_photo_url": body.get("dog_photo_url", ""),
            "dog_photo_400x400_url": "",
            "dog_photo_50x50_url": "",
            "shelter_id": body.get("shelter_id", ""),
            "created_at": current_time,
            "updated_at": current_time,
            "is_labrador": "labrador" in body["dog_species"].lower(),
            "wag_count": 0,
            "growl_count": 0,
            "status": "available"
        }
        
        print(f"Saving dog record: {dog_record}")
        
        # Save to DynamoDB
        dogs_table.put_item(Item=dog_record)
        
        print("Dog saved successfully")
        
        # Prepare response
        response_data = dog_record.copy()
        response_data["dog_name"] = body["dog_name"]  # Return unencrypted name
        del response_data["dog_name_encrypted"]
        
        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
            },
            "body": json.dumps({
                "success": True,
                "data": {
                    "message": "Dog successfully added to the system",
                    **response_data
                }
            }, default=str)  # Handle Decimal serialization
        }

    except Exception as e:
        print(f"Error creating dog: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
            },
            "body": json.dumps({
                "success": False,
                "error": "Internal server error"
            })
        }
