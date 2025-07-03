import json
import os
from datetime import datetime
from decimal import Decimal
import boto3

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
VOTES_TABLE = os.environ.get("VOTES_TABLE", "pupper-votes")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def lambda_handler(event, context):
    """Simple Lambda handler for updating dogs (mainly for voting)"""
    
    try:
        print("Processing update dog request")
        
        # Get dog ID from path
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if not dog_id:
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
                    "error": "Dog ID is required"
                })
            }
        
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
        print(f"Update request: {body}")
        
        # Check if this is a vote request
        if "vote_type" in body and "user_id" in body:
            vote_type = body["vote_type"]
            user_id = body["user_id"]
            
            if vote_type not in ["wag", "growl"]:
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
                        "error": "Vote type must be 'wag' or 'growl'"
                    })
                }
            
            print(f"Recording {vote_type} vote for dog {dog_id} by user {user_id}")
            
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
            
            vote_type_display = "wag" if vote_type == "wag" else "growl"
            
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                },
                "body": json.dumps({
                    "success": True,
                    "data": {
                        "message": f"Successfully recorded {vote_type_display} for dog",
                        "dog_id": dog_id,
                        "user_id": user_id,
                        "vote_type": vote_type,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            }
        
        else:
            # Regular update (for future use)
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
                    "error": "Only voting is currently supported"
                })
            }

    except Exception as e:
        print(f"Error updating dog: {str(e)}")
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
