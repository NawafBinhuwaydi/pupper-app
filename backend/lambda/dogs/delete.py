import json
import os
from datetime import datetime
import boto3
import base64

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def lambda_handler(event, context):
    """Simple Lambda handler for deleting dogs"""
    
    try:
        print("Processing delete dog request")
        
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
        
        print(f"Deleting dog: {dog_id}")
        
        # Get the dog record first to return info
        try:
            response = dogs_table.get_item(Key={"dog_id": dog_id})
            
            if "Item" not in response:
                return {
                    "statusCode": 404,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
                        "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE"
                    },
                    "body": json.dumps({
                        "success": False,
                        "error": "Dog not found"
                    })
                }
            
            dog_record = response["Item"]
            
            # Get dog name for response
            dog_name = "Unknown"
            if "dog_name_encrypted" in dog_record:
                try:
                    dog_name = base64.b64decode(dog_record["dog_name_encrypted"]).decode()
                except:
                    dog_name = "Unknown"
            
        except Exception as e:
            print(f"Error getting dog record: {str(e)}")
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
                    "error": "Error retrieving dog record"
                })
            }
        
        # Delete the dog record
        dogs_table.delete_item(Key={"dog_id": dog_id})
        
        print(f"Dog {dog_id} deleted successfully")
        
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
                    "message": "Dog successfully deleted from the system",
                    "dog_id": dog_id,
                    "dog_name": dog_name,
                    "deleted_at": datetime.utcnow().isoformat() + "Z"
                }
            })
        }

    except Exception as e:
        print(f"Error deleting dog: {str(e)}")
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
