"""
Unit tests for the create dog API endpoint
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_dynamodb

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lambda.dogs.create import lambda_handler


class TestCreateDogAPI:
    """Test cases for the create dog API endpoint"""
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context"""
        context = MagicMock()
        context.function_name = "test-create-dog"
        context.function_version = "1"
        context.memory_limit_in_mb = 128
        context.aws_request_id = "test-request-id"
        context.get_remaining_time_in_millis.return_value = 30000
        return context
    
    @pytest.fixture
    def valid_dog_data(self):
        """Valid dog data for testing"""
        return {
            "shelter_name": "Arlington Shelter",
            "city": "Arlington",
            "state": "VA",
            "dog_name": "Fido",
            "dog_species": "Labrador Retriever",
            "shelter_entry_date": "1/7/2019",
            "dog_description": "Good boy",
            "dog_birthday": "4/23/2014",
            "dog_weight": 32,
            "dog_color": "Brown",
            "dog_photo_url": "https://example.com/photo.jpg"
        }
    
    @pytest.fixture
    def api_gateway_event(self, valid_dog_data):
        """Mock API Gateway event"""
        return {
            "httpMethod": "POST",
            "path": "/dogs",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "test-agent"
            },
            "body": json.dumps(valid_dog_data),
            "requestContext": {
                "requestId": "test-request-id",
                "identity": {
                    "sourceIp": "127.0.0.1"
                }
            }
        }
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images',
        'SHELTERS_TABLE': 'test-pupper-shelters'
    })
    def test_create_dog_success(self, api_gateway_event, lambda_context):
        """Test successful dog creation"""
        # Setup DynamoDB mock
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create test table
        table = dynamodb.create_table(
            TableName='test-pupper-dogs',
            KeySchema=[
                {'AttributeName': 'dog_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'dog_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Call the Lambda function
        response = lambda_handler(api_gateway_event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['message'] == "Dog successfully added to the system"
        assert 'data' in body
        
        dog_data = body['data']
        assert dog_data['shelter_name'] == "Arlington Shelter"
        assert dog_data['state'] == "VA"  # Should be uppercase
        assert dog_data['dog_color'] == "brown"  # Should be lowercase
        assert dog_data['is_labrador'] is True
        assert dog_data['wag_count'] == 0
        assert dog_data['growl_count'] == 0
        assert dog_data['status'] == "available"
        assert 'dog_id' in dog_data
        assert 'created_at' in dog_data
        assert 'dog_name_encrypted' not in dog_data  # Should not be in response
    
    def test_create_dog_invalid_json(self, lambda_context):
        """Test creation with invalid JSON"""
        event = {
            "httpMethod": "POST",
            "path": "/dogs",
            "body": "invalid json"
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Invalid JSON" in body['error']
    
    def test_create_dog_missing_required_field(self, lambda_context):
        """Test creation with missing required field"""
        incomplete_data = {
            "shelter_name": "Arlington Shelter",
            "city": "Arlington",
            # Missing state, dog_name, etc.
        }
        
        event = {
            "httpMethod": "POST",
            "path": "/dogs",
            "body": json.dumps(incomplete_data)
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Missing required field" in body['error']
    
    def test_create_dog_invalid_species(self, valid_dog_data, lambda_context):
        """Test creation with non-Labrador species"""
        valid_dog_data['dog_species'] = "Golden Retriever"
        
        event = {
            "httpMethod": "POST",
            "path": "/dogs",
            "body": json.dumps(valid_dog_data)
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Only Labrador Retrievers are allowed" in body['error']
    
    def test_create_dog_invalid_weight(self, valid_dog_data, lambda_context):
        """Test creation with invalid weight"""
        valid_dog_data['dog_weight'] = "thirty two pounds"
        
        event = {
            "httpMethod": "POST",
            "path": "/dogs",
            "body": json.dumps(valid_dog_data)
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "weight must be a valid number" in body['error']
    
    def test_create_dog_invalid_date_format(self, valid_dog_data, lambda_context):
        """Test creation with invalid date format"""
        valid_dog_data['dog_birthday'] = "2014-04-23"  # Wrong format
        
        event = {
            "httpMethod": "POST",
            "path": "/dogs",
            "body": json.dumps(valid_dog_data)
        }
        
        response = lambda_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "MM/DD/YYYY format" in body['error']
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images'
    })
    def test_create_dog_database_error(self, api_gateway_event, lambda_context):
        """Test handling of database errors"""
        # Don't create the table to simulate database error
        
        response = lambda_handler(api_gateway_event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Internal server error" in body['error']
    
    def test_dog_name_encryption(self, valid_dog_data):
        """Test that dog names are properly encrypted"""
        from schemas import EncryptionUtils
        
        dog_name = "Fido"
        encrypted_name = EncryptionUtils.encrypt_dog_name(dog_name)
        
        # Should be different from original
        assert encrypted_name != dog_name
        
        # Should be base64 encoded
        import base64
        try:
            decoded = base64.b64decode(encrypted_name.encode()).decode()
            assert decoded == dog_name
        except Exception:
            pytest.fail("Encrypted name is not valid base64")
    
    def test_age_calculation(self):
        """Test age calculation from birthday"""
        from schemas import DogSchema
        from datetime import datetime
        
        # Test with a known birthday
        dog_data = {
            "shelter_name": "Test Shelter",
            "city": "Test City",
            "state": "TX",
            "dog_name": "Test Dog",
            "dog_species": "Labrador Retriever",
            "shelter_entry_date": "1/1/2020",
            "dog_description": "Test description",
            "dog_birthday": "1/1/2020",  # 4+ years ago
            "dog_weight": 30,
            "dog_color": "black"
        }
        
        dog_record = DogSchema.create_dog_record(**dog_data)
        
        # Age should be calculated
        assert 'dog_age_years' in dog_record
        assert dog_record['dog_age_years'] > 0
        assert isinstance(dog_record['dog_age_years'], (int, float))
    
    def test_response_format(self, api_gateway_event, lambda_context):
        """Test that response format is correct"""
        with patch('boto3.resource'):
            response = lambda_handler(api_gateway_event, lambda_context)
            
            # Should have correct structure
            assert 'statusCode' in response
            assert 'headers' in response
            assert 'body' in response
            
            # Headers should include CORS
            headers = response['headers']
            assert 'Access-Control-Allow-Origin' in headers
            assert 'Content-Type' in headers
            
            # Body should be valid JSON
            body = json.loads(response['body'])
            assert isinstance(body, dict)
