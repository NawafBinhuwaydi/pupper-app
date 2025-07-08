# Image Classification with Amazon Rekognition

This document describes the image classification feature that ensures only Labrador Retriever images are accepted in the Pupper application.

## Overview

The image classification system uses Amazon Rekognition to analyze uploaded images and determine if they contain Labrador Retrievers. Only images that pass this classification are accepted for further processing.

## Architecture

```
User Upload → API Gateway → Image Upload Lambda → Image Classification Lambda → Amazon Rekognition
                                ↓                           ↓
                         S3 Storage (if accepted)    Classification Result
                                ↓
                         Image Processing Pipeline
```

## Components

### 1. Image Classification Lambda Function
- **File**: `backend/lambda/image_processing/classify.py`
- **Purpose**: Analyzes images using Amazon Rekognition
- **Runtime**: Python 3.9
- **Memory**: 512 MB
- **Timeout**: 60 seconds

### 2. Updated Image Upload Lambda Function
- **File**: `backend/lambda/image_processing/upload.py`
- **Purpose**: Handles image uploads and invokes classification
- **Integration**: Calls classification function before storing images

### 3. Amazon Rekognition Integration
- **Service**: AWS Rekognition
- **APIs Used**:
  - `detect_labels`: Identifies objects and scenes in images
  - `detect_text`: Reads text in images for additional breed information
- **Permissions**: Added to Lambda execution role

## Classification Logic

### Primary Detection
The system looks for these labels with minimum 70% confidence:
- "Labrador Retriever"
- "Labrador" 
- "Lab"
- "Golden Retriever" (often confused with Labs)
- "Retriever"

### Secondary Detection
If primary detection doesn't find Labrador-specific labels but detects "Dog":
- Analyzes any text in the image for breed mentions
- Provides additional confidence scoring

### Decision Process
1. **Image Upload**: User uploads image via POST /images
2. **S3 Storage**: Image temporarily stored in S3
3. **Classification**: Rekognition analyzes the image
4. **Decision**:
   - ✅ **Accept**: If Labrador detected → Continue processing
   - ❌ **Reject**: If no Labrador detected → Delete image and return error

## API Response Changes

### Successful Upload (Labrador Detected)
```json
{
  "success": true,
  "data": {
    "message": "Image uploaded and verified as Labrador Retriever successfully",
    "image_id": "uuid",
    "original_url": "https://bucket.s3.amazonaws.com/...",
    "status": "uploaded",
    "processing_status": "pending",
    "size_bytes": 1234567,
    "content_type": "image/jpeg",
    "created_at": "2024-01-01T12:00:00.000Z",
    "classification": {
      "is_labrador": true,
      "confidence_score": 85.5,
      "detected_labels": ["Labrador Retriever", "Dog"]
    }
  }
}
```

### Rejected Upload (Not a Labrador)
```json
{
  "success": false,
  "error": "Only images of Labrador Retrievers are allowed. Please upload an image containing a Labrador Retriever.",
  "error_code": "NOT_LABRADOR",
  "classification_details": {
    "is_dog": true,
    "is_labrador": false,
    "confidence_score": 0,
    "detected_labels": [
      {
        "name": "German Shepherd",
        "confidence": 92.3
      },
      {
        "name": "Dog",
        "confidence": 98.7
      }
    ]
  }
}
```

## Error Handling

### Classification Errors
- **Invalid Image Format**: Returns specific error message
- **Image Too Large**: Handled by Rekognition limits
- **Service Unavailable**: Graceful fallback with retry logic
- **Network Issues**: Timeout handling with appropriate error messages

### Fallback Behavior
If classification service is unavailable:
- Images are temporarily accepted (configurable)
- Warning logged for manual review
- System continues to function

## Security Considerations

### IAM Permissions
The Lambda execution role includes minimal Rekognition permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectLabels",
        "rekognition:DetectText",
        "rekognition:DetectModerationLabels"
      ],
      "Resource": "*"
    }
  ]
}
```

### Data Privacy
- Images are analyzed but not stored by Rekognition
- Classification metadata stored in DynamoDB
- Rejected images are immediately deleted from S3

## Performance Considerations

### Optimization
- **Concurrent Executions**: Limited to 20 for classification function
- **Memory Allocation**: 512 MB for optimal performance
- **Timeout**: 60 seconds to handle large images
- **Caching**: Classification results stored in DynamoDB

### Cost Management
- Rekognition charges per image analyzed
- Failed uploads don't incur processing costs
- Batch processing for multiple images (future enhancement)

## Monitoring and Logging

### CloudWatch Metrics
- Classification success/failure rates
- Processing times
- Error rates by type
- Cost tracking

### Logging
- Detailed classification results
- Confidence scores for accepted images
- Rejection reasons for failed uploads
- Performance metrics

## Testing

### Test Script
Use `test_image_classification.py` to test the system:

```bash
python test_image_classification.py
```

### Test Cases
1. **Labrador Images**: Should be accepted
2. **Other Dog Breeds**: Should be rejected
3. **Non-Dog Images**: Should be rejected
4. **Invalid Images**: Should return format errors

### Sample Test Images Needed
- `labrador_sitting.jpg` ✅ Should accept
- `golden_retriever.jpg` ✅ Should accept (similar breed)
- `german_shepherd.jpg` ❌ Should reject
- `cat_photo.jpg` ❌ Should reject
- `landscape.jpg` ❌ Should reject
- `corrupted_file.jpg` ❌ Should return error

## Configuration

### Environment Variables
- `CLASSIFICATION_FUNCTION`: Name of classification Lambda function
- `CONFIDENCE_THRESHOLD`: Minimum confidence for detection (default: 70%)
- `CLASSIFICATION_ENABLED`: Enable/disable classification (default: true)

### Tuning Parameters
```python
# In classify.py
CONFIDENCE_THRESHOLD = 70.0  # Minimum confidence for dog detection
LABRADOR_KEYWORDS = [
    "labrador retriever",
    "labrador", 
    "lab",
    "golden retriever",
    "retriever"
]
```

## Deployment

### CDK Changes
The classification feature is automatically deployed with:
```bash
cdk deploy
```

### New Resources Created
- `ImageClassificationFunction` Lambda
- Updated IAM permissions for Rekognition
- Environment variables for function integration

## Future Enhancements

### Planned Improvements
1. **Custom Model Training**: Train custom Rekognition model for better breed detection
2. **Batch Processing**: Process multiple images in single request
3. **Advanced Filtering**: Age, size, and health detection
4. **User Feedback**: Allow users to report misclassifications
5. **A/B Testing**: Compare different confidence thresholds

### Integration Opportunities
1. **Amazon Bedrock**: Generate breed descriptions
2. **Amazon Textract**: Extract vaccination records from documents
3. **Amazon Comprehend**: Analyze user-provided descriptions
4. **Amazon Personalize**: Recommend dogs based on user preferences

## Troubleshooting

### Common Issues

#### Classification Always Fails
- Check IAM permissions for Rekognition
- Verify Lambda function deployment
- Check CloudWatch logs for errors

#### High False Positives
- Adjust `CONFIDENCE_THRESHOLD` in classify.py
- Review and update `LABRADOR_KEYWORDS` list
- Add more specific breed detection logic

#### Performance Issues
- Increase Lambda memory allocation
- Optimize image preprocessing
- Implement result caching

### Debug Commands
```bash
# Check Lambda function logs
aws logs tail /aws/lambda/ImageClassificationFunction --follow

# Test classification directly
aws lambda invoke \
  --function-name ImageClassificationFunction \
  --payload '{"bucket":"your-bucket","key":"test-image.jpg"}' \
  response.json

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/PupperLambdaRole \
  --action-names rekognition:DetectLabels \
  --resource-arns "*"
```

## Support

For issues with image classification:
1. Check CloudWatch logs for detailed error messages
2. Verify test images meet format requirements
3. Ensure API Gateway URL is correctly configured
4. Review IAM permissions for Rekognition access

## Compliance

This feature helps ensure:
- **Brand Consistency**: Only Labrador content in the application
- **User Experience**: Relevant search and matching results
- **Data Quality**: High-quality, verified dog profiles
- **Automated Moderation**: Reduces manual content review needs
