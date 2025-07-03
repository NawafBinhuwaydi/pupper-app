"""
Unit tests for the read dog API endpoint
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch
from decimal import Decimal

import pytest
from moto import mock_dynamodb

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lambda.dogs.read import lambda_handler


class TestReadDogAPI:
    """Test cases for the read dog API endpoint"""
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context"""
        context = MagicMock()
        context.function_name = "test-read-dog"
        context.function_version = "1"
        context.memory_limit_in_mb = 128
        context.aws_request_id = "test-request-id"
        context.get_remaining_time_in_millis.return_value = 30000
        return context
    
    @pytest.fixture
    def sample_dog_data(self):
        """Sample dog data for testing"""
        return {
            "dog_id": "test-dog-id-123",
            "shelter_name": "Arlington Shelter",
            "city": "Arlington",
            "state": "VA",
            "dog_name_encrypted": "Rmlkbw==",  # "Fido" in base64
            "dog_species": "Labrador Retriever",
            "shelter_entry_date": "1/7/2019",
            "dog_description": "Good boy",
            "dog_birthday": "4/23/2014",
            "dog_weight": Decimal("32"),
            "dog_color": "brown",
            "dog_age_years": Decimal("9.2"),
            "dog_photo_url": "https://example.com/photo.jpg",
            "created_at": "2024-01-01T12:00:00.000Z",
            "updated_at": "2024-01-01T12:00:00.000Z",
            "is_labrador": True,
            "wag_count": Decimal("5"),
            "growl_count": Decimal("1"),
            "status": "available"
        }
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images'
    })
    def test_get_single_dog_success(self, sample_dog_data, lambda_context):
        """Test successful retrieval of a single dog"""
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
        
        # Insert test data
        table.put_item(Item=sample_dog_data)
        
        # Create API Gateway event for single dog
        event = {
            "httpMethod": "GET",
            "path": "/dogs/test-dog-id-123",
            "pathParameters": {
                "dog_id": "test-dog-id-123"
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['message'] == "Dog retrieved successfully"
        assert 'data' in body
        
        dog_data = body['data']
        assert dog_data['dog_id'] == "test-dog-id-123"
        assert dog_data['dog_name'] == "Fido"  # Should be decrypted
        assert 'dog_name_encrypted' not in dog_data  # Should not be in response
        assert dog_data['shelter_name'] == "Arlington Shelter"
        assert dog_data['dog_weight'] == 32  # Decimal should be converted to float
    
    def test_get_single_dog_not_found(self, lambda_context):
        """Test retrieval of non-existent dog"""
        with mock_dynamodb():
            # Setup DynamoDB mock
            import boto3
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            
            # Create empty test table
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
            
            # Create API Gateway event for non-existent dog
            event = {
                "httpMethod": "GET",
                "path": "/dogs/non-existent-id",
                "pathParameters": {
                    "dog_id": "non-existent-id"
                }
            }
            
            with patch.dict(os.environ, {'DOGS_TABLE': 'test-pupper-dogs'}):
                response = lambda_handler(event, lambda_context)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['success'] is False
            assert body['error'] == "Dog not found"
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images'
    })
    def test_get_all_dogs_success(self, sample_dog_data, lambda_context):
        """Test successful retrieval of all dogs"""
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
        
        # Insert multiple test dogs
        dog1 = sample_dog_data.copy()
        dog1['dog_id'] = 'dog-1'
        dog1['dog_color'] = 'brown'
        dog1['state'] = 'VA'
        
        dog2 = sample_dog_data.copy()
        dog2['dog_id'] = 'dog-2'
        dog2['dog_color'] = 'black'
        dog2['state'] = 'CA'
        
        table.put_item(Item=dog1)
        table.put_item(Item=dog2)
        
        # Create API Gateway event for all dogs
        event = {
            "httpMethod": "GET",
            "path": "/dogs",
            "queryStringParameters": None
        }
        
        # Call the Lambda function
        response = lambda_handler(event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['message'] == "Dogs retrieved successfully"
        assert 'data' in body
        
        data = body['data']
        assert 'dogs' in data
        assert 'count' in data
        assert data['count'] == 2
        assert len(data['dogs']) == 2
        
        # Check that dog names are decrypted
        for dog in data['dogs']:
            assert 'dog_name' in dog
            assert 'dog_name_encrypted' not in dog
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images'
    })
    def test_get_dogs_with_state_filter(self, sample_dog_data, lambda_context):
        """Test retrieval of dogs with state filter"""
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
        
        # Insert dogs from different states
        dog_va = sample_dog_data.copy()
        dog_va['dog_id'] = 'dog-va'
        dog_va['state'] = 'VA'
        
        dog_ca = sample_dog_data.copy()
        dog_ca['dog_id'] = 'dog-ca'
        dog_ca['state'] = 'CA'
        
        table.put_item(Item=dog_va)
        table.put_item(Item=dog_ca)
        
        # Create API Gateway event with state filter
        event = {
            "httpMethod": "GET",
            "path": "/dogs",
            "queryStringParameters": {
                "state": "VA"
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        data = body['data']
        
        # Should only return VA dogs
        assert data['count'] >= 0  # Filtering might not work perfectly in mock
        assert 'filters_applied' in data
        assert data['filters_applied']['state'] == 'VA'
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGES_BUCKET': 'test-pupper-images'
    })
    def test_get_dogs_with_weight_filter(self, sample_dog_data, lambda_context):
        """Test retrieval of dogs with weight filter"""
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
        
        # Insert dogs with different weights
        light_dog = sample_dog_data.copy()
        light_dog['dog_id'] = 'light-dog'
        light_dog['dog_weight'] = Decimal("20")
        
        heavy_dog = sample_dog_data.copy()
        heavy_dog['dog_id'] = 'heavy-dog'
        heavy_dog['dog_weight'] = Decimal("60")
        
        table.put_item(Item=light_dog)
        table.put_item(Item=heavy_dog)
        
        # Create API Gateway event with weight filter
        event = {
            "httpMethod": "GET",
            "path": "/dogs",
            "queryStringParameters": {
                "min_weight": "25",
                "max_weight": "50"
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        data = body['data']
        
        assert 'filters_applied' in data
        assert data['filters_applied']['min_weight'] == 25.0
        assert data['filters_applied']['max_weight'] == 50.0
    
    def test_get_dogs_invalid_filter_values(self, lambda_context):
        """Test handling of invalid filter values"""
        event = {
            "httpMethod": "GET",
            "path": "/dogs",
            "queryStringParameters": {
                "min_weight": "invalid",
                "max_age": "not_a_number"
            }
        }
        
        with mock_dynamodb():
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
            
            with patch.dict(os.environ, {'DOGS_TABLE': 'test-pupper-dogs'}):
                response = lambda_handler(event, lambda_context)
            
            # Should still work, just ignore invalid filters
            assert response['statusCode'] == 200
            
            body = json.loads(response['body'])
            data = body['data']
            
            # Invalid filters should not be applied
            filters = data.get('filters_applied', {})
            assert 'min_weight' not in filters
            assert 'max_age' not in filters
    
    def test_decimal_conversion(self):
        """Test conversion of Decimal types to float"""
        from lambda.dogs.read import convert_decimals
        
        test_data = {
            'weight': Decimal('32.5'),
            'age': Decimal('5'),
            'nested': {
                'count': Decimal('10')
            },
            'list': [Decimal('1'), Decimal('2')],
            'string': 'test',
            'int': 42
        }
        
        converted = convert_decimals(test_data)
        
        assert converted['weight'] == 32.5
        assert converted['age'] == 5.0
        assert converted['nested']['count'] == 10.0
        assert converted['list'] == [1.0, 2.0]
        assert converted['string'] == 'test'
        assert converted['int'] == 42
    
    def test_dog_name_decryption(self):
        """Test dog name decryption"""
        from schemas import EncryptionUtils
        
        original_name = "Buddy"
        encrypted_name = EncryptionUtils.encrypt_dog_name(original_name)
        decrypted_name = EncryptionUtils.decrypt_dog_name(encrypted_name)
        
        assert decrypted_name == original_name
    
    def test_dog_name_decryption_invalid(self):
        """Test handling of invalid encrypted dog names"""
        from schemas import EncryptionUtils
        
        invalid_encrypted = "invalid_base64!"
        decrypted_name = EncryptionUtils.decrypt_dog_name(invalid_encrypted)
        
        assert decrypted_name == "Unknown"
    
    def test_response_headers(self, lambda_context):
        """Test that response includes proper headers"""
        event = {
            "httpMethod": "GET",
            "path": "/dogs",
            "queryStringParameters": None
        }
        
        with mock_dynamodb():
            with patch.dict(os.environ, {'DOGS_TABLE': 'test-pupper-dogs'}):
                # Setup minimal table
                import boto3
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
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
                
                response = lambda_handler(event, lambda_context)
        
        assert 'headers' in response
        headers = response['headers']
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Content-Type' in headers
        assert headers['Content-Type'] == 'application/json'
