#!/usr/bin/env python3
"""
Test script for image classification functionality
"""

import json
import base64
import requests
import os
from pathlib import Path

# Configuration
API_BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"  # Update with your actual API URL

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def test_image_upload(image_path: str, description: str = "Test image"):
    """Test image upload with classification"""
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return None
    
    print(f"Testing image upload: {image_path}")
    print(f"Description: {description}")
    
    # Encode image
    try:
        image_data = encode_image_to_base64(image_path)
        print(f"Image encoded successfully, size: {len(image_data)} characters")
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None
    
    # Determine content type
    file_extension = Path(image_path).suffix.lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp'
    }
    content_type = content_type_map.get(file_extension, 'image/jpeg')
    
    # Prepare request payload
    payload = {
        "image_data": image_data,
        "content_type": content_type,
        "description": description,
        "dog_id": "",  # Optional
        "tags": ["test", "classification"]
    }
    
    # Make API request
    try:
        print("Sending request to API...")
        response = requests.post(
            f"{API_BASE_URL}/images",
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 201:
            # Success - Labrador detected
            result = response.json()
            print("✅ SUCCESS: Image accepted (Labrador Retriever detected)")
            print(f"Image ID: {result['data']['image_id']}")
            print(f"Image URL: {result['data']['original_url']}")
            
            if 'classification' in result['data']:
                classification = result['data']['classification']
                print(f"Classification confidence: {classification.get('confidence_score', 0):.2f}%")
                print(f"Detected labels: {', '.join(classification.get('detected_labels', []))}")
            
            return result
            
        elif response.status_code == 400:
            # Rejection - Not a Labrador
            result = response.json()
            print("❌ REJECTED: Image not accepted")
            print(f"Reason: {result.get('error', 'Unknown error')}")
            
            if 'classification_details' in result:
                details = result['classification_details']
                print(f"Is dog detected: {details.get('is_dog', False)}")
                print(f"Is Labrador detected: {details.get('is_labrador', False)}")
                print(f"Confidence score: {details.get('confidence_score', 0):.2f}%")
                
                if details.get('detected_labels'):
                    print("Detected labels:")
                    for label in details['detected_labels']:
                        print(f"  - {label['name']} ({label['confidence']:.2f}%)")
            
            return result
            
        else:
            print(f"❌ ERROR: Unexpected response status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON response: {str(e)}")
        return None

def create_test_images():
    """Create sample test images for testing (placeholder function)"""
    print("To test the classification system, you'll need:")
    print("1. Images of Labrador Retrievers (should be accepted)")
    print("2. Images of other dog breeds (should be rejected)")
    print("3. Images of non-dogs (should be rejected)")
    print("4. Invalid images (should be rejected)")
    print()
    print("Place test images in a 'test_images' directory with descriptive names:")
    print("  - labrador_1.jpg")
    print("  - golden_retriever.jpg")
    print("  - german_shepherd.jpg")
    print("  - cat.jpg")
    print("  - landscape.jpg")

def main():
    """Main test function"""
    print("🐕 Pupper Image Classification Test")
    print("=" * 50)
    
    # Check if API URL is configured
    if "your-api-gateway-url" in API_BASE_URL:
        print("❌ ERROR: Please update API_BASE_URL with your actual API Gateway URL")
        print("You can find this in your CDK deployment outputs or AWS Console")
        return
    
    # Test images directory
    test_images_dir = Path("test_images")
    
    if not test_images_dir.exists():
        print(f"Test images directory not found: {test_images_dir}")
        create_test_images()
        return
    
    # Find test images
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    test_images = []
    
    for ext in image_extensions:
        test_images.extend(test_images_dir.glob(f"*{ext}"))
        test_images.extend(test_images_dir.glob(f"*{ext.upper()}"))
    
    if not test_images:
        print("No test images found in test_images directory")
        create_test_images()
        return
    
    print(f"Found {len(test_images)} test images")
    print()
    
    # Test each image
    results = []
    for image_path in sorted(test_images):
        print(f"\n{'='*60}")
        result = test_image_upload(str(image_path), f"Test image: {image_path.name}")
        results.append({
            'image': image_path.name,
            'result': result
        })
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    accepted = 0
    rejected = 0
    errors = 0
    
    for test in results:
        if test['result'] is None:
            status = "ERROR"
            errors += 1
        elif test['result'].get('success', False):
            status = "ACCEPTED"
            accepted += 1
        else:
            status = "REJECTED"
            rejected += 1
        
        print(f"{test['image']:<30} {status}")
    
    print(f"\nTotal: {len(results)} images")
    print(f"Accepted: {accepted}")
    print(f"Rejected: {rejected}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    main()
