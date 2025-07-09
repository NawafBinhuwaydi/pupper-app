from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct


class PupperFrontendStack(Stack):
    """
    CDK Stack for Pupper Frontend Infrastructure
    Creates S3 bucket for static website hosting and CloudFront distribution
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for hosting static frontend assets
        self.frontend_bucket = s3.Bucket(
            self, "PupperFrontendBucket",
            bucket_name=f"pupper-frontend-{self.account}-{self.region}",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,  # Allow public read for website hosting
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Origin Access Identity for CloudFront
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "PupperOAI",
            comment="Origin Access Identity for Pupper Frontend",
        )

        # Grant CloudFront access to S3 bucket
        self.frontend_bucket.grant_read(origin_access_identity)

        # CloudFront Distribution
        self.distribution = cloudfront.Distribution(
            self, "PupperDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_identity=origin_access_identity,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                compress=True,
            ),
            # Additional behaviors for different file types
            additional_behaviors={
                # Cache static assets (CSS, JS, images) for longer
                "/static/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    compress=True,
                ),
                # Cache images for longer
                "*.jpg": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True,
                ),
                "*.png": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True,
                ),
                "*.svg": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True,
                ),
                # CSS and JS files
                "*.css": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True,
                ),
                "*.js": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_identity=origin_access_identity,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    compress=True,
                ),
            },
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(30),
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # Use only North America and Europe
            enabled=True,
            comment="Pupper Dog Adoption App Frontend Distribution",
        )

        # Deploy frontend assets to S3 (if build directory exists)
        try:
            self.deployment = s3deploy.BucketDeployment(
                self, "PupperFrontendDeployment",
                sources=[s3deploy.Source.asset("./frontend/build")],
                destination_bucket=self.frontend_bucket,
                distribution=self.distribution,
                distribution_paths=["/*"],
                prune=True,  # Remove files that are not in the source
            )
        except Exception as e:
            print(f"Note: Frontend build directory not found. You'll need to build and deploy manually. Error: {e}")

        # Outputs
        CfnOutput(
            self, "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="S3 Bucket name for frontend assets",
        )

        CfnOutput(
            self, "FrontendBucketWebsiteURL",
            value=self.frontend_bucket.bucket_website_url,
            description="S3 Bucket website URL",
        )

        CfnOutput(
            self, "CloudFrontDistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront Distribution ID",
        )

        CfnOutput(
            self, "CloudFrontDistributionDomainName",
            value=self.distribution.distribution_domain_name,
            description="CloudFront Distribution Domain Name",
        )

        CfnOutput(
            self, "CloudFrontURL",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront Distribution URL",
        )

        # Store references for cross-stack access
        self.frontend_bucket_name = self.frontend_bucket.bucket_name
        self.distribution_domain_name = self.distribution.distribution_domain_name
