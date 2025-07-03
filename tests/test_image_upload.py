"""
Unit tests for image upload functionality
"""
import base64
import json
import os
import sys
from unittest.mock import MagicMock, patch, Mock
from io import BytesIO

import pytest
from moto import mock_dynamodb, mock_s3
from PIL import Image

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lambda.image_processing.upload import lambda_handler as upload_handler
from schemas import ImageSchema


class TestImageUpload:
    """Test cases for image upload functionality"""
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context"""
        context = MagicMock()
        context.function_name = "test-image-upload"
        context.function_version = "1"
        context.memory_limit_in_mb = 1024
        context.aws_request_id = "test-request-id"
        context.get_remaining_time_in_millis.return_value = 30000
        return context
    
    @pytest.fixture
    def sample_image_base64(self):
        """Create a sample image in base64 format"""
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        # Convert to base64
        image_data = buffer.getvalue()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        return {
            'base64': base64_data,
            'bytes': image_data,
            'size': len(image_data)
        }
    
    @pytest.fixture
    def large_image_base64(self):
        """Create a large test image (>10MB)"""
        # Create a large test image
        img = Image.new('RGB', (3000, 3000), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        image_data = buffer.getvalue()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        return {
            'base64': base64_data,
            'bytes': image_data,
            'size': len(image_data)
        }
    
    @pytest.fixture
    def upload_event(self, sample_image_base64):
        """Mock API Gateway event for image upload"""
        return {
            "httpMethod": "POST",
            "path": "/images",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "image_data": sample_image_base64['base64'],
                "content_type": "image/jpeg",
                "dog_id": "test-dog-123",
                "description": "Test dog photo",
                "tags": ["cute", "labrador"]
            }),
            "requestContext": {
                "requestId": "test-request-id"
            }
        }
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table',
        'DOGS_TABLE': 'test-pupper-dogs',
        'IMAGE_PROCESSING_FUNCTION': 'test-image-processing'
    })
    def test_image_upload_success(self, upload_event, lambda_context, sample_image_base64):
        """Test successful image upload"""
        # Setup AWS mocks
        import boto3
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-pupper-images-table',
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Lambda client
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = Mock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {}
            
            # Call the upload handler
            response = upload_handler(upload_event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['message'] == "Image uploaded successfully"
        assert 'data' in body
        
        data = body['data']
        assert 'image_id' in data
        assert data['status'] == 'uploaded'
        assert data['processing_status'] == 'queued'
        assert data['content_type'] == 'image/jpeg'
        assert data['size_bytes'] == sample_image_base64['size']
        assert 'original_url' in data
        assert 'created_at' in data
    
    def test_image_upload_missing_data(self, lambda_context):
        """Test upload with missing image data"""
        event = {
            "httpMethod": "POST",
            "path": "/images",
            "body": json.dumps({
                "content_type": "image/jpeg"
                # Missing image_data
            })
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Missing required field: image_data" in body['error']
    
    def test_image_upload_invalid_content_type(self, lambda_context, sample_image_base64):
        """Test upload with unsupported content type"""
        event = {
            "httpMethod": "POST",
            "path": "/images",
            "body": json.dumps({
                "image_data": sample_image_base64['base64'],
                "content_type": "image/gif"  # Unsupported
            })
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Unsupported image format" in body['error']
    
    def test_image_upload_invalid_base64(self, lambda_context):
        """Test upload with invalid base64 data"""
        event = {
            "httpMethod": "POST",
            "path": "/images",
            "body": json.dumps({
                "image_data": "invalid_base64_data!",
                "content_type": "image/jpeg"
            })
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Invalid base64 image data" in body['error']
    
    def test_image_upload_too_small(self, lambda_context):
        """Test upload with image too small"""
        # Create tiny image
        tiny_data = b"tiny"
        base64_data = base64.b64encode(tiny_data).decode('utf-8')
        
        event = {
            "httpMethod": "POST",
            "path": "/images",
            "body": json.dumps({
                "image_data": base64_data,
                "content_type": "image/jpeg"
            })
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Image too small" in body['error']
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_large_image_upload(self, lambda_context, large_image_base64):
        """Test upload of large image (>10MB)"""
        # Setup AWS mocks
        import boto3
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-pupper-images-table',
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        event = {
            "httpMethod": "POST",
            "path": "/images",
            "body": json.dumps({
                "image_data": large_image_base64['base64'],
                "content_type": "image/jpeg"
            })
        }
        
        # Mock Lambda client
        with patch('boto3.client') as mock_boto_client:
            mock_lambda = Mock()
            mock_boto_client.return_value = mock_lambda
            mock_lambda.invoke.return_value = {}
            
            response = upload_handler(event, lambda_context)
        
        # Should succeed for large images under 50MB limit
        if large_image_base64['size'] < 50 * 1024 * 1024:
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
        else:
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert "Image too large" in body['error']
    
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_image_metadata_retrieval(self, lambda_context):
        """Test image metadata retrieval"""
        # Setup DynamoDB table
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='test-pupper-images-table',
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Insert test metadata
        test_metadata = {
            'image_id': 'test-image-123',
            'original_url': 'https://example.com/image.jpg',
            'status': 'completed',
            'processing_status': 'completed',
            'content_type': 'image/jpeg',
            'size_bytes': 12345,
            'resized_urls': {
                '400x400': 'https://example.com/400x400.png',
                '50x50': 'https://example.com/50x50.png'
            },
            'created_at': '2024-01-01T12:00:00.000Z'
        }
        table.put_item(Item=test_metadata)
        
        # Create GET request event
        event = {
            "httpMethod": "GET",
            "path": "/images/test-image-123",
            "pathParameters": {
                "image_id": "test-image-123"
            }
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['image_id'] == 'test-image-123'
        assert body['data']['status'] == 'completed'
        assert '400x400' in body['data']['resized_urls']
    
    def test_image_metadata_not_found(self, lambda_context):
        """Test metadata retrieval for non-existent image"""
        with mock_dynamodb():
            # Setup empty table
            import boto3
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.create_table(
                TableName='test-pupper-images-table',
                KeySchema=[
                    {'AttributeName': 'image_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'image_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            event = {
                "httpMethod": "GET",
                "path": "/images/non-existent",
                "pathParameters": {
                    "image_id": "non-existent"
                }
            }
            
            with patch.dict(os.environ, {'IMAGES_TABLE': 'test-pupper-images-table'}):
                response = upload_handler(event, lambda_context)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['success'] is False
            assert "Image not found" in body['error']
    
    def test_unsupported_http_method(self, lambda_context):
        """Test unsupported HTTP method"""
        event = {
            "httpMethod": "DELETE",
            "path": "/images"
        }
        
        response = upload_handler(event, lambda_context)
        
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Method not allowed" in body['error']


class TestImageSchema:
    """Test cases for ImageSchema"""
    
    def test_create_image_record(self):
        """Test image record creation"""
        record = ImageSchema.create_image_record(
            image_id="test-123",
            original_key="uploads/test-123/original.jpg",
            content_type="image/jpeg",
            size_bytes=12345,
            dog_id="dog-456",
            description="Test image",
            tags=["test", "photo"]
        )
        
        assert record['image_id'] == "test-123"
        assert record['original_key'] == "uploads/test-123/original.jpg"
        assert record['content_type'] == "image/jpeg"
        assert record['size_bytes'] == 12345
        assert record['dog_id'] == "dog-456"
        assert record['description'] == "Test image"
        assert record['tags'] == ["test", "photo"]
        assert record['status'] == "uploaded"
        assert record['processing_status'] == "pending"
        assert 'created_at' in record
        assert 'updated_at' in record
    
    def test_validate_image_upload_success(self):
        """Test successful image upload validation"""
        # Create valid base64 image data
        img = Image.new('RGB', (10, 10), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        data = {
            "image_data": base64_data,
            "content_type": "image/jpeg"
        }
        
        is_valid, message = ImageSchema.validate_image_upload(data)
        
        assert is_valid is True
        assert message == "Valid"
    
    def test_validate_image_upload_missing_field(self):
        """Test validation with missing field"""
        data = {
            "content_type": "image/jpeg"
            # Missing image_data
        }
        
        is_valid, message = ImageSchema.validate_image_upload(data)
        
        assert is_valid is False
        assert "Missing required field: image_data" in message
    
    def test_validate_image_upload_invalid_content_type(self):
        """Test validation with invalid content type"""
        data = {
            "image_data": "dGVzdA==",  # base64 for "test"
            "content_type": "image/gif"
        }
        
        is_valid, message = ImageSchema.validate_image_upload(data)
        
        assert is_valid is False
        assert "Unsupported content type" in message
    
    def test_validate_image_upload_invalid_base64(self):
        """Test validation with invalid base64"""
        data = {
            "image_data": "invalid_base64!",
            "content_type": "image/jpeg"
        }
        
        is_valid, message = ImageSchema.validate_image_upload(data)
        
        assert is_valid is False
        assert "Invalid base64 image data" in message
    
    def test_get_supported_formats(self):
        """Test getting supported formats"""
        formats = ImageSchema.get_supported_formats()
        
        assert isinstance(formats, list)
        assert 'image/jpeg' in formats
        assert 'image/png' in formats
        assert len(formats) > 0
    
    def test_get_max_file_size(self):
        """Test getting max file size"""
        max_size = ImageSchema.get_max_file_size()
        
        assert isinstance(max_size, int)
        assert max_size == 50 * 1024 * 1024  # 50MB
    
    def test_get_resize_configurations(self):
        """Test getting resize configurations"""
        configs = ImageSchema.get_resize_configurations()
        
        assert isinstance(configs, list)
        assert len(configs) > 0
        
        # Check that required configs exist
        config_names = [config['name'] for config in configs]
        assert '400x400' in config_names
        assert '50x50' in config_names
        
        # Check config structure
        for config in configs:
            assert 'name' in config
            assert 'size' in config
            assert 'format' in config
            assert isinstance(config['size'], tuple)
            assert len(config['size']) == 2
