# Pupper Frontend Infrastructure

This document describes the frontend hosting infrastructure for the Pupper Dog Adoption application, including S3 static website hosting and CloudFront global distribution.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Users/Browsers│    │   CloudFront     │    │   S3 Bucket     │
│                 │───▶│   Distribution   │───▶│   Static Files  │
│   Global Access │    │   (Global CDN)   │    │   (Origin)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Route 53       │
                       │   (Custom Domain)│
                       └──────────────────┘
```

## Components

### 1. S3 Bucket (Static Website Hosting)
- **Purpose**: Hosts static frontend assets (HTML, CSS, JavaScript, images)
- **Configuration**: 
  - Website hosting enabled
  - Versioning enabled for rollback capability
  - Lifecycle rules for old version cleanup
  - Origin Access Control (OAC) for security

### 2. CloudFront Distribution
- **Purpose**: Global content delivery network for fast, secure access
- **Features**:
  - HTTPS enforcement
  - Global edge locations
  - Intelligent caching policies
  - Compression (Gzip/Brotli)
  - Security headers
  - Custom error pages for SPA routing

### 3. Custom Caching Policies
- **Static Assets** (CSS, JS, Images): 1 year cache
- **HTML Files**: 1 hour cache
- **API Calls**: No caching
- **Error Pages**: 5 minutes cache

## Deployment Options

### Option 1: Basic Deployment
Use the basic frontend stack for simple deployments:

```bash
# Deploy basic frontend infrastructure
./deploy-frontend.sh
```

### Option 2: Enhanced Deployment with Custom Domain
Use the enhanced stack for production with custom domains:

```python
# In app_with_frontend.py, use enhanced stack
from infra.pupper_frontend_enhanced_stack import PupperFrontendEnhancedStack

frontend_stack = PupperFrontendEnhancedStack(
    app,
    "PupperFrontendStack",
    domain_name="pupper.yourdomain.com",
    certificate_arn="arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012",
    hosted_zone_id="Z1D633PJN98FT9"
)
```

## Configuration

### Frontend Configuration (`frontend-config.json`)
```json
{
  "frontend": {
    "bucketName": "pupper-frontend-{account}-{region}",
    "distributionConfig": {
      "priceClass": "PriceClass_100",
      "cachingEnabled": true,
      "compressionEnabled": true,
      "httpVersion": "http2",
      "ipv6Enabled": true
    },
    "security": {
      "httpsOnly": true,
      "securityHeaders": true,
      "corsEnabled": true
    }
  }
}
```

## Security Features

### 1. Origin Access Control (OAC)
- Replaces legacy Origin Access Identity (OAI)
- More secure and supports additional AWS services
- Prevents direct S3 access, forces traffic through CloudFront

### 2. Security Headers
- **Content-Type-Options**: Prevents MIME type sniffing
- **Frame-Options**: Prevents clickjacking
- **Referrer-Policy**: Controls referrer information
- **Strict-Transport-Security**: Enforces HTTPS

### 3. HTTPS Enforcement
- All HTTP requests automatically redirected to HTTPS
- TLS 1.2+ required
- Perfect Forward Secrecy enabled

## Performance Optimizations

### 1. Caching Strategy
```
Static Assets (CSS/JS/Images): 365 days
HTML Files: 1 hour
Error Pages: 5 minutes
```

### 2. Compression
- Gzip compression enabled
- Brotli compression enabled (better than Gzip)
- Automatic compression for text-based files

### 3. HTTP/2 and HTTP/3
- HTTP/2 enabled for multiplexing
- HTTP/3 support for improved performance
- IPv6 support enabled

## Management Commands

### Deploy Frontend
```bash
# Basic deployment
./deploy-frontend.sh

# Enhanced deployment with custom domain
cdk deploy PupperFrontendStack --app "python app_with_frontend.py"
```

### Invalidate CloudFront Cache
```bash
# Invalidate all files
python scripts/frontend-utils.py invalidate

# Invalidate specific paths
python scripts/frontend-utils.py invalidate --paths "/index.html" "/static/*"

# Invalidate and wait for completion
python scripts/frontend-utils.py invalidate --wait
```

### Check Distribution Status
```bash
python scripts/frontend-utils.py status
```

### List S3 Objects
```bash
python scripts/frontend-utils.py list
```

### Sync Local Files to S3
```bash
python scripts/frontend-utils.py sync ./frontend/build
```

## Custom Domain Setup

### Prerequisites
1. **Domain Name**: Own a domain name
2. **Route 53 Hosted Zone**: Domain managed in Route 53
3. **SSL Certificate**: ACM certificate in us-east-1 region

### Steps
1. **Request SSL Certificate**:
   ```bash
   aws acm request-certificate \
     --domain-name pupper.yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Validate Certificate**: Add DNS records as instructed by ACM

3. **Deploy with Custom Domain**:
   ```python
   frontend_stack = PupperFrontendEnhancedStack(
       app,
       "PupperFrontendStack",
       domain_name="pupper.yourdomain.com",
       certificate_arn="your-certificate-arn",
       hosted_zone_id="your-hosted-zone-id"
   )
   ```

## Monitoring and Logging

### CloudWatch Metrics
- **Requests**: Number of requests to CloudFront
- **Bytes Downloaded**: Data transfer metrics
- **Error Rate**: 4xx and 5xx error rates
- **Cache Hit Rate**: Percentage of requests served from cache

### Access Logs
Enable CloudFront access logs for detailed request analysis:
```python
# In your CDK stack
distribution = cloudfront.Distribution(
    self, "Distribution",
    # ... other config
    enable_logging=True,
    log_bucket=log_bucket,
    log_file_prefix="cloudfront-logs/",
)
```

## Cost Optimization

### 1. Price Class Selection
- **PriceClass_100**: North America and Europe only (lowest cost)
- **PriceClass_200**: North America, Europe, Asia, Middle East, Africa
- **PriceClass_All**: All edge locations (highest performance, highest cost)

### 2. Caching Strategy
- Long cache times for static assets reduce origin requests
- Proper cache headers minimize unnecessary invalidations

### 3. Compression
- Reduces bandwidth costs
- Improves performance

## Troubleshooting

### Common Issues

#### 1. 403 Forbidden Errors
- **Cause**: Incorrect OAC configuration or S3 bucket policy
- **Solution**: Verify OAC is properly configured and S3 bucket allows CloudFront access

#### 2. Stale Content
- **Cause**: Cached content not updated after deployment
- **Solution**: Create CloudFront invalidation after deployment

#### 3. SPA Routing Issues
- **Cause**: Direct access to routes returns 404
- **Solution**: Configure error responses to return index.html for 404/403 errors

#### 4. Slow Initial Load
- **Cause**: Cold start or cache miss
- **Solution**: Implement proper cache warming or preloading strategies

### Debug Commands
```bash
# Check distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# List invalidations
aws cloudfront list-invalidations --distribution-id YOUR_DISTRIBUTION_ID

# Check S3 bucket policy
aws s3api get-bucket-policy --bucket YOUR_BUCKET_NAME
```

## Best Practices

### 1. Deployment
- Always build frontend before deployment
- Use versioned deployments for rollback capability
- Test in staging environment first

### 2. Caching
- Set appropriate cache headers for different file types
- Use cache busting for updated assets
- Monitor cache hit rates

### 3. Security
- Keep security headers updated
- Regularly review access policies
- Use HTTPS everywhere

### 4. Performance
- Optimize images and assets before upload
- Use modern image formats (WebP, AVIF)
- Implement lazy loading for images

## Integration with Backend

The frontend infrastructure integrates with your existing Pupper backend:

1. **API Calls**: Frontend makes requests to API Gateway endpoints
2. **Image Display**: Shows dog images from the S3 images bucket
3. **CORS**: CloudFront handles CORS for API requests
4. **Authentication**: Integrates with Cognito (if implemented)

## Future Enhancements

1. **Lambda@Edge**: Add serverless functions at edge locations
2. **Real-time Updates**: WebSocket support for live updates
3. **Progressive Web App**: Service worker for offline functionality
4. **Advanced Analytics**: Detailed user behavior tracking
5. **A/B Testing**: CloudFront functions for feature flags

## Support

For issues or questions:
1. Check CloudWatch logs and metrics
2. Review CloudFront distribution configuration
3. Verify S3 bucket permissions and content
4. Use the provided utility scripts for common tasks
