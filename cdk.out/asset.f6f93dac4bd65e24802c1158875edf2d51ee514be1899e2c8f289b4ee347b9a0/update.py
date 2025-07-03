import json
import os
from datetime import datetime
import boto3
import base64

# Environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
VOTES_TABLE = os.environ.get("VOTES_TABLE", "pupper-votes")

# AWS clients
dynamodb = boto3.resource("dynamodb")
dogs_table = dynamodb.Table(DOGS_TABLE)


def lambda_handler(event, context):
    """Lambda handler for updating dogs (voting and full updates)"""
    
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
            return handle_vote(dog_id, body)
        else:
            # Regular dog update
            return handle_dog_update(dog_id, body)

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
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
                "error": "Invalid JSON in request body"
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


def handle_vote(dog_id, body):
    """Handle voting on a dog"""
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


def handle_dog_update(dog_id, body):
    """Handle updating dog information"""
    
    # First, check if the dog exists
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
        
        existing_dog = response["Item"]
        
    except Exception as e:
        print(f"Error fetching dog: {str(e)}")
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
                "error": "Error fetching dog information"
            })
        }
    
    # Prepare update expression and values
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    # Updatable fields
    updatable_fields = {
        "shelter_name": "shelter_name",
        "city": "city", 
        "state": "state",
        "dog_name": "dog_name_encrypted",  # Note: we encrypt dog names
        "dog_species": "dog_species",
        "shelter_entry_date": "shelter_entry_date",
        "dog_description": "dog_description",
        "dog_birthday": "dog_birthday",
        "dog_weight": "dog_weight",
        "dog_color": "dog_color",
        "dog_photo_url": "dog_photo_url",
        "status": "status"
    }
    
    # Process each field in the request
    for field, db_field in updatable_fields.items():
        if field in body:
            value = body[field]
            
            # Special handling for different fields
            if field == "dog_name" and value:
                # Encrypt dog name (simple base64 for now)
                value = base64.b64encode(value.encode()).decode()
            elif field == "dog_species" and value:
                # Validate species (only Labrador Retrievers allowed)
                if "Labrador" not in value:
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
                            "error": "Only Labrador Retrievers are allowed"
                        })
                    }
            elif field == "dog_color" and value:
                value = value.lower()
            elif field == "state" and value:
                value = value.upper()
            elif field == "dog_weight" and value:
                try:
                    value = float(value)  # Use float instead of Decimal
                except:
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
                            "error": "Invalid weight value"
                        })
                    }
            
            # Add to update expression
            attr_name = f"#{db_field}"
            attr_value = f":{db_field}"
            
            update_expression_parts.append(f"{attr_name} = {attr_value}")
            expression_attribute_names[attr_name] = db_field
            expression_attribute_values[attr_value] = value
    
    # Always update the updated_at timestamp
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_names["#updated_at"] = "updated_at"
    expression_attribute_values[":updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Recalculate age if birthday was updated
    if "dog_birthday" in body:
        try:
            birthday_str = body["dog_birthday"]
            birthday = datetime.strptime(birthday_str, "%m/%d/%Y")
            age_years = (datetime.now() - birthday).days / 365.25
            
            update_expression_parts.append("#dog_age_years = :dog_age_years")
            expression_attribute_names["#dog_age_years"] = "dog_age_years"
            expression_attribute_values[":dog_age_years"] = f"{age_years:.1f}"
        except Exception as e:
            print(f"Error calculating age: {str(e)}")
            pass  # If age calculation fails, skip it
    
    # Update is_labrador flag if species was updated
    if "dog_species" in body:
        is_labrador = "Labrador" in body["dog_species"]
        update_expression_parts.append("#is_labrador = :is_labrador")
        expression_attribute_names["#is_labrador"] = "is_labrador"
        expression_attribute_values[":is_labrador"] = is_labrador
    
    if not update_expression_parts:
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
                "error": "No valid fields to update"
            })
        }
    
    # Perform the update
    try:
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        print(f"Updating dog {dog_id} with expression: {update_expression}")
        
        response = dogs_table.update_item(
            Key={"dog_id": dog_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW"
        )
        
        updated_dog = response["Attributes"]
        
        # Decrypt dog name for response
        if "dog_name_encrypted" in updated_dog:
            try:
                updated_dog["dog_name"] = base64.b64decode(updated_dog["dog_name_encrypted"]).decode()
            except:
                updated_dog["dog_name"] = "Unknown"
        
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
                    "message": "Dog updated successfully",
                    **{k: (str(v) if hasattr(v, '__str__') else v) for k, v in updated_dog.items()}
                }
            })  # Remove default=str to avoid serialization issues
        }
        
    except Exception as e:
        print(f"Error updating dog in database: {str(e)}")
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
                "error": "Failed to update dog in database"
            })
        }
