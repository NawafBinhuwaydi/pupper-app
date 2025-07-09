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
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Add bucket policy for public read access
        bucket_policy = iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"{self.frontend_bucket.bucket_arn}/*"],
            principals=[iam.AnyPrincipal()],
            effect=iam.Effect.ALLOW,
        )
        self.frontend_bucket.add_to_resource_policy(bucket_policy)

        # Origin Access Control for CloudFront
        origin_access_control = cloudfront.OriginAccessControl(
            self, "PupperOAC",
            description="Origin Access Control for Pupper Frontend",
            origin_access_control_origin_type=cloudfront.OriginAccessControlOriginType.S3,
            signing_behavior=cloudfront.OriginAccessControlSigningBehavior.ALWAYS,
            signing_protocol=cloudfront.OriginAccessControlSigningProtocol.SIGV4,
        )

        # CloudFront Distribution
        self.distribution = cloudfront.Distribution(
            self, "PupperDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_control_id=origin_access_control.origin_access_control_id,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT_AND_SECURITY_HEADERS,
            ),
            # Additional behaviors for different file types
            additional_behaviors={
                # Cache static assets (CSS, JS, images) for longer
                "/static/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                ),
                # Cache images for longer
                "*.jpg": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                ),
                "*.png": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                ),
                # API calls should not be cached
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
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
