# Pupper - Dog Adoption API

A serverless REST API for the Pupper dog adoption application, built with AWS CDK, Lambda, DynamoDB, and API Gateway.

## Architecture

- **API Gateway**: REST API endpoints
- **AWS Lambda**: Serverless compute for business logic
- **DynamoDB**: NoSQL database for dog, user, vote, and shelter data
- **S3**: Image storage with automatic resizing
- **CDK**: Infrastructure as Code

## Data Schema

### Dogs Table (`pupper-dogs`)
```json
{
  "dog_id": "uuid",
  "shelter_name": "string",
  "city": "string", 
  "state": "string (uppercase)",
  "dog_name_encrypted": "string (encrypted)",
  "dog_species": "string",
  "shelter_entry_date": "string (MM/DD/YYYY)",
  "dog_description": "string",
  "dog_birthday": "string (MM/DD/YYYY)",
  "dog_weight": "number",
  "dog_color": "string (lowercase)",
  "dog_age_years": "number",
  "dog_photo_url": "string",
  "dog_photo_400x400_url": "string",
  "dog_photo_50x50_url": "string",
  "shelter_id": "string",
  "created_at": "string (ISO)",
  "updated_at": "string (ISO)",
  "is_labrador": "boolean",
  "wag_count": "number",
  "growl_count": "number",
  "status": "string (available|adopted|pending)"
}
```

### Users Table (`pupper-users`)
```json
{
  "user_id": "uuid",
  "email": "string",
  "username": "string",
  "state_preference": "string",
  "max_weight_preference": "number",
  "min_weight_preference": "number", 
  "color_preference": "string",
  "max_age_preference": "number",
  "min_age_preference": "number",
  "created_at": "string (ISO)",
  "updated_at": "string (ISO)",
  "is_active": "boolean"
}
```

### Votes Table (`pupper-votes`)
```json
{
  "user_id": "string",
  "dog_id": "string",
  "vote_type": "string (wag|growl)",
  "created_at": "string (ISO)",
  "updated_at": "string (ISO)"
}
```

### Shelters Table (`pupper-shelters`)
```json
{
  "shelter_id": "uuid",
  "shelter_name": "string",
  "city": "string",
  "state": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "created_at": "string (ISO)",
  "updated_at": "string (ISO)",
  "is_active": "boolean",
  "dogs_count": "number"
}
```

## API Endpoints

### Dogs

#### POST /dogs
Create a new dog entry.

**Request Body:**
```json
{
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
  "dog_photo_url": "https://example.com/photo.jpg",
  "shelter_id": "optional-shelter-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dog successfully added to the system",
  "data": {
    "dog_id": "generated-uuid",
    "shelter_name": "Arlington Shelter",
    "city": "Arlington",
    "state": "VA",
    "dog_species": "Labrador Retriever",
    "shelter_entry_date": "1/7/2019",
    "dog_description": "Good boy",
    "dog_birthday": "4/23/2014",
    "dog_weight": 32,
    "dog_color": "brown",
    "dog_age_years": 9.2,
    "created_at": "2024-01-01T12:00:00.000Z",
    "updated_at": "2024-01-01T12:00:00.000Z",
    "is_labrador": true,
    "wag_count": 0,
    "growl_count": 0,
    "status": "available"
  }
}
```

#### GET /dogs
Retrieve all dogs with optional filtering.

**Query Parameters:**
- `state`: Filter by state (e.g., `?state=VA`)
- `min_weight`: Minimum weight filter (e.g., `?min_weight=20`)
- `max_weight`: Maximum weight filter (e.g., `?max_weight=50`)
- `color`: Filter by color (e.g., `?color=brown`)
- `min_age`: Minimum age filter (e.g., `?min_age=1`)
- `max_age`: Maximum age filter (e.g., `?max_age=5`)

**Response:**
```json
{
  "success": true,
  "message": "Dogs retrieved successfully",
  "data": {
    "dogs": [...],
    "count": 25,
    "filters_applied": {
      "state": "VA",
      "max_weight": 50
    }
  }
}
```

#### GET /dogs/{dog_id}
Retrieve a specific dog by ID.

**Response:**
```json
{
  "success": true,
  "message": "Dog retrieved successfully", 
  "data": {
    "dog_id": "uuid",
    "dog_name": "Fido",
    "shelter_name": "Arlington Shelter",
    ...
  }
}
```

#### PUT /dogs/{dog_id}
Update a specific dog's information.

**Request Body:** (any subset of dog fields)
```json
{
  "dog_description": "Updated description",
  "dog_weight": 35,
  "status": "adopted"
}
```

#### DELETE /dogs/{dog_id}
Delete a specific dog entry.

**Response:**
```json
{
  "success": true,
  "message": "Dog successfully deleted from the system",
  "data": {
    "dog_id": "uuid",
    "deleted_at": "2024-01-01T12:00:00.000Z"
  }
}
```

#### POST /images
Upload a new image for processing.

**Request Body:**
```json
{
  "image_data": "base64_encoded_image_data",
  "content_type": "image/jpeg",
  "dog_id": "optional-dog-uuid",
  "description": "Optional description",
  "tags": ["optional", "tags"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "data": {
    "image_id": "generated-uuid",
    "original_url": "https://bucket.s3.amazonaws.com/uploads/uuid/original.jpg",
    "status": "uploaded",
    "processing_status": "queued",
    "size_bytes": 1234567,
    "content_type": "image/jpeg",
    "created_at": "2024-01-01T12:00:00.000Z"
  }
}
```

#### GET /images/{image_id}
Retrieve image metadata and processing status.

**Response:**
```json
{
  "success": true,
  "message": "Image metadata retrieved successfully",
  "data": {
    "image_id": "uuid",
    "original_url": "https://bucket.s3.amazonaws.com/uploads/uuid/original.jpg",
    "resized_urls": {
      "400x400": "https://bucket.s3.amazonaws.com/processed/uuid/400x400.png",
      "50x50": "https://bucket.s3.amazonaws.com/processed/uuid/50x50.png",
      "800x600": "https://bucket.s3.amazonaws.com/processed/uuid/800x600.jpg",
      "200x150": "https://bucket.s3.amazonaws.com/processed/uuid/200x150.jpg"
    },
    "processing_status": "completed",
    "dimensions": {...},
    "created_at": "2024-01-01T12:00:00.000Z"
  }
}
```

## Image Processing Features

### Large Image Support
- **Maximum Size**: 50MB per image
- **Supported Formats**: JPEG, PNG, WebP
- **Automatic Processing**: Creates multiple resized versions
- **Asynchronous Pipeline**: Non-blocking image processing

### Automatic Resizing
The system automatically creates optimized versions:
- **400x400 PNG**: Dog profile display
- **50x50 PNG**: Thumbnail/avatar  
- **800x600 JPEG**: High-quality preview
- **200x150 JPEG**: List view thumbnail

### Processing Pipeline
1. Image uploaded to S3 with metadata stored in DynamoDB
2. S3 event triggers processing Lambda function
3. Original image downloaded and validated
4. Multiple resized versions created with aspect ratio preservation
5. Processed images uploaded to S3
6. Metadata updated with URLs and dimensions

#### POST /dogs/{dog_id}/vote
Vote on a dog (wag or growl).

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "vote_type": "wag"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully recorded wag for dog",
  "data": {
    "dog_id": "dog-uuid",
    "user_id": "user-uuid", 
    "vote_type": "wag",
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

## Security Features

1. **Dog Name Encryption**: Dog names are encrypted before storage using base64 encoding (replace with proper encryption in production)
2. **CORS Configuration**: API Gateway configured with CORS for web frontend access
3. **Input Validation**: All inputs validated against schema requirements
4. **Species Filtering**: Only Labrador Retrievers allowed (PR disaster prevention)
5. **IAM Roles**: Least privilege access for Lambda functions
6. **Image Classification**: Amazon Rekognition ensures only Labrador Retriever images are accepted

## Image Classification

The application uses **Amazon Rekognition** to automatically classify uploaded images and ensure only Labrador Retriever photos are accepted:

- **Automatic Detection**: Uses AI to identify dog breeds in uploaded images
- **High Accuracy**: Minimum 70% confidence threshold for breed detection
- **Instant Rejection**: Non-Labrador images are immediately rejected and deleted
- **Detailed Feedback**: Users receive specific information about why images were rejected
- **Cost Efficient**: Only processes images that pass initial validation

### Classification Process
1. User uploads image via POST /images
2. Image temporarily stored in S3
3. Amazon Rekognition analyzes image content
4. If Labrador detected → Image accepted for processing
5. If not Labrador → Image deleted and user notified

For detailed information, see [IMAGE_CLASSIFICATION.md](IMAGE_CLASSIFICATION.md).

## Image Processing

- Original images stored in S3
- Automatic generation of 400x400 PNG and 50x50 thumbnail PNG versions
- Images resized maintaining aspect ratio with white background padding
- URLs automatically updated in dog records

## Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

3. Deploy the stack:
```bash
cdk deploy
```

4. Get the API Gateway URL from the deployment output.

## Data Validation Rules

1. **Required Fields**: All shelter and dog information fields are required
2. **Species Validation**: Only "Labrador Retriever" allowed
3. **Date Format**: Dates must be in MM/DD/YYYY format
4. **Weight Validation**: Must be a valid number
5. **Vote Types**: Only "wag" or "growl" accepted
6. **State Format**: Automatically converted to uppercase
7. **Color Format**: Automatically converted to lowercase

## Error Handling

All endpoints return consistent error responses:
```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found
- `500`: Internal Server Error

## Future Enhancements

1. **Authentication**: Add Cognito user pools for user authentication
2. **Authorization**: Implement role-based access control
3. **Pagination**: Add pagination for large result sets
4. **Caching**: Add CloudFront and ElastiCache for performance
5. **Monitoring**: Add CloudWatch dashboards and alarms
6. **AI Features**: Integrate with Amazon Bedrock for dog matching and image generation
7. **Multi-Region**: Deploy across multiple AWS regions for global availability
