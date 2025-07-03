import json
import boto3
import os
import sys

# Add the backend directory to the path to import schemas
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from schemas import ResponseFormatter
except ImportError:
    # Fallback for when schemas module is not available
    class ResponseFormatter:
        @staticmethod
        def success_response(data, message="Success"):
            return {
                "statusCode": 200,
                "body": json.dumps({"success": True, "data": data}),
            }

        @staticmethod
        def error_response(error, status_code=400):
            return {"statusCode": status_code, "body": json.dumps({"error": error})}


# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

# Get environment variables
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images")


def lambda_handler(event, context):
    """
    Lambda function to delete a dog entry
    """
    try:
        # Get dog ID from path parameters
        path_parameters = event.get("pathParameters", {})
        dog_id = path_parameters.get("dog_id")

        if not dog_id:
            return ResponseFormatter.error_response("Dog ID is required", 400)

        dogs_table = dynamodb.Table(DOGS_TABLE)

        # Check if dog exists and get its data
        response = dogs_table.get_item(Key={"dog_id": dog_id})
        if "Item" not in response:
            return ResponseFormatter.error_response("Dog not found", 404)

        dog_data = response["Item"]

        # Delete associated images from S3
        try:
            delete_dog_images(dog_id)
        except Exception as e:
            print(f"Warning: Error deleting images for dog {dog_id}: {str(e)}")
            # Continue with deletion even if image cleanup fails

        # Delete the dog record from DynamoDB
        dogs_table.delete_item(Key={"dog_id": dog_id})

        # TODO: Also delete associated votes from votes table
        # This would require querying the votes table by dog_id and deleting all votes

        return ResponseFormatter.success_response(
            {"dog_id": dog_id, "deleted_at": dog_data.get("created_at")},
            "Dog successfully deleted from the system",
        )

    except Exception as e:
        print(f"Error deleting dog: {str(e)}")
        return ResponseFormatter.error_response(
            "Internal server error occurred while deleting dog", 500
        )


def delete_dog_images(dog_id):
    """
    Delete all images associated with a dog from S3
    """
    try:
        # List all objects with the dog's prefix
        prefix = f"dogs/{dog_id}/"

        response = s3_client.list_objects_v2(Bucket=IMAGES_BUCKET, Prefix=prefix)

        if "Contents" in response:
            # Delete all objects
            objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]

            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket=IMAGES_BUCKET, Delete={"Objects": objects_to_delete}
                )
                print(f"Deleted {len(objects_to_delete)} images for dog {dog_id}")

    except Exception as e:
        print(f"Error deleting images for dog {dog_id}: {str(e)}")
        raise e


def soft_delete_dog(dog_id):
    """
    Alternative: Soft delete by marking dog as inactive instead of hard delete
    This preserves data for analytics while hiding from users
    """
    try:
        dogs_table = dynamodb.Table(DOGS_TABLE)

        response = dogs_table.update_item(
            Key={"dog_id": dog_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "deleted",
                ":updated_at": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )

        return response["Attributes"]

    except Exception as e:
        print(f"Error soft deleting dog: {str(e)}")
        raise e
