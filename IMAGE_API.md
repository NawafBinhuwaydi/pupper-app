# Image Upload and Processing API

This document describes the image upload and processing functionality for the Pupper application.

## Overview

The image service provides:
- **Large Image Upload**: Support for images up to 50MB
- **Automatic Processing**: Creates multiple resized versions
- **Metadata Storage**: Tracks original and processed image information
- **Asynchronous Processing**: Non-blocking image processing pipeline

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│  Upload Lambda   │───▶│   S3 Bucket     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
                       ┌──────────────────┐              │
                       │  Images Table    │              │
                       │   (DynamoDB)     │              │
                       └──────────────────┘              │
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Processed      │◀───│ Processing       │◀───│  S3 Event       │
│  Images (S3)    │    │  Lambda          │    │  Trigger        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## API Endpoints

### POST /images - Upload Image

Upload a new image for processing.

**Request:**
```http
POST /images
Content-Type: application/json

{
  "image_data": "base64_encoded_image_data",
  "content_type": "image/jpeg",
  "dog_id": "optional-dog-uuid",
  "description": "Optional description",
  "tags": ["optional", "tags"]
}
```

**Request Fields:**
- `image_data` (required): Base64 encoded image data
- `content_type` (required): MIME type (`image/jpeg`, `image/png`, `image/webp`)
- `dog_id` (optional): Associated dog ID
- `description` (optional): Image description
- `tags` (optional): Array of tags

**Response:**
```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "data": {
    "image_id": "uuid-generated",
    "original_url": "https://bucket.s3.amazonaws.com/uploads/uuid/original.jpg",
    "status": "uploaded",
    "processing_status": "queued",
    "size_bytes": 1234567,
    "content_type": "image/jpeg",
    "created_at": "2024-01-01T12:00:00.000Z"
  }
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": "Missing required field: image_data"
}
```

### GET /images/{image_id} - Get Image Metadata

Retrieve metadata for a specific image.

**Request:**
```http
GET /images/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "success": true,
  "message": "Image metadata retrieved successfully",
  "data": {
    "image_id": "550e8400-e29b-41d4-a716-446655440000",
    "original_url": "https://bucket.s3.amazonaws.com/uploads/uuid/original.jpg",
    "resized_urls": {
      "400x400": "https://bucket.s3.amazonaws.com/processed/uuid/400x400.png",
      "50x50": "https://bucket.s3.amazonaws.com/processed/uuid/50x50.png",
      "800x600": "https://bucket.s3.amazonaws.com/processed/uuid/800x600.jpg",
      "200x150": "https://bucket.s3.amazonaws.com/processed/uuid/200x150.jpg"
    },
    "status": "uploaded",
    "processing_status": "completed",
    "content_type": "image/jpeg",
    "size_bytes": 1234567,
    "dimensions": {
      "400x400": {
        "width": 400,
        "height": 400,
        "file_size_bytes": 45678
      },
      "50x50": {
        "width": 50,
        "height": 50,
        "file_size_bytes": 2345
      }
    },
    "dog_id": "dog-uuid",
    "description": "Beautiful Labrador",
    "tags": ["cute", "labrador"],
    "created_at": "2024-01-01T12:00:00.000Z",
    "updated_at": "2024-01-01T12:05:00.000Z"
  }
}
```

## Image Processing

### Supported Formats

**Input Formats:**
- JPEG (`image/jpeg`, `image/jpg`)
- PNG (`image/png`)
- WebP (`image/webp`)

**Output Formats:**
- PNG for thumbnails and square images
- JPEG for larger preview images

### Size Limits

- **Minimum Size**: 1KB
- **Maximum Size**: 50MB
- **Maximum Pixels**: 50 megapixels (to prevent memory issues)

### Resize Configurations

The system automatically creates the following versions:

| Version | Size | Format | Quality | Use Case |
|---------|------|--------|---------|----------|
| 400x400 | 400×400px | PNG | 85% | Dog profile display |
| 50x50 | 50×50px | PNG | 85% | Thumbnail/avatar |
| 800x600 | 800×600px | JPEG | 90% | High-quality preview |
| 200x150 | 200×150px | JPEG | 80% | List view thumbnail |

### Processing Pipeline

1. **Upload**: Image uploaded to S3 `uploads/` prefix
2. **Validation**: Content type and size validation
3. **Metadata Storage**: Initial metadata saved to DynamoDB
4. **Trigger Processing**: S3 event triggers processing Lambda
5. **Image Processing**: 
   - Download original image
   - Create resized versions
   - Upload processed images to S3
6. **Update Metadata**: Store URLs and dimensions in DynamoDB

### Processing Status

- `pending`: Initial upload completed, processing not started
- `processing`: Image processing in progress
- `completed`: All resize versions created successfully
- `failed`: Processing failed (check error_message field)
- `queued`: Processing triggered but not yet started

## Error Handling

### Upload Errors

| Error | Status Code | Description |
|-------|-------------|-------------|
| Missing required field | 400 | Required field not provided |
| Unsupported image format | 400 | Content type not supported |
| Invalid base64 image data | 400 | Image data cannot be decoded |
| Image too small | 400 | Image smaller than 1KB |
| Image too large | 400 | Image larger than 50MB |
| Internal server error | 500 | Unexpected server error |

### Processing Errors

Processing errors are stored in the `error_message` field and the `processing_status` is set to `failed`.

Common processing errors:
- Failed to open image (corrupted file)
- Image too large (exceeds pixel limit)
- S3 upload/download failures
- Memory allocation errors

## Performance Considerations

### Upload Performance

- **Large Images**: Images >10MB are supported but may take longer to upload
- **Base64 Encoding**: Increases payload size by ~33%
- **Timeout**: Upload timeout is 60 seconds

### Processing Performance

- **Memory**: Processing Lambda has 3GB memory for large images
- **Timeout**: Processing timeout is 5 minutes
- **Concurrency**: Limited concurrent processing to manage memory usage
- **Ephemeral Storage**: 2GB temporary storage for large image processing

### Optimization Tips

1. **Compress Images**: Use appropriate JPEG quality before upload
2. **Batch Processing**: Upload multiple images separately rather than in one request
3. **Monitor Status**: Check processing_status before using resized images
4. **Cache URLs**: Cache resized image URLs to avoid repeated API calls

## Security

### Access Control

- All API endpoints require authentication (to be implemented)
- S3 bucket blocks public access
- Images are served through CloudFront (to be implemented)

### Data Protection

- Images stored in versioned S3 bucket
- Metadata stored in DynamoDB with point-in-time recovery
- All data encrypted at rest and in transit

### Input Validation

- Content type validation
- File size limits
- Base64 data validation
- Malicious file detection (basic)

## Monitoring and Logging

### Structured Logging

All operations include structured logs with:
- Request ID correlation
- Processing duration
- File sizes and dimensions
- Error details and stack traces

### Metrics

Key metrics tracked:
- Upload success/failure rates
- Processing duration by image size
- Storage usage
- API response times

### Tracing

AWS X-Ray tracing enabled for:
- End-to-end request tracing
- S3 operation performance
- DynamoDB query performance
- Lambda cold start analysis

## Usage Examples

### JavaScript/Node.js

```javascript
// Upload image
const uploadImage = async (imageFile, dogId) => {
  // Convert file to base64
  const base64Data = await fileToBase64(imageFile);
  
  const response = await fetch('/images', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify({
      image_data: base64Data,
      content_type: imageFile.type,
      dog_id: dogId,
      description: 'Dog photo'
    })
  });
  
  return response.json();
};

// Check processing status
const checkProcessingStatus = async (imageId) => {
  const response = await fetch(`/images/${imageId}`);
  const data = await response.json();
  
  return data.data.processing_status;
};

// Get resized image URL
const getResizedImageUrl = async (imageId, size = '400x400') => {
  const response = await fetch(`/images/${imageId}`);
  const data = await response.json();
  
  return data.data.resized_urls[size];
};
```

### Python

```python
import base64
import requests

def upload_image(image_path, dog_id=None):
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine content type
    content_type = 'image/jpeg' if image_path.endswith('.jpg') else 'image/png'
    
    # Upload
    response = requests.post('/images', json={
        'image_data': image_data,
        'content_type': content_type,
        'dog_id': dog_id
    })
    
    return response.json()

def get_image_metadata(image_id):
    response = requests.get(f'/images/{image_id}')
    return response.json()
```

### cURL

```bash
# Upload image
curl -X POST /images \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "'$(base64 -i dog.jpg)'",
    "content_type": "image/jpeg",
    "dog_id": "dog-123"
  }'

# Get metadata
curl -X GET /images/550e8400-e29b-41d4-a716-446655440000
```

## Best Practices

### For Clients

1. **Validate Before Upload**: Check file size and type client-side
2. **Show Progress**: Provide upload progress indicators for large files
3. **Handle Async Processing**: Poll processing status for completion
4. **Cache Resized URLs**: Store resized image URLs to avoid repeated API calls
5. **Error Handling**: Implement retry logic for transient failures

### For Large Images

1. **Compress First**: Reduce file size before upload when possible
2. **Use Appropriate Format**: JPEG for photos, PNG for graphics
3. **Monitor Memory**: Large images require more processing time
4. **Batch Uploads**: Upload images individually rather than in batches

### For Production

1. **CDN Integration**: Use CloudFront for image delivery
2. **Monitoring**: Set up alerts for processing failures
3. **Backup Strategy**: Regular backups of S3 and DynamoDB
4. **Cost Optimization**: Monitor storage costs and implement lifecycle policies

## Troubleshooting

### Common Issues

**Upload Fails with 400 Error:**
- Check image format is supported
- Verify base64 encoding is correct
- Ensure image size is within limits

**Processing Status Stuck on 'pending':**
- Check Lambda function logs
- Verify S3 event notifications are configured
- Check DynamoDB table permissions

**Resized Images Not Available:**
- Wait for processing to complete
- Check processing_status field
- Review error_message if status is 'failed'

**Performance Issues:**
- Monitor Lambda memory usage
- Check S3 transfer speeds
- Review concurrent execution limits

### Debug Information

Enable debug logging by setting `LOG_LEVEL=DEBUG` environment variable.

Debug logs include:
- Detailed processing steps
- Performance metrics
- S3 operation details
- Memory usage statistics
