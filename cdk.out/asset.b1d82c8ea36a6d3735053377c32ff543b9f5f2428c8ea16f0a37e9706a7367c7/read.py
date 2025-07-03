import json
import os
import boto3
import base64

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def lambda_handler(event, context):
    """Simple Lambda handler for reading dogs"""
    
    try:
        print("Processing read dog request")
        
        # Check if this is a single dog request
        path_parameters = event.get("pathParameters") or {}
        dog_id = path_parameters.get("dog_id")
        
        if dog_id:
            # Get single dog
            print(f"Getting single dog: {dog_id}")
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
            
            dog = response["Item"]
            
            # Decrypt dog name
            if "dog_name_encrypted" in dog:
                try:
                    dog["dog_name"] = base64.b64decode(dog["dog_name_encrypted"]).decode()
                    del dog["dog_name_encrypted"]
                except:
                    dog["dog_name"] = "Unknown"
            
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
                        "message": "Dog retrieved successfully",
                        **dog
                    }
                }, default=str)
            }
        
        else:
            # Get all dogs
            print("Getting all dogs")
            
            # Get query parameters for filtering
            query_parameters = event.get("queryStringParameters") or {}
            
            # Simple scan (no complex filtering for now)
            response = dogs_table.scan()
            dogs = response.get("Items", [])
            
            # Decrypt dog names
            for dog in dogs:
                if "dog_name_encrypted" in dog:
                    try:
                        dog["dog_name"] = base64.b64decode(dog["dog_name_encrypted"]).decode()
                        del dog["dog_name_encrypted"]
                    except:
                        dog["dog_name"] = "Unknown"
            
            print(f"Found {len(dogs)} dogs")
            
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
                        "message": "Dogs retrieved successfully",
                        "dogs": dogs,
                        "count": len(dogs),
                        "filters_applied": query_parameters
                    }
                }, default=str)
            }

    except Exception as e:
        print(f"Error reading dogs: {str(e)}")
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
