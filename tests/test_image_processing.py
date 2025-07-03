"""
Unit tests for image processing functionality
"""
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

from lambda.image_processing.resize import lambda_handler as resize_handler


class TestImageProcessing:
    """Test cases for image processing functionality"""
    
    @pytest.fixture
    def lambda_context(self):
        """Mock Lambda context"""
        context = MagicMock()
        context.function_name = "test-image-processing"
        context.function_version = "1"
        context.memory_limit_in_mb = 3008
        context.aws_request_id = "test-request-id"
        context.get_remaining_time_in_millis.return_value = 300000
        return context
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes"""
        img = Image.new('RGB', (800, 600), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        return buffer.getvalue()
    
    @pytest.fixture
    def large_image_bytes(self):
        """Create large image bytes"""
        img = Image.new('RGB', (2000, 1500), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        return buffer.getvalue()
    
    @pytest.fixture
    def s3_event(self):
        """Mock S3 event"""
        return {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-pupper-images"},
                        "object": {"key": "uploads/test-image-123/original.jpg"}
                    }
                }
            ]
        }
    
    @pytest.fixture
    def direct_invocation_event(self):
        """Mock direct invocation event"""
        return {
            "image_id": "test-image-123",
            "original_key": "uploads/test-image-123/original.jpg",
            "trigger_source": "upload_api"
        }
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table',
        'DOGS_TABLE': 'test-pupper-dogs'
    })
    def test_s3_event_processing(self, s3_event, lambda_context, sample_image_bytes):
        """Test processing triggered by S3 event"""
        # Setup AWS mocks
        import boto3
        
        # Create S3 bucket and upload test image
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/test-image-123/original.jpg',
            Body=sample_image_bytes,
            ContentType='image/jpeg'
        )
        
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
        
        # Insert initial metadata
        table.put_item(Item={
            'image_id': 'test-image-123',
            'original_key': 'uploads/test-image-123/original.jpg',
            'status': 'uploaded',
            'processing_status': 'pending'
        })
        
        # Call the processing handler
        response = resize_handler(s3_event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['processed'] == 1
        assert body['failed'] == 0
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_direct_invocation_processing(self, direct_invocation_event, lambda_context, sample_image_bytes):
        """Test processing via direct invocation"""
        # Setup AWS mocks
        import boto3
        
        # Create S3 bucket and upload test image
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/test-image-123/original.jpg',
            Body=sample_image_bytes,
            ContentType='image/jpeg'
        )
        
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
        
        # Insert initial metadata
        table.put_item(Item={
            'image_id': 'test-image-123',
            'original_key': 'uploads/test-image-123/original.jpg',
            'status': 'uploaded',
            'processing_status': 'pending'
        })
        
        # Call the processing handler
        response = resize_handler(direct_invocation_event, lambda_context)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['image_id'] == 'test-image-123'
        assert 'versions_created' in body
    
    def test_direct_invocation_missing_image_id(self, lambda_context):
        """Test direct invocation without image_id"""
        event = {
            "trigger_source": "upload_api"
            # Missing image_id
        }
        
        response = resize_handler(event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "image_id is required" in body['error']
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_large_image_processing(self, lambda_context, large_image_bytes):
        """Test processing of large images"""
        # Setup AWS mocks
        import boto3
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/large-image-456/original.jpg',
            Body=large_image_bytes,
            ContentType='image/jpeg'
        )
        
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
        
        table.put_item(Item={
            'image_id': 'large-image-456',
            'original_key': 'uploads/large-image-456/original.jpg',
            'status': 'uploaded',
            'processing_status': 'pending'
        })
        
        event = {
            "image_id": "large-image-456",
            "original_key": "uploads/large-image-456/original.jpg"
        }
        
        response = resize_handler(event, lambda_context)
        
        # Should handle large images successfully
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
    
    @mock_s3
    def test_image_download_failure(self, lambda_context):
        """Test handling of S3 download failures"""
        # Don't create the S3 object to simulate failure
        import boto3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        
        event = {
            "image_id": "missing-image",
            "original_key": "uploads/missing-image/original.jpg"
        }
        
        with patch.dict(os.environ, {'IMAGES_BUCKET': 'test-pupper-images'}):
            response = resize_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "download" in body['error'].lower()
    
    def test_invalid_s3_key_format(self, lambda_context):
        """Test handling of invalid S3 key format"""
        s3_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "invalid/key/format.jpg"}  # Wrong format
                    }
                }
            ]
        }
        
        response = resize_handler(s3_event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['processed'] == 0
        assert body['failed'] == 1
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_corrupted_image_handling(self, lambda_context):
        """Test handling of corrupted image data"""
        # Setup AWS mocks
        import boto3
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        
        # Upload corrupted image data
        corrupted_data = b"This is not an image file"
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/corrupted-123/original.jpg',
            Body=corrupted_data,
            ContentType='image/jpeg'
        )
        
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
        
        table.put_item(Item={
            'image_id': 'corrupted-123',
            'original_key': 'uploads/corrupted-123/original.jpg',
            'status': 'uploaded',
            'processing_status': 'pending'
        })
        
        event = {
            "image_id": "corrupted-123",
            "original_key": "uploads/corrupted-123/original.jpg"
        }
        
        response = resize_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "Failed to open image" in body['error']
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_resize_configurations(self, lambda_context, sample_image_bytes):
        """Test that all resize configurations are processed"""
        # Setup AWS mocks
        import boto3
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/test-resize-789/original.jpg',
            Body=sample_image_bytes,
            ContentType='image/jpeg'
        )
        
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
        
        table.put_item(Item={
            'image_id': 'test-resize-789',
            'original_key': 'uploads/test-resize-789/original.jpg',
            'status': 'uploaded',
            'processing_status': 'pending'
        })
        
        event = {
            "image_id": "test-resize-789",
            "original_key": "uploads/test-resize-789/original.jpg"
        }
        
        response = resize_handler(event, lambda_context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        
        # Check that multiple versions were created
        assert body['versions_created'] >= 2  # At least 400x400 and 50x50
        
        # Verify metadata was updated
        updated_item = table.get_item(Key={'image_id': 'test-resize-789'})['Item']
        assert updated_item['processing_status'] == 'completed'
        assert 'resized_urls' in updated_item
        assert len(updated_item['resized_urls']) >= 2
    
    def test_unknown_event_source(self, lambda_context):
        """Test handling of unknown event sources"""
        unknown_event = {
            "unknown_field": "unknown_value"
        }
        
        response = resize_handler(unknown_event, lambda_context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['success'] is False
        assert "image_id is required" in body['error']
    
    @mock_s3
    @mock_dynamodb
    @patch.dict(os.environ, {
        'IMAGES_BUCKET': 'test-pupper-images',
        'IMAGES_TABLE': 'test-pupper-images-table'
    })
    def test_metadata_update_failure(self, lambda_context, sample_image_bytes):
        """Test handling of metadata update failures"""
        # Setup S3 but not DynamoDB to simulate metadata failure
        import boto3
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-pupper-images')
        s3.put_object(
            Bucket='test-pupper-images',
            Key='uploads/metadata-fail-999/original.jpg',
            Body=sample_image_bytes,
            ContentType='image/jpeg'
        )
        
        # Don't create DynamoDB table to simulate failure
        
        event = {
            "image_id": "metadata-fail-999",
            "original_key": "uploads/metadata-fail-999/original.jpg"
        }
        
        response = resize_handler(event, lambda_context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
    
    def test_image_processing_performance(self, lambda_context, sample_image_bytes):
        """Test image processing performance metrics"""
        # This test would verify that processing completes within reasonable time
        # and memory constraints for various image sizes
        
        # For now, just verify the function can handle the test image
        with mock_s3(), mock_dynamodb():
            import boto3
            
            s3 = boto3.client('s3', region_name='us-east-1')
            s3.create_bucket(Bucket='test-pupper-images')
            s3.put_object(
                Bucket='test-pupper-images',
                Key='uploads/perf-test/original.jpg',
                Body=sample_image_bytes,
                ContentType='image/jpeg'
            )
            
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
            
            table.put_item(Item={
                'image_id': 'perf-test',
                'original_key': 'uploads/perf-test/original.jpg',
                'status': 'uploaded',
                'processing_status': 'pending'
            })
            
            event = {
                "image_id": "perf-test",
                "original_key": "uploads/perf-test/original.jpg"
            }
            
            with patch.dict(os.environ, {
                'IMAGES_BUCKET': 'test-pupper-images',
                'IMAGES_TABLE': 'test-pupper-images-table'
            }):
                import time
                start_time = time.time()
                response = resize_handler(event, lambda_context)
                end_time = time.time()
                
                # Processing should complete within reasonable time (e.g., 30 seconds)
                processing_time = end_time - start_time
                assert processing_time < 30
                
                # Should succeed
                assert response['statusCode'] == 200
