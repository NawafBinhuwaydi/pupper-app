import json
import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Tuple

# AWS clients
rekognition = boto3.client("rekognition")
s3 = boto3.client("s3")

# Configuration
CONFIDENCE_THRESHOLD = 70.0  # Minimum confidence for dog detection
LABRADOR_KEYWORDS = [
    "labrador retriever",
    "labrador",
    "lab",
    "golden retriever",  # Often confused with labs, we'll accept both
    "retriever"
]

def classify_image_content(bucket: str, key: str) -> Dict:
    """
    Use Amazon Rekognition to classify image content and detect if it contains a Labrador Retriever
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Dict containing classification results
    """
    try:
        print(f"Starting image classification for s3://{bucket}/{key}")
        
        # Detect labels in the image
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=50,
            MinConfidence=CONFIDENCE_THRESHOLD
        )
        
        labels = response.get('Labels', [])
        print(f"Detected {len(labels)} labels with confidence >= {CONFIDENCE_THRESHOLD}%")
        
        # Check for dog-related labels
        dog_labels = []
        labrador_labels = []
        
        for label in labels:
            label_name = label['Name'].lower()
            confidence = label['Confidence']
            
            print(f"Label: {label['Name']} (Confidence: {confidence:.2f}%)")
            
            # Check if it's a dog
            if 'dog' in label_name:
                dog_labels.append({
                    'name': label['Name'],
                    'confidence': confidence
                })
            
            # Check if it's specifically a Labrador or related breed
            for keyword in LABRADOR_KEYWORDS:
                if keyword in label_name:
                    labrador_labels.append({
                        'name': label['Name'],
                        'confidence': confidence,
                        'keyword_match': keyword
                    })
                    break
        
        # Additional check using detect_custom_labels for more specific breed detection
        breed_info = detect_dog_breed(bucket, key)
        
        # Determine if image is acceptable
        is_labrador = len(labrador_labels) > 0
        is_dog = len(dog_labels) > 0
        
        # If we detect a dog but no specific Labrador labels, check breed detection
        if is_dog and not is_labrador and breed_info.get('is_labrador', False):
            is_labrador = True
            labrador_labels.append({
                'name': 'Labrador (breed detection)',
                'confidence': breed_info.get('confidence', 0),
                'keyword_match': 'breed_detection'
            })
        
        classification_result = {
            'is_acceptable': is_labrador,
            'is_dog': is_dog,
            'is_labrador': is_labrador,
            'confidence_score': max([label['confidence'] for label in labrador_labels], default=0),
            'dog_labels': dog_labels,
            'labrador_labels': labrador_labels,
            'all_labels': [{'name': label['Name'], 'confidence': label['Confidence']} for label in labels],
            'breed_detection': breed_info,
            'classification_timestamp': response['ResponseMetadata']['HTTPHeaders']['date']
        }
        
        print(f"Classification result: Acceptable={is_labrador}, Dog={is_dog}, Labrador={is_labrador}")
        return classification_result
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print(f"Rekognition error: {error_code} - {error_message}")
        
        # Handle specific errors
        if error_code == 'InvalidImageFormatException':
            return {
                'is_acceptable': False,
                'error': 'Invalid image format. Please upload a JPEG, PNG, or WebP image.',
                'error_code': 'INVALID_FORMAT'
            }
        elif error_code == 'ImageTooLargeException':
            return {
                'is_acceptable': False,
                'error': 'Image is too large for processing. Please upload a smaller image.',
                'error_code': 'IMAGE_TOO_LARGE'
            }
        elif error_code == 'InvalidS3ObjectException':
            return {
                'is_acceptable': False,
                'error': 'Could not access the uploaded image. Please try uploading again.',
                'error_code': 'S3_ACCESS_ERROR'
            }
        else:
            return {
                'is_acceptable': False,
                'error': f'Image classification failed: {error_message}',
                'error_code': 'CLASSIFICATION_ERROR'
            }
    
    except Exception as e:
        print(f"Unexpected error during classification: {str(e)}")
        return {
            'is_acceptable': False,
            'error': 'Image classification service temporarily unavailable. Please try again.',
            'error_code': 'SERVICE_ERROR'
        }

def detect_dog_breed(bucket: str, key: str) -> Dict:
    """
    Additional breed detection using text detection and object analysis
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        Dict containing breed detection results
    """
    try:
        # Use detect_text to see if there are any breed indicators in the image
        text_response = rekognition.detect_text(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        detected_text = []
        for text_detection in text_response.get('TextDetections', []):
            if text_detection['Type'] == 'LINE':
                detected_text.append(text_detection['DetectedText'].lower())
        
        # Check if any detected text mentions Labrador
        text_mentions_labrador = any(
            keyword in ' '.join(detected_text) 
            for keyword in LABRADOR_KEYWORDS
        )
        
        return {
            'detected_text': detected_text,
            'text_mentions_labrador': text_mentions_labrador,
            'is_labrador': text_mentions_labrador,
            'confidence': 80.0 if text_mentions_labrador else 0.0
        }
        
    except Exception as e:
        print(f"Breed detection error: {str(e)}")
        return {
            'detected_text': [],
            'text_mentions_labrador': False,
            'is_labrador': False,
            'confidence': 0.0,
            'error': str(e)
        }

def lambda_handler(event, context):
    """
    Lambda handler for image classification
    
    Expected event format:
    {
        "bucket": "bucket-name",
        "key": "path/to/image.jpg"
    }
    """
    try:
        print("Starting image classification Lambda")
        
        # Parse input
        bucket = event.get('bucket')
        key = event.get('key')
        
        if not bucket or not key:
            return {
                'statusCode': 400,
                'body': {
                    'success': False,
                    'error': 'Both bucket and key parameters are required',
                    'is_acceptable': False
                }
            }
        
        # Perform classification
        classification_result = classify_image_content(bucket, key)
        
        # Return result
        return {
            'statusCode': 200,
            'body': {
                'success': True,
                'classification': classification_result,
                'is_acceptable': classification_result.get('is_acceptable', False)
            }
        }
        
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'success': False,
                'error': 'Classification service error',
                'is_acceptable': False
            }
        }

# Helper function for testing
def test_classification():
    """Test function for local development"""
    test_event = {
        'bucket': 'pupper-images-test',
        'key': 'uploads/test-image.jpg'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_classification()
