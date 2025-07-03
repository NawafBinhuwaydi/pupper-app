"""
Lambda function to process dog images
Creates 400x400 and 50x50 versions of uploaded images
Handles large images (>10MB) with optimized processing
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import boto3
from PIL import Image, ImageOps
import io
from botocore.exceptions import ClientError

# Add the backend directory to the path to import utilities
sys.path.append("/opt/python")
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from utils.logger import get_lambda_logger, log_s3_operation
    from utils.tracing import trace_lambda_handler, trace_s3_operation
except ImportError:
    # Fallback for when modules are not available
    def get_lambda_logger(context):
        import logging

        return logging.getLogger()

    def log_s3_operation(
        logger, operation, bucket, key, size_bytes=None, duration_ms=None, success=True
    ):
        pass

    def trace_lambda_handler(func):
        return func

    def trace_s3_operation(operation, bucket, key):
        def decorator(func):
            return func

        return decorator


# Initialize AWS clients
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# Get environment variables
IMAGES_BUCKET = os.environ.get("IMAGES_BUCKET", "pupper-images")
DOGS_TABLE = os.environ.get("DOGS_TABLE", "pupper-dogs")
IMAGES_TABLE = os.environ.get("IMAGES_TABLE", "pupper-images")

# Image processing configuration
RESIZE_CONFIGS = [
    {"name": "400x400", "size": (400, 400), "quality": 85, "format": "PNG"},
    {"name": "50x50", "size": (50, 50), "quality": 85, "format": "PNG"},
    {
        "name": "800x600",
        "size": (800, 600),
        "quality": 90,
        "format": "JPEG",
    },  # High quality preview
    {
        "name": "200x150",
        "size": (200, 150),
        "quality": 80,
        "format": "JPEG",
    },  # Thumbnail
]

# Memory optimization settings
MAX_PIXELS = 50000000  # 50MP limit to prevent memory issues
CHUNK_SIZE = 8192  # For streaming large files


@trace_lambda_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to process dog images
    Creates multiple resized versions of uploaded images
    """
    logger = get_lambda_logger(context)

    try:
        logger.info(
            "Image processing started", event_source=determine_event_source(event)
        )

        # Handle different event sources
        if "Records" in event:
            # S3 event trigger
            return process_s3_events(event["Records"], logger)
        else:
            # Direct invocation
            return process_direct_invocation(event, logger)

    except Exception as e:
        logger.error(
            "Image processing failed", error=str(e), error_type=type(e).__name__
        )
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"success": False, "error": f"Image processing failed: {str(e)}"}
            ),
        }


def determine_event_source(event: Dict[str, Any]) -> str:
    """Determine the source of the event"""
    if "Records" in event:
        return "s3_event"
    elif "image_id" in event:
        return "direct_invocation"
    else:
        return "unknown"


def process_s3_events(records: list, logger) -> Dict[str, Any]:
    """Process S3 event notifications"""
    processed_count = 0
    failed_count = 0

    for record in records:
        try:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]

            logger.info("Processing S3 event", bucket=bucket, key=key)

            # Extract image_id from key (format: uploads/{image_id}/original.ext)
            path_parts = key.split("/")
            if len(path_parts) >= 2 and path_parts[0] == "uploads":
                image_id = path_parts[1]
                result = process_image_from_s3(image_id, bucket, key, logger)

                if result["success"]:
                    processed_count += 1
                else:
                    failed_count += 1
                    logger.error(
                        "Failed to process S3 image",
                        image_id=image_id,
                        error=result.get("error"),
                    )
            else:
                logger.warning("Invalid S3 key format", key=key)
                failed_count += 1

        except Exception as e:
            logger.error("Error processing S3 record", error=str(e))
            failed_count += 1

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "success": True,
                "message": f"Processed {processed_count} images, {failed_count} failed",
                "processed": processed_count,
                "failed": failed_count,
            }
        ),
    }


def process_direct_invocation(event: Dict[str, Any], logger) -> Dict[str, Any]:
    """Process direct Lambda invocation"""
    image_id = event.get("image_id")
    original_key = event.get("original_key")

    if not image_id:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "success": False,
                    "error": "image_id is required for direct invocation",
                }
            ),
        }

    if original_key:
        # Process from provided key
        result = process_image_from_s3(image_id, IMAGES_BUCKET, original_key, logger)
    else:
        # Process from image metadata
        result = process_image_from_metadata(image_id, logger)

    status_code = 200 if result["success"] else 500

    return {"statusCode": status_code, "body": json.dumps(result)}


def process_image_from_s3(
    image_id: str, bucket: str, key: str, logger
) -> Dict[str, Any]:
    """Process an image from S3"""
    try:
        logger.info(
            "Starting image processing", image_id=image_id, bucket=bucket, key=key
        )

        # Update processing status
        update_processing_status(image_id, "processing", logger)

        # Download and validate image
        image_data = download_image_from_s3(bucket, key, logger)
        if not image_data["success"]:
            update_processing_status(image_id, "failed", logger, image_data["error"])
            return image_data

        # Process the image
        processing_result = process_image_data(
            image_id, image_data["data"], image_data["content_type"], logger
        )

        if processing_result["success"]:
            # Update metadata with processing results
            update_result = update_image_metadata_with_results(
                image_id, processing_result["results"], logger
            )

            if update_result["success"]:
                update_processing_status(image_id, "completed", logger)
                logger.info(
                    "Image processing completed successfully", image_id=image_id
                )
                return {
                    "success": True,
                    "message": "Image processed successfully",
                    "image_id": image_id,
                    "processed_versions": len(processing_result["results"]),
                }
            else:
                update_processing_status(
                    image_id, "metadata_update_failed", logger, update_result["error"]
                )
                return update_result
        else:
            update_processing_status(
                image_id, "failed", logger, processing_result["error"]
            )
            return processing_result

    except Exception as e:
        error_msg = f"Unexpected error processing image: {str(e)}"
        logger.error("Image processing error", error=error_msg, image_id=image_id)
        update_processing_status(image_id, "failed", logger, error_msg)
        return {"success": False, "error": error_msg}


def process_image_from_metadata(image_id: str, logger) -> Dict[str, Any]:
    """Process image using metadata from DynamoDB"""
    try:
        # Get image metadata
        metadata_result = get_image_metadata(image_id, logger)
        if not metadata_result["success"]:
            return metadata_result

        metadata = metadata_result["data"]
        original_key = metadata.get("original_key")

        if not original_key:
            return {"success": False, "error": "No original key found in metadata"}

        return process_image_from_s3(image_id, IMAGES_BUCKET, original_key, logger)

    except Exception as e:
        error_msg = f"Error processing image from metadata: {str(e)}"
        logger.error("Metadata processing error", error=error_msg, image_id=image_id)
        return {"success": False, "error": error_msg}


@trace_s3_operation("get_object", "", "")
def download_image_from_s3(bucket: str, key: str, logger) -> Dict[str, Any]:
    """Download image from S3 with error handling"""
    start_time = time.time()

    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")

        duration_ms = (time.time() - start_time) * 1000
        log_s3_operation(
            logger,
            "get_object",
            bucket,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=True,
        )

        logger.info(
            "Image downloaded successfully",
            bucket=bucket,
            key=key,
            size_bytes=len(image_data),
        )

        return {
            "success": True,
            "data": image_data,
            "content_type": content_type,
            "size_bytes": len(image_data),
        }

    except ClientError as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"S3 download failed: {str(e)}"
        log_s3_operation(
            logger, "get_object", bucket, key, duration_ms=duration_ms, success=False
        )
        logger.error("S3 download error", error=error_msg, bucket=bucket, key=key)
        return {"success": False, "error": error_msg}

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Unexpected download error: {str(e)}"
        log_s3_operation(
            logger, "get_object", bucket, key, duration_ms=duration_ms, success=False
        )
        logger.error("Download error", error=error_msg, bucket=bucket, key=key)
        return {"success": False, "error": error_msg}


def process_image_data(
    image_id: str, image_data: bytes, content_type: str, logger
) -> Dict[str, Any]:
    """Process image data to create resized versions"""
    try:
        logger.info(
            "Starting image data processing",
            image_id=image_id,
            size_bytes=len(image_data),
        )

        # Open and validate the image
        try:
            image = Image.open(io.BytesIO(image_data))

            # Auto-orient image based on EXIF data
            image = ImageOps.exif_transpose(image)

            # Convert to RGB if necessary (handles RGBA, CMYK, etc.)
            if image.mode not in ("RGB", "L"):
                if image.mode == "RGBA":
                    # Create white background for transparent images
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert("RGB")

            original_dimensions = image.size
            logger.info(
                "Image opened successfully",
                image_id=image_id,
                dimensions=original_dimensions,
                mode=image.mode,
            )

        except Exception as e:
            error_msg = f"Failed to open image: {str(e)}"
            logger.error("Image open error", error=error_msg, image_id=image_id)
            return {"success": False, "error": error_msg}

        # Check image size limits
        total_pixels = original_dimensions[0] * original_dimensions[1]
        if total_pixels > MAX_PIXELS:
            error_msg = f"Image too large: {total_pixels} pixels (max: {MAX_PIXELS})"
            logger.error("Image size error", error=error_msg, image_id=image_id)
            return {"success": False, "error": error_msg}

        # Process each resize configuration
        processing_results = []

        for config in RESIZE_CONFIGS:
            try:
                result = create_resized_version(image, image_id, config, logger)

                if result["success"]:
                    processing_results.append(result)
                    logger.info(
                        "Resize completed",
                        image_id=image_id,
                        version=config["name"],
                        size=config["size"],
                    )
                else:
                    logger.error(
                        "Resize failed",
                        image_id=image_id,
                        version=config["name"],
                        error=result["error"],
                    )

            except Exception as e:
                logger.error(
                    "Resize processing error",
                    error=str(e),
                    image_id=image_id,
                    version=config["name"],
                )

        if not processing_results:
            return {
                "success": False,
                "error": "No resized versions were created successfully",
            }

        logger.info(
            "Image processing completed",
            image_id=image_id,
            versions_created=len(processing_results),
        )

        return {
            "success": True,
            "results": processing_results,
            "original_dimensions": original_dimensions,
            "versions_created": len(processing_results),
        }

    except Exception as e:
        error_msg = f"Image processing failed: {str(e)}"
        logger.error("Processing error", error=error_msg, image_id=image_id)
        return {"success": False, "error": error_msg}


def create_resized_version(
    image: Image.Image, image_id: str, config: dict, logger
) -> Dict[str, Any]:
    """Create a single resized version of the image"""
    try:
        # Resize image while maintaining aspect ratio
        resized_image = resize_image_with_padding(image, config["size"])

        # Convert to appropriate format
        if config["format"] == "PNG":
            output_format = "PNG"
            file_extension = "png"
        else:
            output_format = "JPEG"
            file_extension = "jpg"
            # Ensure RGB mode for JPEG
            if resized_image.mode != "RGB":
                resized_image = resized_image.convert("RGB")

        # Save to bytes buffer
        img_buffer = io.BytesIO()
        save_kwargs = {"format": output_format}

        if output_format == "JPEG":
            save_kwargs["quality"] = config["quality"]
            save_kwargs["optimize"] = True
        elif output_format == "PNG":
            save_kwargs["optimize"] = True

        resized_image.save(img_buffer, **save_kwargs)
        img_buffer.seek(0)

        # Generate S3 key
        s3_key = f"processed/{image_id}/{config['name']}.{file_extension}"

        # Upload to S3
        upload_result = upload_resized_image(
            img_buffer.getvalue(), s3_key, config, logger
        )

        if upload_result["success"]:
            return {
                "success": True,
                "version": config["name"],
                "key": s3_key,
                "url": f"https://{IMAGES_BUCKET}.s3.amazonaws.com/{s3_key}",
                "size": config["size"],
                "format": config["format"],
                "file_size_bytes": len(img_buffer.getvalue()),
            }
        else:
            return upload_result

    except Exception as e:
        error_msg = f"Failed to create {config['name']} version: {str(e)}"
        logger.error(
            "Resize creation error",
            error=error_msg,
            image_id=image_id,
            version=config["name"],
        )
        return {"success": False, "error": error_msg}


def resize_image_with_padding(
    image: Image.Image, target_size: Tuple[int, int]
) -> Image.Image:
    """
    Resize image while maintaining aspect ratio and adding padding if necessary
    """
    original_width, original_height = image.size
    target_width, target_height = target_size

    # Calculate scaling factor to fit within target size
    scale = min(target_width / original_width, target_height / original_height)

    # Calculate new dimensions
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create final image with target size and white background
    final_image = Image.new("RGB", target_size, (255, 255, 255))

    # Calculate position to center the resized image
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2

    # Paste the resized image onto the white background
    final_image.paste(resized_image, (x, y))

    return final_image


@trace_s3_operation("put_object", IMAGES_BUCKET, "")
def upload_resized_image(
    image_data: bytes, key: str, config: dict, logger
) -> Dict[str, Any]:
    """Upload resized image to S3"""
    start_time = time.time()

    try:
        content_type = "image/png" if config["format"] == "PNG" else "image/jpeg"

        s3_client.put_object(
            Bucket=IMAGES_BUCKET,
            Key=key,
            Body=image_data,
            ContentType=content_type,
            Metadata={
                "processed_at": datetime.utcnow().isoformat(),
                "version": config["name"],
                "size": f"{config['size'][0]}x{config['size'][1]}",
                "format": config["format"],
            },
        )

        duration_ms = (time.time() - start_time) * 1000
        log_s3_operation(
            logger,
            "put_object",
            IMAGES_BUCKET,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=True,
        )

        return {"success": True, "key": key}

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to upload resized image: {str(e)}"
        log_s3_operation(
            logger,
            "put_object",
            IMAGES_BUCKET,
            key,
            size_bytes=len(image_data),
            duration_ms=duration_ms,
            success=False,
        )
        logger.error("Upload error", error=error_msg, key=key)
        return {"success": False, "error": error_msg}


def update_processing_status(
    image_id: str, status: str, logger, error_message: str = None
) -> None:
    """Update image processing status in DynamoDB"""
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)

        update_expression = "SET processing_status = :status, updated_at = :updated_at"
        expression_values = {
            ":status": status,
            ":updated_at": datetime.utcnow().isoformat(),
        }

        if error_message:
            update_expression += ", error_message = :error"
            expression_values[":error"] = error_message

        images_table.update_item(
            Key={"image_id": image_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
        )

        logger.info("Processing status updated", image_id=image_id, status=status)

    except Exception as e:
        logger.error(
            "Failed to update processing status",
            error=str(e),
            image_id=image_id,
            status=status,
        )


def update_image_metadata_with_results(
    image_id: str, results: list, logger
) -> Dict[str, Any]:
    """Update image metadata with processing results"""
    try:
        # Prepare resized URLs and dimensions
        resized_urls = {}
        dimensions = {}

        for result in results:
            version = result["version"]
            resized_urls[version] = result["url"]
            dimensions[version] = {
                "width": result["size"][0],
                "height": result["size"][1],
                "file_size_bytes": result["file_size_bytes"],
            }

        # Update DynamoDB record
        images_table = dynamodb.Table(IMAGES_TABLE)

        images_table.update_item(
            Key={"image_id": image_id},
            UpdateExpression="""
                SET resized_urls = :urls,
                    dimensions = :dims,
                    processing_status = :status,
                    updated_at = :updated_at
            """,
            ExpressionAttributeValues={
                ":urls": resized_urls,
                ":dims": dimensions,
                ":status": "completed",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(
            "Image metadata updated with results",
            image_id=image_id,
            versions=len(results),
        )

        return {"success": True}

    except Exception as e:
        error_msg = f"Failed to update image metadata: {str(e)}"
        logger.error("Metadata update error", error=error_msg, image_id=image_id)
        return {"success": False, "error": error_msg}


def get_image_metadata(image_id: str, logger) -> Dict[str, Any]:
    """Get image metadata from DynamoDB"""
    try:
        images_table = dynamodb.Table(IMAGES_TABLE)
        response = images_table.get_item(Key={"image_id": image_id})

        if "Item" not in response:
            return {"success": False, "error": "Image metadata not found"}

        return {"success": True, "data": response["Item"]}

    except Exception as e:
        error_msg = f"Failed to get image metadata: {str(e)}"
        logger.error("Metadata get error", error=error_msg, image_id=image_id)
        return {"success": False, "error": error_msg}
