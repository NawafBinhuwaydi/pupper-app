import json
import boto3
import os
import sys
from datetime import datetime
from boto3.dynamodb.conditions import Key

# Add the backend directory to the path to import schemas
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from schemas import VoteSchema, ResponseFormatter, EncryptionUtils
except ImportError:
    # Fallback for when schemas module is not available
    class VoteSchema:
        @staticmethod
        def create_vote_record(user_id, dog_id, vote_type):
            return {"user_id": user_id, "dog_id": dog_id, "vote_type": vote_type}

        @staticmethod
        def validate_vote_type(vote_type):
            return vote_type.lower() in ["wag", "growl"]

    class ResponseFormatter:
        @staticmethod
        def success_response(data, message="Success"):
            return {
                "statusCode": 200,
                "body": json.dumps({"success": True, "data": data}, default=str),
            }

        @staticmethod
        def error_response(error, status_code=400):
            return {"statusCode": status_code, "body": json.dumps({"error": error})}

    class EncryptionUtils:
        @staticmethod
        def encrypt_dog_name(name):
            import base64

            return base64.b64encode(name.encode()).decode()


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
VOTES_TABLE = os.environ.get("VOTES_TABLE", "pupper-votes")


def lambda_handler(event, context):
    """
    Lambda function to update dog entries or handle voting
    """
    try:
        # Parse the request
        path_parameters = event.get("pathParameters", {})
        dog_id = path_parameters.get("dog_id")

        if not dog_id:
            return ResponseFormatter.error_response("Dog ID is required", 400)

        # Check if this is a voting request
        resource_path = event.get("resource", "")
        if "/vote" in resource_path:
            return handle_vote(event, dog_id)
        else:
            return update_dog(event, dog_id)

    except Exception as e:
        print(f"Error updating dog: {str(e)}")
        return ResponseFormatter.error_response(
            "Internal server error occurred while updating dog", 500
        )


def update_dog(event, dog_id):
    """
    Update dog information
    """
    try:
        # Parse the request body
        if "body" in event:
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]
        else:
            return ResponseFormatter.error_response("Request body is required", 400)

        dogs_table = dynamodb.Table(DOGS_TABLE)

        # Check if dog exists
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        if "Item" not in response:
            return ResponseFormatter.error_response("Dog not found", 404)

        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_attribute_values = {":updated_at": datetime.utcnow().isoformat()}

        # Handle updatable fields
        updatable_fields = [
            "shelter_name",
            "city",
            "state",
            "dog_species",
            "shelter_entry_date",
            "dog_description",
            "dog_birthday",
            "dog_weight",
            "dog_color",
            "dog_photo_url",
            "status",
        ]

        for field in updatable_fields:
            if field in body:
                if field == "state":
                    value = body[field].upper()
                elif field == "dog_color":
                    value = body[field].lower()
                elif field == "dog_weight":
                    value = float(body[field])
                else:
                    value = body[field]

                update_expression += f", {field} = :{field}"
                expression_attribute_values[f":{field}"] = value

        # Handle dog name encryption if provided
        if "dog_name" in body:
            encrypted_name = EncryptionUtils.encrypt_dog_name(body["dog_name"])
            update_expression += ", dog_name_encrypted = :dog_name_encrypted"
            expression_attribute_values[":dog_name_encrypted"] = encrypted_name

        # Recalculate age if birthday is updated
        if "dog_birthday" in body:
            try:
                from datetime import datetime

                birth_date = datetime.strptime(body["dog_birthday"], "%m/%d/%Y")
                age_years = (datetime.now() - birth_date).days / 365.25
                update_expression += ", dog_age_years = :dog_age_years"
                expression_attribute_values[":dog_age_years"] = round(age_years, 1)
            except:
                pass

        # Update the item
        response = dogs_table.update_item(
            Key={"dog_id": dog_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )

        updated_dog = response["Attributes"]

        # Remove encrypted name from response
        if "dog_name_encrypted" in updated_dog:
            del updated_dog["dog_name_encrypted"]

        return ResponseFormatter.success_response(
            updated_dog, "Dog updated successfully"
        )

    except json.JSONDecodeError:
        return ResponseFormatter.error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error updating dog: {str(e)}")
        return ResponseFormatter.error_response("Error updating dog", 500)


def handle_vote(event, dog_id):
    """
    Handle user voting (wag or growl) for a dog
    """
    try:
        # Parse the request body
        if "body" in event:
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]
        else:
            return ResponseFormatter.error_response("Request body is required", 400)

        user_id = body.get("user_id")
        vote_type = body.get("vote_type")

        if not user_id:
            return ResponseFormatter.error_response("User ID is required", 400)

        if not vote_type or not VoteSchema.validate_vote_type(vote_type):
            return ResponseFormatter.error_response(
                "Valid vote type (wag or growl) is required", 400
            )

        # Check if dog exists
        dogs_table = dynamodb.Table(DOGS_TABLE)
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        if "Item" not in response:
            return ResponseFormatter.error_response("Dog not found", 404)

        # Create vote record
        vote_record = VoteSchema.create_vote_record(user_id, dog_id, vote_type)

        # Save vote to votes table
        votes_table = dynamodb.Table(VOTES_TABLE)
        votes_table.put_item(Item=vote_record)

        # Update vote counts on dog record
        vote_field = f"{vote_type.lower()}_count"
        dogs_table.update_item(
            Key={"dog_id": dog_id},
            UpdateExpression=f"ADD {vote_field} :inc SET updated_at = :updated_at",
            ExpressionAttributeValues={
                ":inc": 1,
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        return ResponseFormatter.success_response(
            {
                "dog_id": dog_id,
                "user_id": user_id,
                "vote_type": vote_type,
                "timestamp": vote_record["created_at"],
            },
            f"Successfully recorded {vote_type} for dog",
        )

    except json.JSONDecodeError:
        return ResponseFormatter.error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error handling vote: {str(e)}")
        return ResponseFormatter.error_response("Error recording vote", 500)
