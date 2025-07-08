import json
import os
import uuid
import base64
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Environment variables
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images-380141752789-us-east-1")
IMAGES_TABLE = os.environ.get("IMAGES_TABLE", "pupper-images")
CLASSIFICATION_FUNCTION = os.environ.get("CLASSIFICATION_FUNCTION", "")

# AWS clients
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Try to get the images table, create basic structure if it doesn't exist
try:
    images_table = dynamodb.Table(IMAGES_TABLE)
except:
    images_table = None


def classify_uploaded_image(bucket: str, key: str) -> dict:
    """
    Invoke the image classification Lambda function to check if image contains a Labrador Retriever
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Classification result dictionary
    """
    try:
        if not CLASSIFICATION_FUNCTION:
            print("Warning: Classification function not configured, skipping classification")
            return {
                'is_acceptable': True,  # Default to accepting if classification is not configured
                'classification_skipped': True,
                'reason': 'Classification function not configured'
            }
        
        print(f"Invoking classification function for s3://{bucket}/{key}")
        
        # Prepare payload for classification function
        payload = {
            'bucket': bucket,
            'key': key
        }
        
        # Invoke the classification Lambda function
        response = lambda_client.invoke(
            FunctionName=CLASSIFICATION_FUNCTION,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse the response
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            classification_body = response_payload.get('body', {})
            if classification_body.get('success', False):
                return classification_body.get('classification', {})
            else:
                print(f"Classification function returned error: {classification_body.get('error', 'Unknown error')}")
                return {
                    'is_acceptable': False,
                    'error': classification_body.get('error', 'Classification failed'),
                    'error_code': 'CLASSIFICATION_FAILED'
                }
        else:
            print(f"Classification function invocation failed with status: {response['StatusCode']}")
            return {
                'is_acceptable': False,
                'error': 'Image classification service unavailable',
                'error_code': 'SERVICE_UNAVAILABLE'
            }
            
    except Exception as e:
        print(f"Error invoking classification function: {str(e)}")
        return {
            'is_acceptable': False,
            'error': 'Image classification failed',
            'error_code': 'CLASSIFICATION_ERROR'
        }


def lambda_handler(event, context):
    """Lambda handler for uploading images"""
    
    try:
        print("Processing image upload request")
        
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
        print(f"Upload request received")
        
        # Validate required fields
        if not body.get("image_data"):
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
                    "error": "image_data is required"
                })
            }
        
        # Get image data and metadata
        image_data = body["image_data"]
        content_type = body.get("content_type", "image/jpeg")
        dog_id = body.get("dog_id", "")
        description = body.get("description", "")
        
        # Validate content type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if content_type not in allowed_types:
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
                    "error": f"Content type must be one of: {', '.join(allowed_types)}"
                })
            }
        
        # Generate unique image ID and key
        image_id = str(uuid.uuid4())
        file_extension = content_type.split("/")[1]
        if file_extension == "jpg":
            file_extension = "jpeg"
        
        s3_key = f"uploads/{image_id}/original.{file_extension}"
        
        try:
            # Decode base64 image data
            if "," in image_data:
                # Remove data URL prefix if present (data:image/jpeg;base64,...)
                image_data = image_data.split(",")[1]
            
            image_bytes = base64.b64decode(image_data)
            
            # Validate image size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if len(image_bytes) > max_size:
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
                        "error": f"Image size ({len(image_bytes)} bytes) exceeds maximum allowed size (50MB)"
                    })
                }
            
        except Exception as e:
            print(f"Error decoding image data: {str(e)}")
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
                    "error": "Invalid image data format"
                })
            }
        
        # Upload to S3
        try:
            print(f"Uploading image to S3: {s3_key}")
            s3.put_object(
                Bucket=IMAGES_BUCKET,
                Key=s3_key,
                Body=image_bytes,
                ContentType=content_type,
                Metadata={
                    "image_id": image_id,
                    "dog_id": dog_id,
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "original_size": str(len(image_bytes))
                }
            )
            
            # Generate the public URL
            original_url = f"https://{IMAGES_BUCKET}.s3.amazonaws.com/{s3_key}"
            
            print(f"Image uploaded successfully: {original_url}")
            
        except ClientError as e:
            print(f"Error uploading to S3: {str(e)}")
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
                    "error": "Failed to upload image to storage"
                })
            }
        
        # Classify the uploaded image using Amazon Rekognition
        print("Starting image classification...")
        classification_result = classify_uploaded_image(IMAGES_BUCKET, s3_key)
        
        # Check if image is acceptable (contains Labrador Retriever)
        if not classification_result.get('is_acceptable', False):
            # Delete the uploaded image since it's not acceptable
            try:
                s3.delete_object(Bucket=IMAGES_BUCKET, Key=s3_key)
                print(f"Deleted unacceptable image: {s3_key}")
            except Exception as delete_error:
                print(f"Warning: Could not delete rejected image: {str(delete_error)}")
            
            # Return rejection response
            error_message = classification_result.get('error', 
                'Only images of Labrador Retrievers are allowed. Please upload an image containing a Labrador Retriever.')
            
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
                    "error": error_message,
                    "error_code": classification_result.get('error_code', 'NOT_LABRADOR'),
                    "classification_details": {
                        "is_dog": classification_result.get('is_dog', False),
                        "is_labrador": classification_result.get('is_labrador', False),
                        "confidence_score": classification_result.get('confidence_score', 0),
                        "detected_labels": classification_result.get('dog_labels', [])
                    }
                })
            }
        
        print(f"Image classification passed - Labrador detected with confidence: {classification_result.get('confidence_score', 0):.2f}%")
        
        # Store metadata in DynamoDB (if table exists)
        current_time = datetime.utcnow().isoformat() + "Z"
        image_record = {
            "image_id": image_id,
            "dog_id": dog_id,
            "original_url": original_url,
            "s3_bucket": IMAGES_BUCKET,
            "s3_key": s3_key,
            "content_type": content_type,
            "size_bytes": len(image_bytes),
            "description": description,
            "status": "uploaded",
            "processing_status": "pending",
            "created_at": current_time,
            "updated_at": current_time,
            # Add classification results to metadata
            "classification_result": {
                "is_labrador": classification_result.get('is_labrador', False),
                "confidence_score": classification_result.get('confidence_score', 0),
                "detected_labels": classification_result.get('labrador_labels', []),
                "classification_timestamp": classification_result.get('classification_timestamp', current_time)
            }
        }
        
        if images_table:
            try:
                images_table.put_item(Item=image_record)
                print("Image metadata saved to DynamoDB")
            except Exception as e:
                print(f"Warning: Could not save to DynamoDB: {str(e)}")
                # Continue anyway - the image is uploaded to S3
        
        # Return success response
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
                    "message": "Image uploaded and verified as Labrador Retriever successfully",
                    "image_id": image_id,
                    "original_url": original_url,
                    "status": "uploaded",
                    "processing_status": "pending",
                    "size_bytes": len(image_bytes),
                    "content_type": content_type,
                    "created_at": current_time,
                    "classification": {
                        "is_labrador": classification_result.get('is_labrador', False),
                        "confidence_score": classification_result.get('confidence_score', 0),
                        "detected_labels": [label['name'] for label in classification_result.get('labrador_labels', [])]
                    }
                }
            })
        }

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
        print(f"Unexpected error uploading image: {str(e)}")
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
