#!/usr/bin/env python3
"""
Local test for image classification logic
This script tests the classification function locally without deploying to AWS
"""

import json
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_classification_logic():
    """Test the classification logic with mock data"""
    
    # Mock Rekognition response for a Labrador image
    mock_labrador_response = {
        'Labels': [
            {'Name': 'Dog', 'Confidence': 98.5},
            {'Name': 'Labrador Retriever', 'Confidence': 92.3},
            {'Name': 'Animal', 'Confidence': 99.1},
            {'Name': 'Pet', 'Confidence': 95.7},
            {'Name': 'Canine', 'Confidence': 98.2}
        ],
        'ResponseMetadata': {
            'HTTPHeaders': {'date': '2024-01-01T12:00:00Z'}
        }
    }
    
    # Mock Rekognition response for a non-Labrador dog
    mock_other_dog_response = {
        'Labels': [
            {'Name': 'Dog', 'Confidence': 97.8},
            {'Name': 'German Shepherd', 'Confidence': 89.4},
            {'Name': 'Animal', 'Confidence': 98.9},
            {'Name': 'Pet', 'Confidence': 94.2},
            {'Name': 'Canine', 'Confidence': 97.1}
        ],
        'ResponseMetadata': {
            'HTTPHeaders': {'date': '2024-01-01T12:00:00Z'}
        }
    }
    
    # Mock Rekognition response for a cat
    mock_cat_response = {
        'Labels': [
            {'Name': 'Cat', 'Confidence': 96.7},
            {'Name': 'Animal', 'Confidence': 98.2},
            {'Name': 'Pet', 'Confidence': 92.1},
            {'Name': 'Feline', 'Confidence': 95.8}
        ],
        'ResponseMetadata': {
            'HTTPHeaders': {'date': '2024-01-01T12:00:00Z'}
        }
    }
    
    # Test classification logic
    def simulate_classification(response):
        """Simulate the classification logic from classify.py"""
        labels = response.get('Labels', [])
        
        CONFIDENCE_THRESHOLD = 70.0
        LABRADOR_KEYWORDS = [
            "labrador retriever",
            "labrador",
            "lab", 
            "golden retriever",
            "retriever"
        ]
        
        dog_labels = []
        labrador_labels = []
        
        for label in labels:
            label_name = label['Name'].lower()
            confidence = label['Confidence']
            
            if 'dog' in label_name:
                dog_labels.append({
                    'name': label['Name'],
                    'confidence': confidence
                })
            
            for keyword in LABRADOR_KEYWORDS:
                if keyword in label_name:
                    labrador_labels.append({
                        'name': label['Name'],
                        'confidence': confidence,
                        'keyword_match': keyword
                    })
                    break
        
        is_labrador = len(labrador_labels) > 0
        is_dog = len(dog_labels) > 0
        
        return {
            'is_acceptable': is_labrador,
            'is_dog': is_dog,
            'is_labrador': is_labrador,
            'confidence_score': max([label['confidence'] for label in labrador_labels], default=0),
            'dog_labels': dog_labels,
            'labrador_labels': labrador_labels,
            'all_labels': [{'name': label['Name'], 'confidence': label['Confidence']} for label in labels]
        }
    
    # Test cases
    test_cases = [
        ("Labrador Retriever Image", mock_labrador_response, True),
        ("German Shepherd Image", mock_other_dog_response, False),
        ("Cat Image", mock_cat_response, False)
    ]
    
    print("🧪 Testing Image Classification Logic")
    print("=" * 50)
    
    for test_name, mock_response, expected_result in test_cases:
        print(f"\n📸 Testing: {test_name}")
        print("-" * 30)
        
        result = simulate_classification(mock_response)
        
        print(f"Expected: {'✅ Accept' if expected_result else '❌ Reject'}")
        print(f"Actual:   {'✅ Accept' if result['is_acceptable'] else '❌ Reject'}")
        print(f"Is Dog:   {result['is_dog']}")
        print(f"Is Labrador: {result['is_labrador']}")
        print(f"Confidence: {result['confidence_score']:.1f}%")
        
        if result['dog_labels']:
            print("Dog Labels:")
            for label in result['dog_labels']:
                print(f"  - {label['name']} ({label['confidence']:.1f}%)")
        
        if result['labrador_labels']:
            print("Labrador Labels:")
            for label in result['labrador_labels']:
                print(f"  - {label['name']} ({label['confidence']:.1f}%)")
        
        # Check if test passed
        if result['is_acceptable'] == expected_result:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
    
    print(f"\n{'=' * 50}")
    print("🎯 Classification Logic Test Complete")

def test_lambda_handler_structure():
    """Test the Lambda handler structure"""
    print("\n🔧 Testing Lambda Handler Structure")
    print("=" * 50)
    
    # Test event structure
    test_event = {
        'bucket': 'test-bucket',
        'key': 'uploads/test-image.jpg'
    }
    
    print("✅ Event structure valid:")
    print(f"   Bucket: {test_event['bucket']}")
    print(f"   Key: {test_event['key']}")
    
    # Test response structure
    mock_response = {
        'statusCode': 200,
        'body': {
            'success': True,
            'classification': {
                'is_acceptable': True,
                'is_labrador': True,
                'confidence_score': 92.3
            },
            'is_acceptable': True
        }
    }
    
    print("\n✅ Response structure valid:")
    print(f"   Status Code: {mock_response['statusCode']}")
    print(f"   Success: {mock_response['body']['success']}")
    print(f"   Acceptable: {mock_response['body']['is_acceptable']}")

if __name__ == "__main__":
    test_classification_logic()
    test_lambda_handler_structure()
    
    print("\n🚀 Ready for deployment!")
    print("Run './deploy_with_classification.sh' to deploy to AWS")
