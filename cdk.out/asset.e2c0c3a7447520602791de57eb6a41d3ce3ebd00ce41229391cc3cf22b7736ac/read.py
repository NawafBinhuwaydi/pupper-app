import json
import boto3
import os
import sys
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

# Add the backend directory to the path to import schemas
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from schemas import FilterSchema, ResponseFormatter, EncryptionUtils
except ImportError:
    # Fallback for when schemas module is not available
    class FilterSchema:
        @staticmethod
        def parse_filters(params):
            return params

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
        def decrypt_dog_name(encrypted_name):
            import base64

            try:
                return base64.b64decode(encrypted_name.encode()).decode()
            except:
                return "Unknown"


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images")


def lambda_handler(event, context):
    """
    Lambda function to read dog entries
    Supports both single dog retrieval and filtered list retrieval
    """
    try:
        # Check if this is a request for a specific dog
        path_parameters = event.get("pathParameters", {})
        if path_parameters and path_parameters.get("dog_id"):
            return get_single_dog(path_parameters["dog_id"])

        # Otherwise, return filtered list of dogs
        query_parameters = event.get("queryStringParameters", {}) or {}
        return get_filtered_dogs(query_parameters)

    except Exception as e:
        print(f"Error reading dogs: {str(e)}")
        return ResponseFormatter.error_response(
            "Internal server error occurred while reading dogs", 500
        )


def get_single_dog(dog_id):
    """
    Retrieve a single dog by ID
    """
    try:
        dogs_table = dynamodb.Table(DOGS_TABLE)

        response = dogs_table.get_item(Key={"dog_id": dog_id})

        if "Item" not in response:
            return ResponseFormatter.error_response("Dog not found", 404)

        dog = response["Item"]

        # Decrypt dog name for display
        if "dog_name_encrypted" in dog:
            dog["dog_name"] = EncryptionUtils.decrypt_dog_name(
                dog["dog_name_encrypted"]
            )
            del dog["dog_name_encrypted"]  # Remove encrypted version from response

        # Convert Decimal types to float for JSON serialization
        dog = convert_decimals(dog)

        return ResponseFormatter.success_response(dog, "Dog retrieved successfully")

    except Exception as e:
        print(f"Error getting single dog: {str(e)}")
        return ResponseFormatter.error_response("Error retrieving dog", 500)


def get_filtered_dogs(query_parameters):
    """
    Retrieve dogs with optional filters
    """
    try:
        dogs_table = dynamodb.Table(DOGS_TABLE)

        # Parse filters
        filters = FilterSchema.parse_filters(query_parameters)

        # Start with scanning all dogs (in production, consider pagination)
        scan_kwargs = {
            "FilterExpression": Attr("is_labrador").eq(
                True
            )  # Only show Labrador Retrievers
        }

        # Apply filters
        filter_expressions = [Attr("is_labrador").eq(True)]

        if "state" in filters:
            filter_expressions.append(Attr("state").eq(filters["state"]))

        if "color" in filters:
            filter_expressions.append(Attr("dog_color").eq(filters["color"]))

        if "min_weight" in filters:
            filter_expressions.append(Attr("dog_weight").gte(filters["min_weight"]))

        if "max_weight" in filters:
            filter_expressions.append(Attr("dog_weight").lte(filters["max_weight"]))

        if "min_age" in filters:
            filter_expressions.append(Attr("dog_age_years").gte(filters["min_age"]))

        if "max_age" in filters:
            filter_expressions.append(Attr("dog_age_years").lte(filters["max_age"]))

        # Combine all filter expressions
        if len(filter_expressions) > 1:
            combined_filter = filter_expressions[0]
            for expr in filter_expressions[1:]:
                combined_filter = combined_filter & expr
            scan_kwargs["FilterExpression"] = combined_filter

        # Perform the scan
        response = dogs_table.scan(**scan_kwargs)
        dogs = response.get("Items", [])

        # Process each dog
        processed_dogs = []
        for dog in dogs:
            # Decrypt dog name for display
            if "dog_name_encrypted" in dog:
                dog["dog_name"] = EncryptionUtils.decrypt_dog_name(
                    dog["dog_name_encrypted"]
                )
                del dog["dog_name_encrypted"]  # Remove encrypted version from response

            # Convert Decimal types
            dog = convert_decimals(dog)
            processed_dogs.append(dog)

        # Sort by created_at (newest first)
        processed_dogs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return ResponseFormatter.success_response(
            {
                "dogs": processed_dogs,
                "count": len(processed_dogs),
                "filters_applied": filters,
            },
            "Dogs retrieved successfully",
        )

    except Exception as e:
        print(f"Error getting filtered dogs: {str(e)}")
        return ResponseFormatter.error_response("Error retrieving dogs", 500)


def get_user_wags(user_id):
    """
    Get all dogs that a user has given a "wag" to
    """
    try:
        # This would query the votes table to get user's wags
        # Then retrieve the corresponding dog records
        # Implementation depends on votes table structure
        pass
    except Exception as e:
        print(f"Error getting user wags: {str(e)}")
        return ResponseFormatter.error_response("Error retrieving user wags", 500)


def convert_decimals(obj):
    """
    Convert DynamoDB Decimal types to float for JSON serialization
    """
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
