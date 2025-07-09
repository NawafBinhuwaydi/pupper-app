from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    RemovalPolicy,
    Duration,
    CfnOutput,
)
from constructs import Construct
import json


class PupperFrontendEnhancedStack(Stack):
    """
    Enhanced CDK Stack for Pupper Frontend Infrastructure
    Supports custom domains, advanced caching, and security features
    """

    def __init__(self, scope: Construct, construct_id: str, 
                 domain_name: str = None, 
                 certificate_arn: str = None,
                 hosted_zone_id: str = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load configuration
        try:
            with open('./frontend-config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {"frontend": {}, "build": {}, "deployment": {}}

        # S3 Bucket for hosting static frontend assets
        self.frontend_bucket = s3.Bucket(
            self, "PupperFrontendBucket",
            bucket_name=f"pupper-frontend-{self.account}-{self.region}",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=False,  # Use OAC instead
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(30),
                )
            ],
        )

        # Origin Access Control for CloudFront (recommended over OAI)
        origin_access_control = cloudfront.OriginAccessControl(
            self, "PupperOAC",
            description="Origin Access Control for Pupper Frontend",
            origin_access_control_origin_type=cloudfront.OriginAccessControlOriginType.S3,
            signing_behavior=cloudfront.OriginAccessControlSigningBehavior.ALWAYS,
            signing_protocol=cloudfront.OriginAccessControlSigningProtocol.SIGV4,
        )

        # Custom cache policies
        static_cache_policy = cloudfront.CachePolicy(
            self, "StaticAssetsCachePolicy",
            cache_policy_name=f"PupperStaticAssets-{self.account}",
            comment="Cache policy for static assets (CSS, JS, images)",
            default_ttl=Duration.days(365),
            max_ttl=Duration.days(365),
            min_ttl=Duration.seconds(0),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"
            ),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
        )

        html_cache_policy = cloudfront.CachePolicy(
            self, "HtmlCachePolicy",
            cache_policy_name=f"PupperHtml-{self.account}",
            comment="Cache policy for HTML files",
            default_ttl=Duration.hours(1),
            max_ttl=Duration.days(1),
            min_ttl=Duration.seconds(0),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"
            ),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
        )

        # Security headers response policy
        security_headers_policy = cloudfront.ResponseHeadersPolicy(
            self, "SecurityHeadersPolicy",
            response_headers_policy_name=f"PupperSecurityHeaders-{self.account}",
            comment="Security headers for Pupper frontend",
            cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
                access_control_allow_credentials=False,
                access_control_allow_headers=["*"],
                access_control_allow_methods=["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
                access_control_allow_origins=["*"],
                access_control_max_age=Duration.seconds(600),
                origin_override=True,
            ),
            security_headers_behavior=cloudfront.ResponseHeadersSecurityHeadersBehavior(
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(override=True),
                frame_options=cloudfront.ResponseHeadersFrameOptions(
                    frame_option=cloudfront.HeadersFrameOption.DENY,
                    override=True,
                ),
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
                    override=True,
                ),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(31536000),
                    include_subdomains=True,
                    preload=True,
                    override=True,
                ),
            ),
        )

        # Certificate and domain setup
        certificate = None
        domain_names = None
        
        if domain_name and certificate_arn:
            certificate = acm.Certificate.from_certificate_arn(
                self, "Certificate", certificate_arn
            )
            domain_names = [domain_name]

        # CloudFront Distribution
        distribution_props = {
            "default_behavior": cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_control_id=origin_access_control.origin_access_control_id,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=html_cache_policy,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                response_headers_policy=security_headers_policy,
                compress=True,
            ),
            "additional_behaviors": {
                # Static assets with long-term caching
                "/static/*": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    response_headers_policy=security_headers_policy,
                    compress=True,
                ),
                # Images with long-term caching
                "*.jpg": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True,
                ),
                "*.png": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True,
                ),
                "*.svg": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True,
                ),
                # CSS and JS files
                "*.css": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True,
                ),
                "*.js": cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        self.frontend_bucket,
                        origin_access_control_id=origin_access_control.origin_access_control_id,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_cache_policy,
                    compress=True,
                ),
            },
            "default_root_object": "index.html",
            "error_responses": [
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
            "price_class": cloudfront.PriceClass.PRICE_CLASS_100,
            "enabled": True,
            "comment": "Pupper Dog Adoption App Frontend Distribution - Enhanced",
            "http_version": cloudfront.HttpVersion.HTTP2_AND_3,
            "enable_ipv6": True,
        }

        # Add certificate and domain if provided
        if certificate and domain_names:
            distribution_props["certificate"] = certificate
            distribution_props["domain_names"] = domain_names

        self.distribution = cloudfront.Distribution(self, "PupperDistribution", **distribution_props)

        # Grant CloudFront access to S3 bucket
        self.frontend_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{self.frontend_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
                    }
                },
            )
        )

        # Route53 record for custom domain
        if domain_name and hosted_zone_id:
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self, "HostedZone",
                zone_name=domain_name.split('.', 1)[1],  # Remove subdomain
                hosted_zone_id=hosted_zone_id,
            )
            
            route53.ARecord(
                self, "AliasRecord",
                zone=hosted_zone,
                record_name=domain_name,
                target=route53.RecordTarget.from_alias(
                    targets.CloudFrontTarget(self.distribution)
                ),
            )

        # Deploy frontend assets to S3 (if build directory exists)
        try:
            self.deployment = s3deploy.BucketDeployment(
                self, "PupperFrontendDeployment",
                sources=[s3deploy.Source.asset("./frontend/build")],
                destination_bucket=self.frontend_bucket,
                distribution=self.distribution,
                distribution_paths=["/*"],
                prune=True,
                retain_on_delete=False,
                memory_limit=1024,
                ephemeral_storage_size=Size.mebibytes(2048),
            )
        except Exception as e:
            print(f"Note: Frontend build directory not found. Build frontend first. Error: {e}")

        # Outputs
        CfnOutput(
            self, "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="S3 Bucket name for frontend assets",
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

        if domain_name:
            CfnOutput(
                self, "CustomDomainURL",
                value=f"https://{domain_name}",
                description="Custom Domain URL",
            )

        # Store references
        self.frontend_bucket_name = self.frontend_bucket.bucket_name
        self.distribution_domain_name = self.distribution.distribution_domain_name
